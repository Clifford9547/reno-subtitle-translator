import sys, os, locale
from typing import Optional
import pyaudio
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QMessageBox

from .ui import MainWindow, OverlayWindow
from .workers import AudioCaptureWorker, ASRWorker
from .utils import MODELS_DIR, argos_pair_installed, argos_find_package, argos_install_from_file, TranslateRoute, abs_path
from .utils import ensure_vosk_model_ready, ARGOS_OK
from .i18n import set_lang, t

def _detect_lang_from_system() -> str:
    try:
        lc = locale.getdefaultlocale()
        code = (lc[0] or "").lower() if lc else ""
    except Exception:
        code = ""
    return "zh" if "zh" in code else "en"

class App:
    def __init__(self):
        set_lang(_detect_lang_from_system())
        self.qt = QApplication(sys.argv)
        self.qt.setApplicationName(t("app.title"))
        os.makedirs(MODELS_DIR, exist_ok=True)
        self.overlay = OverlayWindow()
        self.win = MainWindow()
        self.win.show()
        self.pa = pyaudio.PyAudio()
        self.device_map = {}
        self._scan_devices()
        self.cap: Optional[AudioCaptureWorker] = None
        self.asr: Optional[ASRWorker] = None
        self.win.startStopRequested.connect(self._toggle)
        self.win.subtitleStyleChanged.connect(self.overlay.apply_subtitle_font)
        self.win.emit_current_subtitle_style()

    def _toggle(self):
        if self.cap or self.asr:
            self.stop()
        else:
            self.start()

    def _scan_devices(self):
        items = [t("input.auto")]
        device_map = {}
        try:
            n = self.pa.get_device_count()
            for i in range(n):
                try:
                    info = self.pa.get_device_info_by_index(i)
                    if info.get("maxInputChannels", 0) > 0:
                        name = f"{info.get('name','?')} (#{i})"
                        items.append(name); device_map[name] = i
                except Exception:
                    continue
        except Exception:
            pass
        self.device_map = device_map
        self.win.devCombo.clear()
        self.win.devCombo.addItems(items)

    def _auto_pick_device(self) -> Optional[int]:
        try:
            n = self.pa.get_device_count()
            for i in range(n):
                info = self.pa.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) <= 0:
                    continue
                name = str(info.get("name", "")).lower()
                if any(k in name for k in ["stereo mix", "立体声", "what u hear", "wave out", "loopback", "monitor", "speakers", "扬声器", "realtek"]):
                    if self._test_device(i):
                        return i
        except Exception:
            pass
        try:
            n = self.pa.get_device_count()
            for i in range(n):
                info = self.pa.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0 and self._test_device(i):
                    return i
        except Exception:
            pass
        return None

    def _test_device(self, idx) -> bool:
        try:
            s = self.pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True,
                             input_device_index=idx, frames_per_buffer=1024)
            s.close(); return True
        except Exception:
            return False

    @Slot()
    def start(self):
        if self.cap or self.asr:
            return
        asr_lang = self.win.asrCombo.currentText()
        tgt_lang = self.win.tgtCombo.currentText()
        model_data = self.win.asrModelCombo.currentData() or {}
        model_folder = model_data.get("folder")
        if not model_folder:
            QMessageBox.warning(self.win, t("dlg.title.tip"), t("msg.select_model_first")); return
        ok, msg = ensure_vosk_model_ready(model_folder)
        if not ok:
            QMessageBox.critical(self.win, t("dlg.title.fail"), t("msg.asr_model_unavailable", msg=msg)); return
        if ARGOS_OK:
            trans_data = self.win.transModelCombo.currentData() or {}
            if not trans_data.get("installed"):
                src, tgt = trans_data.get("pair", (asr_lang, tgt_lang))
                pkg = argos_find_package(src, tgt)
                if pkg:
                    r = QMessageBox.question(self.win, t("dlg.title.download_trans"),
                                             t("dlg.ask.download_trans", src=src, tgt=tgt),
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    if r == QMessageBox.Yes:
                        url = getattr(pkg, "download_url", None)
                        if url:
                            tmp_dir = abs_path("_argos_tmp"); os.makedirs(tmp_dir, exist_ok=True)
                            tmp_file = os.path.join(tmp_dir, f"{src}_{tgt}.argosmodel")
                            def on_ok():
                                ok2, msg2 = argos_install_from_file(tmp_file)
                                try:
                                    if os.path.exists(tmp_file): os.remove(tmp_file)
                                except Exception:
                                    pass
                                if ok2:
                                    QMessageBox.information(self.win, t("dlg.title.done"), t("dlg.argos_install_ok"))
                                    self.win._reload_trans_models()
                                else:
                                    QMessageBox.critical(self.win, t("dlg.title.fail"), t("dlg.argos_install_fail", err=msg2))
                            self.win._download_with_dialog(url, tmp_file, t("dlg.title.download_trans"), on_ok=on_ok)
            pairs_text = t("engine.pairs_installed") if argos_pair_installed(asr_lang, tgt_lang) else t("engine.pairs_missing")
            self.win.lbArgos.setText(t("label.engine") + pairs_text)
        else:
            self.win.lbArgos.setText(t("label.engine") + t("engine.no_argos"))
        name = self.win.devCombo.currentText()
        if name == t("input.auto"):
            device_index = self._auto_pick_device()
        else:
            device_index = self.device_map.get(name)
        if device_index is None:
            QMessageBox.critical(self.win, t("dlg.title.fail"), t("msg.no_input_device"))
            return
        try:
            self.asr = ASRWorker(asr_lang=asr_lang, tgt_lang=tgt_lang,
                                 route=TranslateRoute.AUTO, model_folder=model_folder, rate=16000, parent=self.win)
            self.asr.textReady.connect(self.overlay.show_texts)
            self.asr.status.connect(lambda s: self.win.lbStatus.setText(t("label.status") + s))
            self.asr.error.connect(self._on_asr_error)
            self.asr.start()
        except Exception as e:
            self.asr = None
            QMessageBox.critical(self.win, t("dlg.title.fail"), t("msg.asr_thread_fail", err=e))
            return
        try:
            self.cap = AudioCaptureWorker(device_index=device_index, rate=16000, chunk=1024, parent=self.win)
            self.cap.levelChanged.connect(self.win.pbLevel.setValue)
            self.cap.chunkReady.connect(self.asr.feed)
            self.cap.error.connect(self._on_cap_error)
            self.cap.start()
        except Exception as e:
            if self.asr:
                self.asr.stop(); self.asr.wait(3000)
                try: self.asr.terminate()
                except Exception: pass
                self.asr = None
            self.cap = None
            QMessageBox.critical(self.win, t("dlg.title.fail"), t("msg.cap_thread_fail", err=e))
            return
        self.overlay.show_texts(t("toast.listening_en"), t("toast.listening_zh"))
        self.win.setRunning(True)
        self.win.lbStatus.setText(t("label.status") + t("status.listening"))

    @Slot()
    def stop(self):
        if self.cap:
            self.cap.stop()
            if not self.cap.wait(3000):
                try: self.cap.terminate()
                except Exception: pass
            self.cap = None
        if self.asr:
            self.asr.stop()
            if not self.asr.wait(3000):
                try: self.asr.terminate()
                except Exception: pass
            self.asr = None
        self.win.setRunning(False)
        self.win.pbLevel.setValue(0)
        self.win.lbStatus.setText(t("label.status") + t("status.stopped"))

    @Slot(str)
    def _on_cap_error(self, msg: str):
        self.win.lbStatus.setText(t("msg.cap_error", msg=msg))
        self.stop()

    @Slot(str)
    def _on_asr_error(self, msg: str):
        self.win.lbStatus.setText(t("msg.asr_error", msg=msg))
        self.stop()

def main():
    need = ["pyaudio", "numpy", "vosk"]
    miss = []
    for p in need:
        try:
            __import__(p)
        except Exception:
            miss.append(p)
    if miss:
        print("Missing deps:", ", ".join(miss))
        print("Install: pip install " + " ".join(miss))
        sys.exit(1)
    app = App()
    ret = 0
    try:
        ret = app.qt.exec()
    finally:
        try:
            app.stop()
        except Exception:
            pass
        try:
            app.pa.terminate()
        except Exception:
            pass
    sys.exit(ret)
