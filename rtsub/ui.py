import os
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QShortcut, QKeySequence, QIcon, QGuiApplication, QCursor

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QMainWindow, QPushButton,
    QComboBox, QHBoxLayout, QProgressBar, QGroupBox, QGridLayout, QStatusBar,
    QMessageBox, QSpacerItem, QSizePolicy, QProgressDialog, QFileDialog, QSpinBox
)

from .utils import (
    MODELS_DIR, abs_path, list_local_vosk_models, unzip_to_models,
    argos_pair_installed, argos_find_package, argos_install_from_file,
    argos_uninstall_pair, ARGOS_OK
)
from .workers import DownloadWorker, ArgosPkgDownloadWorker
from .i18n import t, set_lang, get_lang

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowOpacity(0.86)
        self.original = QLabel("", self)
        self.translated = QLabel("", self)
        for lab in (self.original, self.translated):
            lab.setAlignment(Qt.AlignCenter)
            lab.setWordWrap(True)
        self.original.setStyleSheet("color: white; font-weight: 700;")
        self.translated.setStyleSheet("color: #F8E71C;")
        self.original.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
        self.translated.setFont(QFont("Microsoft YaHei UI", 15))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 6, 24, 6)
        lay.addWidget(self.original)
        lay.addWidget(self.translated)
        self.hideTimer = QTimer(self)
        self.hideTimer.setSingleShot(True)
        self.hideTimer.timeout.connect(self._hide)
        self.resize_to_bottom()
    def resize_to_bottom(self):
        pos = QCursor.pos()
        screen = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        h = 120
        self.setGeometry(geo.x(), geo.y() + geo.height() - h - 24, geo.width(), h)
    def mouseDoubleClickEvent(self, _event):
        self.hide()
    @Slot(str, str)
    def show_texts(self, src_txt: str, tgt_txt: str):
        self.original.setText(src_txt or "")
        self.translated.setText(tgt_txt or "")
        self.setWindowOpacity(0.86)
        self.show()
        self.hideTimer.stop()
        self.hideTimer.start(2000)
    def _hide(self):
        self.hide()
    @Slot(str, int)
    def apply_subtitle_font(self, style_key: str, size: int):
        bold = style_key in ("bold", "bold_italic")
        italic = style_key in ("italic", "bold_italic")
        for lab in (self.original, self.translated):
            f = lab.font()
            f.setPointSize(int(size))
            f.setBold(bold)
            f.setItalic(italic)
            lab.setFont(f)

