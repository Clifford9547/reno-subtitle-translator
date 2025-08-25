import os, re, shutil, zipfile
from typing import Tuple, Optional, List, Dict
from .i18n import t

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
def abs_path(*parts):
    return os.path.join(ROOT_DIR, *parts)

MODELS_DIR = abs_path("models")

# ----------------- Vosk 模型索引与本地扫描 -----------------
KNOWN_VOSK_MODELS: Dict[str, List[Dict]] = {
    "ja": [
        {"label": "small-ja-0.22（默认）", "folder": "vosk-model-small-ja-0.22",
         "url": "https://alphacephei.com/vosk/models/vosk-model-small-ja-0.22.zip", "recommended": True},
        {"label": "ja-0.22（精度更高）", "folder": "vosk-model-ja-0.22",
         "url": "https://alphacephei.com/vosk/models/vosk-model-ja-0.22.zip", "recommended": False}
    ],
    "zh": [
        {"label": "small-cn-0.22（默认）", "folder": "vosk-model-small-cn-0.22",
         "url": "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip", "recommended": True},
        {"label": "cn-0.22（精度更高）", "folder": "vosk-model-cn-0.22",
         "url": "https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip", "recommended": False}
    ],
    "en": [
        {"label": "small-en-us-0.15（默认）", "folder": "vosk-model-small-en-us-0.15",
         "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip", "recommended": True},
        {"label": "en-us-0.22（精度更高）", "folder": "vosk-model-en-us-0.22",
         "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip", "recommended": False},
        {"label": "en-us-0.22-lgraph（内存省）", "folder": "vosk-model-en-us-0.22-lgraph",
         "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip", "recommended": False}
    ],
}

LANG_HINTS_REGEX = {
    "ja": re.compile(r"(vosk-model.*ja.*)", re.IGNORECASE),
    "zh": re.compile(r"(vosk-model.*cn.*)", re.IGNORECASE),
    "en": re.compile(r"(vosk-model.*en.*)", re.IGNORECASE),
}

def list_local_vosk_models(lang_code: str) -> List[Dict]:
    results: List[Dict] = []
    if not os.path.isdir(MODELS_DIR):
        os.makedirs(MODELS_DIR, exist_ok=True)
    hint = LANG_HINTS_REGEX.get(lang_code)
    if hint:
        for name in sorted(os.listdir(MODELS_DIR)):
            full = os.path.join(MODELS_DIR, name)
            if os.path.isdir(full) and hint.match(name):
                results.append({"label": f"{name}（本地）", "folder": name, "url": None,
                                "recommended": False, "installed": True})
    known = KNOWN_VOSK_MODELS.get(lang_code, [])
    known_map = {k["folder"]: k for k in known}
    for folder, k in known_map.items():
        if not any(x["folder"] == folder for x in results):
            results.append({**k, "installed": False})
        else:
            for x in results:
                if x["folder"] == folder:
                    x["recommended"] = k.get("recommended", False)
    results.sort(key=lambda x: (not x.get("recommended", False),
                                not x.get("installed", False), x["label"]))
    return results

def ensure_vosk_model_ready(folder_name: str) -> Tuple[bool, str]:
    p = os.path.join(MODELS_DIR, folder_name)
    if not os.path.isdir(p):
        return False, f"未安装模型目录：{p}"
    ok = os.path.exists(os.path.join(p, "model.conf")) or os.path.isdir(os.path.join(p, "am"))
    return (True, "ok") if ok else (False, f"模型结构异常：{p}")

