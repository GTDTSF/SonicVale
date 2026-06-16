# SonicVale-D 打包指南

## 前置条件

- **Python** 3.10+（含 `uvicorn`, `fastapi`, `sqlalchemy` 等依赖，见 `SonicVale/pyproject.toml`）
- **Node.js** 18+（含 `npm`）
- **PyInstaller** `pip install pyinstaller`

## 打包步骤

### 1. 构建 Python 后端 → main.exe

```powershell
cd SonicVale
python -m PyInstaller --onefile --name main `
  --add-data "app/core/ffmpeg/ffmpeg.exe;core/ffmpeg" `
  --hidden-import=uvicorn.logging `
  --hidden-import=uvicorn.loops.auto `
  --hidden-import=uvicorn.protocols.http.auto `
  --hidden-import=sqlalchemy.ext.declarative `
  app/main.py
```

### 2. 复制 main.exe 到 Electron 目录

```powershell
Copy-Item "dist\main.exe" "..\sonicvale-front\electron\main.exe" -Force
```

### 3. 构建前端 & 打包安装包

```powershell
cd ..\sonicvale-front
npm run build
npx electron-builder --win
```

> 或者一步到位：`npm run electron-build`（等价于 `vite build && electron-builder`）

### 4. 输出

```
sonicvale-front\release\
├── SonicVale-D Setup 1.1.5.exe     ← NSIS 安装包
└── win-unpacked\                    ← 免安装版
```

## 数据目录

**应用数据**（数据库 + 音色参考音频，小文件）：

```
%APPDATA%\SonicVale-D\data\
├── app_test.db        ← SQLite 数据库
├── settings.json      ← 应用配置
├── voices\            ← 音色参考音频
└── app.log            ← 运行日志
```

**项目音频**（大文件，由用户配置）：

首次创建项目时提示选择默认路径（如 `D:\SonicVale-Projects\`），之后所有项目的生成音频保存在该路径下：

```
{DEFAULT_PATH}\
├── 01_第一章\
├── 02_第二章\
└── ...
```

可在 `配置中心 → 通用设置` 中修改默认路径，不影响已创建项目。
