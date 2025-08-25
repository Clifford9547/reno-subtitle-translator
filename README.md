# Rove Subtitle Translator

## English

### Overview

Reno Subtitle Translator is a lightweight real-time multimedia translation tool. It captures the audio currently playing on your computer, performs live speech recognition and translation, and renders on-screen subtitles. It supports Chinese, Japanese, and English, providing real-time bilingual subtitles for online meetings and video content.

Key features:

* Capture system audio via a microphone array
* Real-time original and translated subtitles
* Customizable subtitle font style and size
* Switchable UI language (English/Chinese)
* Manage speech recognition and translation models (download, import, delete)

### Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Dependencies include:

* PySide6 (GUI)
* numpy (audio processing)
* pyaudio (audio capture)
* vosk (speech recognition)
* argostranslate (translation engine, optional)

### Usage

Run the program:

```bash
python main.py
```

First-time setup:

1. Select recognition and target languages.
2. If no models are installed, the software can automatically download them after confirmation. You can also import models manually:

   * Vosk models: download `.zip` and extract to `./models/` (or let the app download automatically)
   * Argos models: download `.argosmodel` and import (or let the app download automatically)
3. Ensure the system has a microphone array enabled. Stereo Mix is not supported.

### Adding Models

The program supports both automatic and manual model installation:

* **Automatic**: When you select an uninstalled recognition or translation model, the app will prompt you to download and install it.
* **Manual**:

  * Vosk: download from [Vosk models](https://alphacephei.com/vosk/models), unzip to `./models/`
  * Argos Translate: download `.argosmodel` files from [Argos model list](https://www.argosopentech.com/argospm/) and import them via the UI

### Screenshots

![alt text](image.png)
![alt text](image-1.png)
## 中文说明

### 项目简介

Reno Subtitle Translator 是一款轻量化的实时多媒体翻译工具。它能够将电脑正在播放的音频实时识别与翻译，并以字幕形式显示在屏幕上。当前支持中文、日文、英文，可为在线会议与视频等场景提供实时双语字幕。

主要功能：

* 通过麦克风阵列捕获电脑播放的声音
* 实时显示原文字幕与翻译字幕
* 支持自定义字幕字体样式和大小
* 支持中英文界面切换
* 管理语音识别与翻译模型（下载、导入、删除）

### 环境依赖

安装依赖：

```bash
pip install -r requirements.txt
```

依赖包括：

* PySide6（图形界面）
* numpy（音频处理）
* pyaudio（音频捕获）
* vosk（语音识别）
* argostranslate（翻译引擎，可选）

### 使用方法

运行程序：

```bash
python main.py
```

首次使用步骤：

1. 选择识别语言和目标语言。
2. 如果没有安装模型，软件会自动提示下载并安装；也可以手动导入：

   * Vosk 模型：下载 `.zip` 并解压到 `./models/`（或由软件自动下载）
   * Argos 模型：下载 `.argosmodel` 并在界面导入（或由软件自动下载）
3. 请确保系统已启用麦克风阵列。本程序不支持立体声混音。

### 模型获取

本程序支持自动和手动两种模型获取方式：

* **自动下载**：当选择未安装的识别或翻译模型时，软件会弹窗提示下载并自动安装。
* **手动安装**：

  * Vosk：从 [Vosk 模型下载页](https://alphacephei.com/vosk/models) 获取并解压到 `./models/`
  * Argos Translate：从 [Argos 模型列表](https://www.argosopentech.com/argospm/) 下载 `.argosmodel` 文件并在界面导入

### 截图

![alt text](image.png)
