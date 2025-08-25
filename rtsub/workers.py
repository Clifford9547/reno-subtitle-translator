import os, json, time, queue
from urllib.request import urlopen, Request
from typing import Optional
import numpy as np
import pyaudio
from PySide6.QtCore import QThread, Signal, Slot

import vosk

from .utils import MODELS_DIR, ensure_vosk_model_ready, argos_translate, TranslateRoute

# ----------------- 下载线程 -----------------
class DownloadWorker(QThread):
    progress = Signal(int)
    finished = Signal(bool, str)
    def __init__(self, url: str, dest_path: str, chunk_size: int = 1024 * 256, parent=None):
        super().__init__(parent)
        self.url = url
        self.dest_path = dest_path
        self.chunk = chunk_size
    def run(self):
        try:
            req = Request(self.url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=60) as resp:
                total = resp.length or 0
                done = 0
                with open(self.dest_path, "wb") as f:
                    while True:
                        if self.isInterruptionRequested():
                            try:
                                f.close(); os.remove(self.dest_path)
                            except Exception:
                                pass
                            self.finished.emit(False, "已取消")
                            return
                        data = resp.read(self.chunk)
                        if not data:
                            break
                        f.write(data)
                        done += len(data)
                        if total > 0:
                            pct = int(done * 100 / total)
                            self.progress.emit(min(100, pct))
            self.progress.emit(100)
            self.finished.emit(True, "")
        except Exception as e:
            try:
                if os.path.exists(self.dest_path):
                    os.remove(self.dest_path)
            except Exception:
                pass
            self.finished.emit(False, f"{e}")

# ----------------- Argos 包下载线程 -----------------
class ArgosPkgDownloadWorker(QThread):
    finished = Signal(bool, str, str)
    def __init__(self, pkg, parent=None):
        super().__init__(parent)
        self.pkg = pkg
    def run(self):
        try:
            path = self.pkg.download()
            self.finished.emit(True, "下载完成", path)
        except Exception as e:
            self.finished.emit(False, f"下载失败：{e}", "")

# ----------------- 录音线程 -----------------
class AudioCaptureWorker(QThread):
    levelChanged = Signal(float)
    chunkReady = Signal(bytes)
    error = Signal(str)
    def __init__(self, device_index: Optional[int], rate=16000, chunk=1024, parent=None):
        super().__init__(parent)
        self.device_index = device_index
        self.rate = rate
        self.chunk = chunk
        self.channels = 1
        self._stop = False
        self.input_rate = None
        self.target_rate = rate
    def stop(self):
        self._stop = True
    def _resample_to_16k(self, audio_np: np.ndarray) -> bytes:
        if self.input_rate == self.target_rate:
            return audio_np.tobytes()
        src = float(self.input_rate); dst = float(self.target_rate)
        if audio_np.size == 0:
            return b""
        dst_len = int(round(audio_np.size * dst / src))
        if dst_len <= 0:
            return b""
        x_old = np.linspace(0, 1, num=audio_np.size, endpoint=False, dtype=np.float64)
        x_new = np.linspace(0, 1, num=dst_len, endpoint=False, dtype=np.float64)
        y = np.interp(x_new, x_old, audio_np.astype(np.float64))
        y = np.clip(y, -32768, 32767).astype(np.int16)
        return y.tobytes()
    def run(self):
        pa = pyaudio.PyAudio()
        stream = None
        try:
            dev_info = pa.get_device_info_by_index(self.device_index) if self.device_index is not None else pa.get_default_input_device_info()
            self.input_rate = int(dev_info.get("defaultSampleRate", 16000)) or 16000
            stream = pa.open(format=pyaudio.paInt16, channels=self.channels, rate=int(self.input_rate),
                             input=True, input_device_index=self.device_index, frames_per_buffer=self.chunk)
            level_hist = []
            while not self._stop and not self.isInterruptionRequested():
                data = stream.read(self.chunk, exception_on_overflow=False)
                audio = np.frombuffer(data, dtype=np.int16)
                if audio.size == 0:
                    continue
                rms = float(np.sqrt(np.mean((audio.astype(np.float64) ** 2))))
                level_hist.append(rms)
                if len(level_hist) > 30:
                    level_hist.pop(0)
                import numpy as _np
                ref = max(100.0, _np.percentile(level_hist, 95)) if level_hist else 1500.0
                level_percent = max(0.0, min(100.0, (rms / ref) * 100.0))
                self.levelChanged.emit(level_percent)
                resampled = self._resample_to_16k(audio)
                self.chunkReady.emit(resampled)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            try:
                if stream:
                    stream.stop_stream(); stream.close()
            except Exception:
                pass
            pa.terminate()