class MainWindow(QMainWindow):
    startStopRequested = Signal()
    subtitleStyleChanged = Signal(str, int)
    def __init__(self):
        super().__init__()
        self._live_threads = set()
        self._live_dialogs = set()
        self._build_ui()
        self._build_shortcuts()
        
        self.retranslate_ui()
        self.uiLangCombo.currentIndexChanged.connect(self._ui_lang_changed)

    def _ensure_lang_items(self):
        cur = get_lang()
        items = [(t("menu.lang.zh"), "zh"), (t("menu.lang.en"), "en")]
        self.uiLangCombo.blockSignals(True)
        self.uiLangCombo.clear()
        for name, code in items:
            self.uiLangCombo.addItem(name, code)
        idx = 0
        for i in range(self.uiLangCombo.count()):
            if self.uiLangCombo.itemData(i) == cur:
                idx = i
                break
        self.uiLangCombo.setCurrentIndex(idx)
        self.uiLangCombo.blockSignals(False)

    def _ui_lang_changed(self):
        code = self.uiLangCombo.currentData() or "en"
        set_lang(code)
        self.retranslate_ui()


    def _build_ui(self):
        self.setWindowTitle(t("app.title"))
        self.setWindowIcon(QIcon("assets/app.ico"))
        self.menuBar().setVisible(False)
        self.resize(300, 340)
        self.setStyleSheet(
            """
            QMainWindow { background: #1f1f1f; }
            QLabel, QGroupBox { color: #ffffff; }
            QPushButton { background:#4CAF50; color:white; padding:1px 10px; border:none; border-radius:6px; font-weight: bold; min-height:25px; }
            QPushButton:disabled { background:#666; }
            QPushButton#stop { background:#E53935; }
            QPushButton#danger { background:#E53935; }
            QPushButton#danger:disabled { background:#8E8E8E; }
            QComboBox { background:#2a2a2a; color:white; padding:6px; border-radius:4px; }
            QProgressBar { background:#2a2a2a; color:white; border:1px solid #333; border-radius:4px; }
            QProgressBar::chunk { background:#2196F3; }
            QGroupBox { border:1px solid #333; margin-top: 10px; border-radius:8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            """
        )


        center = QWidget(); self.setCentralWidget(center)
        grid = QGridLayout(center); grid.setContentsMargins(12,8,12,12); grid.setHorizontalSpacing(8); grid.setVerticalSpacing(6)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 1)

        self.grpLang = QGroupBox()
        grid.addWidget(self.grpLang, 0, 0, 1, 2)
        gl = QGridLayout(self.grpLang); gl.setHorizontalSpacing(8); gl.setVerticalSpacing(8)
        self.asrCombo = QComboBox(); self.asrCombo.addItems(["ja","en","zh"]); self.asrCombo.setCurrentText("ja")
        self.tgtCombo = QComboBox(); self.tgtCombo.addItems(["zh","en","ja"]); self.tgtCombo.setCurrentText("zh")
        self.lbAsr = QLabel()
        leftRow = QWidget()
        leftLay = QHBoxLayout(leftRow)
        leftLay.setContentsMargins(0,0,0,0)
        leftLay.setSpacing(6)
        leftLay.addWidget(self.lbAsr)
        leftLay.addWidget(self.asrCombo, 1)

        self.lbTgt = QLabel()
        rightRow = QWidget()
        rightLay = QHBoxLayout(rightRow)
        rightLay.setContentsMargins(0,0,0,0)
        rightLay.setSpacing(6)
        rightLay.addWidget(self.lbTgt)
        rightLay.addWidget(self.tgtCombo, 1)

        row1 = QWidget()
        row1Lay = QHBoxLayout(row1)
        row1Lay.setContentsMargins(0,0,0,0)
        row1Lay.setSpacing(8)
        row1Lay.addWidget(leftRow)
        row1Lay.addWidget(rightRow)
        row1Lay.setStretch(0, 1)
        row1Lay.setStretch(1, 1)

        gl.addWidget(row1, 0, 0, 1, 4)



        self.asrModelCombo = QComboBox()
        self.asrModelCombo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.asrModelCombo.setMaximumWidth(260)
        self.asrModelCombo.setMinimumContentsLength(14)
        self.btnAsrDelete = QPushButton()
        
        self.btnAsrDelete.setObjectName("danger")
        self.btnAsrImport = QPushButton()
        asr_row = QHBoxLayout()
        asr_row.addWidget(self.btnAsrDelete)
        asr_row.addSpacing(6)
        asr_row.addWidget(self.btnAsrImport)
        asr_row.addStretch(1)
        gl.addWidget(QLabel(), 1, 0); gl.addWidget(self.asrModelCombo, 1, 1)
        gl.addLayout(asr_row, 1, 2, 1, 2)

        self.transModelCombo = QComboBox()
        self.transModelCombo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.transModelCombo.setMinimumContentsLength(14)
        self.transModelCombo.setMaximumWidth(260)
        self.btnTransDelete = QPushButton()
        self.btnTransDelete.setObjectName("danger")
        self.btnTransImport = QPushButton()
        trans_row = QHBoxLayout()
        trans_row.addWidget(self.btnTransDelete)
        trans_row.addSpacing(6)
        trans_row.addWidget(self.btnTransImport)
        trans_row.addStretch(1)
        gl.addWidget(QLabel(), 2, 0); gl.addWidget(self.transModelCombo, 2, 1)
        gl.addLayout(trans_row, 2, 2, 1, 2)

        gl.setColumnStretch(0, 1)
        gl.setColumnStretch(1, 0)
        gl.setColumnStretch(2, 1)
        gl.setColumnStretch(3, 0)


        self.grpAudio = QGroupBox()
        grid.addWidget(self.grpAudio, 1, 0, 1, 2)
        hd = QHBoxLayout(self.grpAudio)
        self.lbInput = QLabel(); self.devCombo = QComboBox(); self.devCombo.addItem("")
        hd.addWidget(self.lbInput); hd.addWidget(self.devCombo, 1)

        self.grpStatus = QGroupBox()
        grid.addWidget(self.grpStatus, 2, 0, 1, 2)
        vs = QVBoxLayout(self.grpStatus)
        self.lbStatus = QLabel()
        self.lbArgos  = QLabel()
        hb = QHBoxLayout(); self.pbLevel = QProgressBar(); self.pbLevel.setRange(0,100); self.pbLevel.setFixedHeight(14)
        self.lbLevel = QLabel()
        hb.addWidget(self.lbLevel); hb.addWidget(self.pbLevel, 1)
        vs.addWidget(self.lbStatus); vs.addWidget(self.lbArgos); vs.addLayout(hb)

        self.grpSubtitle = QGroupBox()
        grid.addWidget(self.grpSubtitle, 3, 0, 1, 1)
        sub = QHBoxLayout(self.grpSubtitle)
        self.lbStyle = QLabel()
        self.styleCombo = QComboBox()
        self.lbSize = QLabel()
        self.sizeSpin = QSpinBox()
        self.sizeSpin.setRange(8, 72)
        self.sizeSpin.setValue(16)
        sub.addWidget(self.lbStyle)
        sub.addWidget(self.styleCombo)
        sub.addSpacing(8)
        sub.addWidget(self.lbSize)
        sub.addWidget(self.sizeSpin)
        sub.addStretch(1)

        self.grpUiLang = QGroupBox()
        grid.addWidget(self.grpUiLang, 3, 1, 1, 1)
        uil = QHBoxLayout(self.grpUiLang)
        self.lbUiLang = QLabel()
        self.uiLangCombo = QComboBox()
        uil.addWidget(self.lbUiLang)
        uil.addWidget(self.uiLangCombo, 1)


        spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
        grid.addItem(spacer, 4, 0, 1, 2)




        btnContainer = QWidget()
        btnLine = QHBoxLayout(btnContainer)
        btnLine.setContentsMargins(0,0,0,0)
        btnLine.setSpacing(0)
        self.btnStartStop = QPushButton()
        self.btnStartStop.clicked.connect(self.startStopRequested.emit)
        btnLine.addStretch(1); btnLine.addWidget(self.btnStartStop); btnLine.addStretch(1)
        btnContainer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        grid.addWidget(btnContainer, 5, 0, 1, 2)


        self.asrCombo.currentTextChanged.connect(self._reload_asr_models)
        self.tgtCombo.currentTextChanged.connect(self._reload_trans_models)
        self.asrModelCombo.activated.connect(self._maybe_download_selected_asr_model)
        self.transModelCombo.activated.connect(self._maybe_download_selected_trans_model)
        self.btnAsrDelete.clicked.connect(self._delete_selected_vosk_model)
        self.btnAsrImport.clicked.connect(self._import_local_vosk_zip)
        self.btnTransDelete.clicked.connect(self._delete_selected_trans_model)
        self.btnTransImport.clicked.connect(self._import_local_argos_file)

        self.styleCombo.currentIndexChanged.connect(self._emit_subtitle_style)
        self.sizeSpin.valueChanged.connect(self._emit_subtitle_style)

        self._reload_asr_models()
        self._reload_trans_models()


    def _build_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, activated=self.startStopRequested.emit)

    def _track_thread(self, th: QThread):
        self._live_threads.add(th)
        th.finished.connect(lambda *args, _th=th: self._live_threads.discard(_th))
        th.finished.connect(th.deleteLater)

    def closeEvent(self, e):
        for dlg in list(self._live_dialogs):
            try:
                dlg.cancel()
            except Exception:
                pass
        for th in list(self._live_threads):
            try:
                if hasattr(th, "requestInterruption"):
                    th.requestInterruption()
                th.wait(3000)
            except Exception:
                pass
        self._live_threads.clear()
        self._live_dialogs.clear()
        super().closeEvent(e)

    def _ensure_style_items(self):
        key = self.styleCombo.currentData() if self.styleCombo.count() else "bold"
        items = [
            (t("style.regular"), "regular"),
            (t("style.bold"), "bold"),
            (t("style.italic"), "italic"),
            (t("style.bold_italic"), "bold_italic"),
        ]
        self.styleCombo.blockSignals(True)
        self.styleCombo.clear()
        for name, k in items:
            self.styleCombo.addItem(name, k)
        idx = 0
        for i in range(self.styleCombo.count()):
            if self.styleCombo.itemData(i) == key:
                idx = i
                break
        self.styleCombo.setCurrentIndex(idx)
        self.styleCombo.blockSignals(False)

    def retranslate_ui(self):
        self.setWindowTitle(t("app.title"))

        self.grpLang.setTitle(t("group.lang_model"))
        self.grpAudio.setTitle(t("group.audio"))
        self.grpStatus.setTitle(t("group.status"))
        self.grpSubtitle.setTitle(t("group.subtitle"))
        self.grpUiLang.setTitle(t("group.ui_lang"))
        self.lbUiLang.setText(t("label.ui_lang"))
        self._ensure_lang_items()


        lang_layout = self.grpLang.layout()
        self.lbAsr.setText(t("label.asr_lang"))
        self.lbTgt.setText(t("label.tgt_lang"))

        lang_layout.itemAtPosition(1,0).widget().setText(t("label.asr_model"))
        lang_layout.itemAtPosition(2,0).widget().setText(t("label.trans_model"))

        self.btnAsrDelete.setText(t("btn.delete"))
        self.btnAsrImport.setText(t("btn.import"))
        self.btnTransDelete.setText(t("btn.delete"))
        self.btnTransImport.setText(t("btn.import"))

        self.lbInput.setText(t("label.input"))
        if self.devCombo.count() == 0:
            self.devCombo.addItem(t("input.auto"))
        else:
            self.devCombo.setItemText(0, t("input.auto"))

        self.lbStatus.setText(t("label.status") + t("status.idle"))
        self.lbArgos.setText(t("label.engine") + t("engine.ready"))
        self.lbLevel.setText(t("label.level"))

        self.lbStyle.setText(t("label.font_style"))
        self.lbSize.setText(t("label.font_size"))
        self._ensure_style_items()

        self.setRunning(getattr(self, "running", False))


        

    def setRunning(self, running: bool):
        self.running = running
        if running:
            self.btnStartStop.setText(t("btn.stop"))
            self.btnStartStop.setObjectName("stop")
            self.btnStartStop.setStyle(self.style())
        else:
            self.btnStartStop.setText(t("btn.start"))
            self.btnStartStop.setObjectName("")
            self.btnStartStop.setStyle(self.style())

    @Slot()
    def _reload_asr_models(self):
        lang = self.asrCombo.currentText()
        items = list_local_vosk_models(lang)
        self.asrModelCombo.clear()
        for it in items:
            tag = (t("combo.installed") if it.get("installed") else t("combo.not_installed"))
            rec = t("combo.recommended") if it.get("recommended") else ""
            self.asrModelCombo.addItem(f"{rec}{tag}{it['label']}", it)
        if self.asrModelCombo.count() == 0:
            self.asrModelCombo.addItem(t("combo.no_models"), {"installed": False, "folder": None})

    @Slot()
    def _maybe_download_selected_asr_model(self):
        data = self.asrModelCombo.currentData()
        if not data or data.get("installed"):
            return
        url = data.get("url"); folder = data.get("folder")
        if not url or not folder:
            QMessageBox.information(self, t("dlg.title.tip"), t("dlg.no_link_use_import"))
            return
        r = QMessageBox.question(self, t("dlg.title.download_asr"),
                                 t("dlg.ask.download_asr", label=data["label"], folder=folder),
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if r != QMessageBox.Yes:
            return
        os.makedirs(MODELS_DIR, exist_ok=True)
        tmpzip = os.path.join(MODELS_DIR, f"_{folder}.zip")
        self._download_with_dialog(url, tmpzip, t("dlg.title.download_asr"),
                                   on_ok=lambda: unzip_to_models(self, tmpzip),
                                   on_done=self._reload_asr_models)

    @Slot()
    def _delete_selected_vosk_model(self):
        data = self.asrModelCombo.currentData()
        if not data or not data.get("installed"):
            QMessageBox.information(self, t("dlg.title.tip"), t("dlg.not_installed"))
            return
        folder = data.get("folder"); p = os.path.join(MODELS_DIR, folder)
        r = QMessageBox.question(self, t("dlg.delete_confirm"),
                                 t("dlg.ask.delete_model", path=p),
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        import shutil
        try:
            shutil.rmtree(p, ignore_errors=True)
            QMessageBox.information(self, t("dlg.title.done"), t("dlg.done.deleted"))
        except Exception as e:
            QMessageBox.critical(self, t("dlg.title.fail"), f"{e}")
        self._reload_asr_models()

    @Slot()
    def _import_local_vosk_zip(self):
        path, _ = QFileDialog.getOpenFileName(self, t("dlg.import_asr_pick"), "", "ZIP (*.zip)")
        if not path:
            return
        if unzip_to_models(self, path):
            QMessageBox.information(self, t("dlg.title.done"), t("dlg.unzip_ok"))
            self._reload_asr_models()

    def _pair_text(self, s: str, t2: str) -> str:
        return f"{s}->{t2}"

    @Slot()
    def _reload_trans_models(self):
        src = self.asrCombo.currentText()
        tgt = self.tgtCombo.currentText()
        self.transModelCombo.clear()
        if not ARGOS_OK:
            self.transModelCombo.addItem(t("combo.argos_missing"),
                                         {"installed": False, "pair": (src, tgt), "url": None})
            return
        installed = argos_pair_installed(src, tgt)
        pkg = argos_find_package(src, tgt)
        url = getattr(pkg, "download_url", None) if pkg else None
        tag = t("combo.installed") if installed else t("combo.not_installed")
        self.transModelCombo.addItem(f"{tag}{self._pair_text(src, tgt)}",
                                     {"installed": installed, "pair": (src, tgt), "url": url, "pkg": pkg})

    @Slot()
    def _maybe_download_selected_trans_model(self):
        data = self.transModelCombo.currentData()
        if not data or data.get("installed"):
            return
        if not ARGOS_OK:
            QMessageBox.warning(self, t("dlg.title.tip"), t("dlg.argos_not_installed"))
            return
        src, tgt = data.get("pair", ("", ""))
        pkg = data.get("pkg", None)
        if not pkg:
            QMessageBox.information(self, t("dlg.title.tip"), t("dlg.argos_index_missing"))
            return
        r = QMessageBox.question(self, t("dlg.title.download_trans"),
                                 t("dlg.ask.download_trans", src=src, tgt=tgt),
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if r != QMessageBox.Yes:
            return
        url = data.get("url", None)
        if url:
            tmp_dir = abs_path("_argos_tmp"); os.makedirs(tmp_dir, exist_ok=True)
            tmp_file = os.path.join(tmp_dir, f"{src}_{tgt}.argosmodel")
            def on_ok():
                ok, msg = argos_install_from_file(tmp_file)
                try:
                    if os.path.exists(tmp_file): os.remove(tmp_file)
                except Exception:
                    pass
                if ok:
                    QMessageBox.information(self, t("dlg.title.done"), t("dlg.argos_install_ok"))
                else:
                    QMessageBox.critical(self, t("dlg.title.fail"), t("dlg.argos_install_fail", err=msg))
            self._download_with_dialog(url, tmp_file, t("dlg.title.download_trans"),
                                       on_ok=on_ok, on_done=self._reload_trans_models)
        else:
            busy = QProgressDialog(t("dlg.download_busy", src=src, tgt=tgt), t("dlg.download_cancelled"), 0, 0, self)
            busy.setWindowModality(Qt.ApplicationModal)
            busy.setMinimumDuration(0)
            self._live_dialogs.add(busy)
            def _busy_cleanup():
                self._live_dialogs.discard(busy)
            busy.destroyed.connect(_busy_cleanup)
            busy.finished.connect(_busy_cleanup)

            worker = ArgosPkgDownloadWorker(pkg, parent=self)
            self._track_thread(worker)
            def on_finished(ok: bool, msg: str, path: str):
                busy.close()
                if not ok:
                    QMessageBox.critical(self, t("dlg.title.fail"), msg); return
                try:
                    from argostranslate import package as argospkg
                    argospkg.install_from_path(path)
                    QMessageBox.information(self, t("dlg.title.done"), t("dlg.argos_install_ok"))
                except Exception as e:
                    QMessageBox.critical(self, t("dlg.title.fail"), t("dlg.argos_install_fail", err=e))
                self._reload_trans_models()
            worker.finished.connect(on_finished)
            worker.start()

    @Slot()
    def _delete_selected_trans_model(self):
        data = self.transModelCombo.currentData()
        if not data or not data.get("installed"):
            QMessageBox.information(self, t("dlg.title.tip"), t("dlg.argos_pair_not_installed"))
            return
        if not ARGOS_OK:
            QMessageBox.warning(self, t("dlg.title.tip"), t("dlg.argos_not_installed"))
            return
        src, tgt = data.get("pair", ("", ""))
        r = QMessageBox.question(self, t("dlg.delete_confirm"), f"{t('dlg.delete_confirm')} {src}->{tgt}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if r != QMessageBox.Yes:
            return
        ok, msg = argos_uninstall_pair(self, src, tgt)
        if ok:
            QMessageBox.information(self, t("dlg.title.done"), t("dlg.argos_uninstall_ok"))
        else:
            QMessageBox.warning(self, t("dlg.title.tip"), t("dlg.argos_uninstall_fail"))
        self._reload_trans_models()

    def _download_with_dialog(self, url: str, save_to: str, title: str, on_ok=None, on_done=None):
        dlg = QProgressDialog(t("dlg.download.connecting"), t("dlg.download_cancelled"), 0, 100, self)
        dlg.setWindowTitle(title)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setMinimumDuration(0)
        dlg.setValue(0)
        self._live_dialogs.add(dlg)
        def _dlg_cleanup():
            self._live_dialogs.discard(dlg)
        dlg.destroyed.connect(_dlg_cleanup)
        dlg.finished.connect(_dlg_cleanup)

        worker = DownloadWorker(url, save_to, chunk_size=1024 * 256, parent=self)
        self._track_thread(worker)
        worker.progress.connect(dlg.setValue)

        def _cancel():
            worker.requestInterruption()
        dlg.canceled.connect(_cancel)

        def _finished(ok: bool, err: str):
            dlg.close()
            if ok:
                try:
                    if on_ok:
                        on_ok()
                finally:
                    if on_done:
                        on_done()
            else:
                try:
                    if os.path.exists(save_to):
                        os.remove(save_to)
                except Exception:
                    pass
                QMessageBox.critical(self, t("dlg.download_failed"), err or "unknown error")

        worker.finished.connect(_finished)
        worker.start()

    @Slot()
    def _import_local_argos_file(self):
        if not ARGOS_OK:
            QMessageBox.warning(self, t("dlg.title.tip"), t("dlg.argos_not_installed"))
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("dlg.import_trans_pick"),
            "",
            "Argos (*.argosmodel *.zip);;All Files (*)"
        )
        if not path:
            return
        ok, msg = argos_install_from_file(path)
        if ok:
            QMessageBox.information(self, t("dlg.title.done"), t("dlg.argos_install_ok"))
        else:
            QMessageBox.critical(self, t("dlg.title.fail"), t("dlg.argos_install_fail", err=msg))
        self._reload_trans_models()

    def _emit_subtitle_style(self):
        key = self.styleCombo.currentData() or "bold"
        size = int(self.sizeSpin.value())
        self.subtitleStyleChanged.emit(key, size)

    def emit_current_subtitle_style(self):
        self._emit_subtitle_style()
