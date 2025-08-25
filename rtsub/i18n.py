from typing import Dict

_LANG = "en"

LANG_MAP = {
    "zh": "中文",
    "en": "English",
}

T: Dict[str, Dict[str, str]] = {
    "zh": {
        "app.title": "Reno字幕翻译器",
        "menu.lang": "语言",
        "menu.lang.zh": "中文",
        "menu.lang.en": "English",

        "group.lang_model": "语言与模型",
        "label.asr_lang": "识别语言",
        "label.tgt_lang": "目标语言",
        "label.asr_model": "识别模型",
        "label.trans_model": "翻译模型",

        "group.audio": "音频输入设备",
        "label.input": "输入源",
        "input.auto": "自动选择",

        "group.status": "运行状态",
        "label.status": "状态：",
        "label.engine": "翻译引擎：",
        "label.level": "音频电平：",

        "group.ui_lang": "语言",
        "label.ui_lang": "语言",

        "group.subtitle": "字幕样式",
        "label.font_style": "样式",
        "label.font_size": "大小",
        "style.regular": "常规",
        "style.bold": "加粗",
        "style.italic": "斜体",
        "style.bold_italic": "加粗斜体",

        "btn.delete": "删除",
        "btn.import": "导入",
        "btn.start": "开始监听 (Ctrl+Shift+S)",
        "btn.stop": "停止监听 (Ctrl+Shift+S)",

        "status.idle": "未开始",
        "status.listening": "监听中 ...",
        "status.stopped": "已停止",
        "engine.ready": "待准备",
        "engine.no_argos": "未安装 argostranslate（仍可只显示原文）",
        "engine.pairs_installed": "已装",
        "engine.pairs_missing": "缺少该方向词典",

        "msg.no_input_device": "未找到可用的输入设备。\n请启用立体声混音/Loopback，或手动选择麦克风/回环设备。",
        "msg.select_model_first": "请先选择或安装识别模型。",
        "msg.asr_model_unavailable": "识别模型不可用：{msg}",
        "msg.asr_thread_fail": "启动识别线程失败：{err}",
        "msg.cap_thread_fail": "启动录音线程失败：{err}",
        "msg.asr_error": "错误：识别失败 - {msg}",
        "msg.cap_error": "错误：录音失败 - {msg}",

        "dlg.title.download_asr": "下载识别模型",
        "dlg.title.download_trans": "下载翻译模型",
        "dlg.title.overwrite": "覆盖确认",
        "dlg.title.done": "完成",
        "dlg.title.fail": "失败",
        "dlg.title.tip": "提示",

        "dlg.ask.download_asr": "是否下载并安装模型：{label}？\n将解压到 ./models/{folder}",
        "dlg.ask.download_trans": "是否下载并安装翻译包：{src}->{tgt}？",
        "dlg.ask.delete_model": "确定删除模型目录？\n{path}",
        "dlg.done.deleted": "已删除。",
        "dlg.no_link_use_import": "该条目没有可用下载链接，请使用右侧“导入”选择本地 ZIP。",
        "dlg.not_installed": "当前选择的模型未安装或无目录。",
        "dlg.unzip_ok": "已导入并解压到 ./models/",
        "dlg.unzip_fail": "解压错误：{err}",
        "dlg.download.connecting": "连接中…",
        "dlg.download_cancelled": "已取消",
        "dlg.download_failed": "下载失败",
        "dlg.delete_confirm": "删除确认",
        "dlg.import_asr_pick": "选择 Vosk 模型 ZIP",
        "dlg.import_trans_pick": "选择 Argos 翻译包",
        "dlg.argos_not_installed": "未安装 argostranslate 库。",
        "dlg.argos_install_ok": "安装成功",
        "dlg.argos_install_fail": "安装失败：{err}",
        "dlg.argos_uninstall_ok": "卸载成功",
        "dlg.argos_uninstall_fail": "未能自动卸载，请手动删除 Argos 包目录（不同系统路径不同）。",
        "dlg.argos_pair_not_installed": "该语言对未安装。",
        "dlg.argos_index_missing": "官方索引未找到该语言对，请尝试右侧“导入”安装本地包。",
        "dlg.download_busy": "下载 {src}->{tgt} …",

        "combo.no_models": "（未发现模型，请下载或导入）",
        "combo.argos_missing": "（未安装 argostranslate 库）",
        "combo.installed": "[已装] ",
        "combo.not_installed": "[未装] ",
        "combo.recommended": "★ ",

        "toast.listening_en": "Listening...",
        "toast.listening_zh": "正在监听…",
    },
    "en": {
        "app.title": "Reno Subtitle Translator",
        "menu.lang": "Language",
        "menu.lang.zh": "Chinese",
        "menu.lang.en": "English",

        "group.lang_model": "Languages & Models",
        "label.asr_lang": "ASR Lang",
        "label.tgt_lang": "Target Lang",
        "label.asr_model": "ASR Model",
        "label.trans_model": "Translation Model",

        "group.audio": "Audio Input",
        "label.input": "Input Device",
        "input.auto": "Auto Select",

        "group.status": "Status",
        "label.status": "Status: ",
        "label.engine": "Translator: ",
        "label.level": "Level: ",

        "group.subtitle": "Subtitles",
        "label.font_style": "Style",
        "label.font_size": "Size",
        "style.regular": "Regular",
        "style.bold": "Bold",
        "style.italic": "Italic",
        "style.bold_italic": "Bold Italic",

        "group.ui_lang": "Language",
        "label.ui_lang": "Language",

        "btn.delete": "Delete",
        "btn.import": "Import",
        "btn.start": "Start (Ctrl+Shift+S)",
        "btn.stop": "Stop (Ctrl+Shift+S)",

        "status.idle": "Idle",
        "status.listening": "Listening ...",
        "status.stopped": "Stopped",
        "engine.ready": "Preparing",
        "engine.no_argos": "Argos not installed (will show source only)",
        "engine.pairs_installed": "Installed",
        "engine.pairs_missing": "Pair missing",

        "msg.no_input_device": "No input device found.\nEnable Stereo Mix/Loopback, or select a mic/monitor device.",
        "msg.select_model_first": "Please select or install an ASR model first.",
        "msg.asr_model_unavailable": "ASR model not available: {msg}",
        "msg.asr_thread_fail": "Failed to start ASR thread: {err}",
        "msg.cap_thread_fail": "Failed to start capture thread: {err}",
        "msg.asr_error": "Error: ASR failed - {msg}",
        "msg.cap_error": "Error: capture failed - {msg}",

        "dlg.title.download_asr": "Download ASR Model",
        "dlg.title.download_trans": "Download Translation Model",
        "dlg.title.overwrite": "Overwrite Confirmation",
        "dlg.title.done": "Done",
        "dlg.title.fail": "Failed",
        "dlg.title.tip": "Info",

        "dlg.ask.download_asr": "Download and install model: {label}?\nWill extract to ./models/{folder}",
        "dlg.ask.download_trans": "Download and install translation pair: {src}->{tgt}?",
        "dlg.ask.delete_model": "Delete model directory?\n{path}",
        "dlg.done.deleted": "Deleted.",
        "dlg.no_link_use_import": "No downloadable link for this entry. Use 'Import' to select a local ZIP.",
        "dlg.not_installed": "The selected model is not installed or has no directory.",
        "dlg.unzip_ok": "Imported and extracted to ./models/",
        "dlg.unzip_fail": "Unzip error: {err}",
        "dlg.download.connecting": "Connecting…",
        "dlg.download_cancelled": "Cancelled",
        "dlg.download_failed": "Download failed",
        "dlg.delete_confirm": "Delete Confirmation",
        "dlg.import_asr_pick": "Select Vosk Model ZIP",
        "dlg.import_trans_pick": "Select Argos Package",
        "dlg.argos_not_installed": "argostranslate is not installed.",
        "dlg.argos_install_ok": "Installed successfully",
        "dlg.argos_install_fail": "Install failed: {err}",
        "dlg.argos_uninstall_ok": "Uninstalled successfully",
        "dlg.argos_uninstall_fail": "Automatic uninstall failed. Please remove the Argos package directory manually.",
        "dlg.argos_pair_not_installed": "This language pair is not installed.",
        "dlg.argos_index_missing": "Language pair not found in the official index. Try 'Import' with a local package.",
        "dlg.download_busy": "Downloading {src}->{tgt} …",

        "combo.no_models": "(No models found. Download or import one.)",
        "combo.argos_missing": "(argostranslate not installed)",
        "combo.installed": "[Installed] ",
        "combo.not_installed": "[Not Installed] ",
        "combo.recommended": "★ ",

        "toast.listening_en": "Listening...",
        "toast.listening_zh": "Listening...",
    }
}

def set_lang(code: str):
    global _LANG
    _LANG = "zh" if code.lower().startswith("zh") else "en"

def get_lang() -> str:
    return _LANG

def t(key: str, **kwargs) -> str:
    table = T.get(_LANG, T["en"])
    s = table.get(key, T["en"].get(key, key))
    return s.format(**kwargs) if kwargs else s
