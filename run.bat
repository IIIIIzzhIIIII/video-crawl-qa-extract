@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

rem 支持把视频文件直接拖到 run.bat 图标上使用
if not "%~1"=="" goto dropped

:menu
cls
echo ==================================================
echo   B 站路演视频  -^>  文字  -^>  答辩问答
echo ==================================================
echo   [1] 处理单个视频（输入 BV 号 或 拖入的文件路径）
echo   [2] 批量处理全部（转写 + 问答 + 高频问题清单）
echo   [3] 批量只转文字（不调用 DeepSeek，不产生费用）
echo   [4] 环境检查（GPU / 依赖 / 配置）
echo   [5] 退出
echo ==================================================
set "CHOICE="
set /p "CHOICE=请输入序号后回车: "
if "%CHOICE%"=="1" goto single
if "%CHOICE%"=="2" goto batch
if "%CHOICE%"=="3" goto batch_only
if "%CHOICE%"=="4" goto check
if "%CHOICE%"=="5" exit /b 0
goto menu

:single
echo.
set "TARGET="
set /p "TARGET=请输入 BV 号（如 BV1L8ez6RELH）或视频文件路径: "
if "%TARGET%"=="" goto menu
echo.
"%PY%" -X utf8 convert.py "%TARGET%" --qa
echo.
pause
goto menu

:batch
echo.
"%PY%" -X utf8 asr_cli.py all
echo.
pause
goto menu

:batch_only
echo.
"%PY%" -X utf8 asr_cli.py transcribe
echo.
pause
goto menu

:check
echo.
"%PY%" -X utf8 asr_cli.py check
echo.
pause
goto menu

:dropped
echo [拖入文件] %~1
"%PY%" -X utf8 convert.py "%~1" --qa
echo.
pause
exit /b 0