# ----------------- ZIP 解压到 ./models -----------------
def unzip_to_models(parent_qwidget, zip_path: str) -> bool:
    from PySide6.QtWidgets import QMessageBox
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            members = zf.namelist()
            root = members[0].split('/')[0] if members else ""
            target_dir = os.path.join(MODELS_DIR, root) if root else MODELS_DIR
            if root and os.path.isdir(target_dir):
                r = QMessageBox.question(parent_qwidget, t("dlg.title.overwrite"),
                                         f"{t('dlg.title.overwrite')}: {root}\n",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if r != QMessageBox.Yes:
                    return False
                shutil.rmtree(target_dir, ignore_errors=True)
            zf.extractall(MODELS_DIR)
        return True
    except Exception as e:
        QMessageBox.critical(parent_qwidget, t("dlg.title.fail"), t("dlg.unzip_fail", err=e))
        return False
    finally:
        try:
            os.remove(zip_path)
        except Exception:
            pass

# ----------------- Argos Translate 工具 -----------------
ARGOS_OK = False
try:
    import argostranslate.translate as argos
    import argostranslate.package as argospkg
    ARGOS_OK = True
except Exception:
    ARGOS_OK = False

def argos_pair_installed(src: str, tgt: str) -> bool:
    if not ARGOS_OK:
        return False
    try:
        langs = {l.code: l for l in argos.get_installed_languages()}
        if not (langs.get(src) and langs.get(tgt)):
            return False
        tr = langs[src].get_translation(langs[tgt])
        return tr is not None
    except Exception:
        return False

def argos_find_package(src: str, tgt: str):
    if not ARGOS_OK:
        return None
    try:
        argospkg.update_package_index()
        avail = argospkg.get_available_packages()
        for p in avail:
            if getattr(p, "from_code", "") == src and getattr(p, "to_code", "") == tgt:
                return p
    except Exception:
        pass
    return None

def argos_install_from_file(path: str):
    if not ARGOS_OK:
        return False, "argostranslate 未安装"
    try:
        argospkg.install_from_path(path)
        return True, "安装成功"
    except Exception as e:
        return False, f"安装失败：{e}"

def argos_uninstall_pair(parent_qwidget, src: str, tgt: str):
    if not ARGOS_OK:
        return False, "argostranslate 未安装"
    try:
        if hasattr(argospkg, "get_installed_packages"):
            pkgs = argospkg.get_installed_packages()
            for p in pkgs:
                if getattr(p, "from_code", None) == src and getattr(p, "to_code", None) == tgt:
                    if hasattr(argospkg, "uninstall"):
                        argospkg.uninstall(p)
                        return True, "卸载成功"
                    d = getattr(p, "package_path", None) or getattr(p, "install_dir", None)
                    if d and os.path.isdir(d):
                        shutil.rmtree(d, ignore_errors=True)
                        return True, "卸载成功（直接删除包目录）"
    except Exception:
        pass
    return False, "未能自动卸载，请手动删除 Argos 包目录（不同系统路径不同）。"

# 翻译路线
class TranslateRoute:
    AUTO = "auto"
    DIRECT = "prefer_direct"
    VIA_EN = "prefer_via_en"

def argos_translate(text: str, src: str, tgt: str, route: str = TranslateRoute.AUTO) -> str:
    if not text or not text.strip() or src == tgt or not ARGOS_OK:
        return text
    try:
        langs = argos.get_installed_languages()
        by = {l.code: l for l in langs}
        def has(a, b):
            try:
                return bool(by.get(a) and by.get(b) and by[a].get_translation(by[b]))
            except Exception:
                return False
        def do(a, b, s):
            tr = by[a].get_translation(by[b]); return tr.translate(s)
        norm = {"zh-cn": "zh", "zh_hans": "zh", "ja-jp": "ja", "jp": "ja"}
        src = norm.get(src.lower(), src.lower()); tgt = norm.get(tgt.lower(), tgt.lower())
        if route == TranslateRoute.DIRECT and has(src, tgt):
            return do(src, tgt, text)
        if route == TranslateRoute.VIA_EN and has(src, "en") and has("en", tgt):
            return do("en", tgt, do(src, "en", text))
        if has(src, tgt):
            return do(src, tgt, text)
        if src != "en" and tgt != "en" and has(src, "en") and has("en", tgt):
            return do("en", tgt, do(src, "en", text))
    except Exception:
        pass
    return text
