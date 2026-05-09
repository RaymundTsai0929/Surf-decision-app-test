@echo off
setlocal
set "PROJECT=D:\VibeCoding\研究論文Prototype\W1"
set "PYTHON_EXE=%PROJECT%\.venv\Scripts\python.exe"

if not exist "%PROJECT%" (
  echo [錯誤] 找不到專案資料夾：%PROJECT%
  pause
  exit /b 1
)

if not exist "%PYTHON_EXE%" (
  echo [錯誤] 找不到虛擬環境 Python：%PYTHON_EXE%
  echo 請先建立 .venv（python -m venv .venv）
  pause
  exit /b 1
)

set "PIP_CACHE_DIR=D:\VibeCoding\pip_cache"
set "TEMP=D:\VibeCoding\tmp"
set "TMP=D:\VibeCoding\tmp"
if not exist "%PIP_CACHE_DIR%" mkdir "%PIP_CACHE_DIR%"
if not exist "%TEMP%" mkdir "%TEMP%"

cd /d "%PROJECT%"
set "APP_PORT=8501"
start "" "http://localhost:%APP_PORT%"
"%PYTHON_EXE%" -m streamlit run src/streamlit_app.py --server.port %APP_PORT%

endlocal