# ----------------- 识别 + 翻译线程 -----------------
class ASRWorker(QThread):
    textReady = Signal(str, str)
    status = Signal(str)
    error = Signal(str)
    def __init__(self, asr_lang="ja", tgt_lang="zh",
                 route=TranslateRoute.AUTO, model_folder=None, rate=16000, parent=None):
        super().__init__(parent)
        self.asr_lang = asr_lang
        self.tgt_lang = tgt_lang
        self.route = route
        self.model_folder = model_folder
        self.rate = rate
        self._stop = False
        self._queue = queue.Queue()
        self.segment_timeout = 1.0
        self.min_chars = 5
        self.src_max = 72
        self.tgt_max = 100
        self._puncts = set(".,!?，。！？、;；:")
        self._cur_partial = ""
        self._last_change_ts = 0.0
    def stop(self):
        self._stop = True
    @Slot(bytes)
    def feed(self, audio_bytes: bytes):
        if not self._stop:
            self._queue.put(audio_bytes)
    def _clip(self, s: str, limit: int) -> str:
        s = s or ""
        return (s[:limit] + "...") if len(s) > limit else s
    def _flush_segment(self, text: str):
        text = (text or "").strip()
        if not text:
            return
        try:
            trans = argos_translate(text, self.asr_lang, self.tgt_lang, route=self.route) or text
        except Exception:
            trans = text
        self.textReady.emit(self._clip(text, self.src_max), self._clip(trans, self.tgt_max))
    def run(self):
        if not self.model_folder:
            self.error.emit("未指定识别模型目录")
            return
        model_path = os.path.join(MODELS_DIR, self.model_folder)
        ok, msg = ensure_vosk_model_ready(self.model_folder)
        if not ok:
            self.error.emit(msg); return
        try:
            model = vosk.Model(model_path)
            rec = vosk.KaldiRecognizer(model, self.rate)
        except Exception as e:
            self.error.emit(f"加载模型失败：{e}"); return
        self._cur_partial = ""
        self._last_change_ts = time.time()
        while not self._stop and not self.isInterruptionRequested():
            try:
                data = self._queue.get(timeout=0.2)
            except queue.Empty:
                now = time.time()
                if self._cur_partial and (now - self._last_change_ts) >= self.segment_timeout and len(self._cur_partial) >= self.min_chars:
                    self._flush_segment(self._cur_partial)
                    self._cur_partial = ""
                continue
            try:
                is_final = rec.AcceptWaveform(data)
            except Exception as e:
                self.status.emit(f"识别错误：{e}")
                continue
            if is_final:
                try:
                    r = json.loads(rec.Result() or "{}"); final_seg = (r.get("text") or "").strip()
                except Exception:
                    final_seg = ""
                if final_seg:
                    self._flush_segment(final_seg)
                self._cur_partial = ""
                self._last_change_ts = time.time()
                continue
            try:
                pr = json.loads(rec.PartialResult() or "{}").get("partial", ""); pr = (pr or "").strip()
            except Exception:
                pr = ""
            if pr and pr != self._cur_partial:
                self._cur_partial = pr
                self._last_change_ts = time.time()
                if pr[-1:] in self._puncts or len(pr) >= self.src_max:
                    self._flush_segment(pr)
                    self._cur_partial = ""
                    self._last_change_ts = time.time()
                    continue
            now = time.time()
            if self._cur_partial and (now - self._last_change_ts) >= self.segment_timeout and len(self._cur_partial) >= self.min_chars:
                self._flush_segment(self._cur_partial)
                self._cur_partial = ""
                self._last_change_ts = now
