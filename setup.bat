@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ==================================================
echo   B 站路演视频：转文字 + 答辩问答    首次安装
echo ==================================================
echo.

where python >nul 2>nul
if errorlevel 1 goto nopython

echo [1/4] 检查依赖是否已安装 ...
python -c "import faster_whisper, requests, yt_dlp" >nul 2>nul
if not errorlevel 1 goto deps_ok

if exist ".venv\Scripts\python.exe" goto venv_exists
echo       创建虚拟环境 .venv ...
python -m venv .venv
if errorlevel 1 goto venvfail
:venv_exists
set "PY=.venv\Scripts\python.exe"

echo [2/4] 安装依赖（首次较久；nvidia-cublas-cu12 约 550MB，请耐心等待）...
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto pipfail
goto ffmpeg_check

:deps_ok
echo       当前 Python 已装好依赖，跳过安装（直接用 run.bat 即可）。
set "PY=python"

:ffmpeg_check
echo [3/4] 检查 ffmpeg ...
where ffmpeg >nul 2>nul
if not errorlevel 1 goto ffmpeg_ok
echo       [提醒] PATH 里没找到 ffmpeg，请在 config_local.py 里填写 FFMPEG_PATH。
echo              下载地址：https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
goto cfg

:ffmpeg_ok
echo       ffmpeg 已就绪。

:cfg
echo [4/4] 准备配置文件 config_local.py ...
if exist "config_local.py" goto cfg_ok
copy /y "config_local.example.py" "config_local.py" >nul
echo       已生成 config_local.py，请用记事本打开并填写 3 项配置。
goto done

:cfg_ok
echo       config_local.py 已存在，保留不动。

:done
echo.
echo ==================================================
echo   安装完成！接下来：
echo     1) 用记事本打开 config_local.py，填好 SESSDATA / LLM_API_KEY / FFMPEG_PATH
echo     2) 双击 run.bat 开始使用
echo ==================================================
echo.
pause
exit /b 0

:nopython
echo [错误] 没找到 python 命令。
echo        请先安装 Python 3.10 或更高版本：https://www.python.org/downloads/
echo        安装时务必勾选 "Add python.exe to PATH"，装完重开窗口再运行本脚本。
echo.
pause
exit /b 1

:venvfail
echo [错误] 创建虚拟环境失败，请检查 Python 安装是否完整。
pause
exit /b 1

:pipfail
echo [错误] 依赖安装失败，请检查网络后重试。
pause
exit /b 1
