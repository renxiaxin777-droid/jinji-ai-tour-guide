@echo off
chcp 65001 >nul
title 晋迹 · 山西古建智能导览体
cd /d "%~dp0"
echo ==================================================
echo    晋迹 · 山西古建智能导览体  —— 正在启动
echo ==================================================
echo.

if exist ".venv\Scripts\python.exe" goto :run

echo [1/3] 首次运行：创建虚拟环境...
python -m venv .venv
if errorlevel 1 (
    echo [错误] 没找到 Python，请先安装 Python 3.11+ 并勾选 Add to PATH
    pause & exit /b 1
)

echo [2/3] 安装依赖（首次约 1-3 分钟，请耐心等待）...
.venv\Scripts\python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
if errorlevel 1 (
    where uv >nul 2>nul
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络后重试
        pause & exit /b 1
    )
    echo [提示] 改用 uv 安装...
    uv pip install --python .venv\Scripts\python.exe --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
)

:run
echo [3/3] 启动中... 浏览器将自动打开 http://localhost:8501
echo.
echo   ★ 若未配置 secret.py，将进入「离线演示模式」（断网也能演示完整流程）
echo   ★ 关闭本窗口即可停止应用
echo.
start "" http://localhost:8501
.venv\Scripts\python -m streamlit run app.py
pause
