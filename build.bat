@echo off
chcp 65001 > nul  & rem 设置代码页为 UTF-8，防止中文乱码

echo.
echo ==========================================================
echo      EchoNote - PyInstaller 打包脚本
echo ==========================================================
echo.

echo 正在检查虚拟环境...
rem --- 1. 项目配置 (请根据需要修改) ---

rem 定义虚拟环境目录
set VIRTUAL_ENV_DIR=venv

rem 定义入口文件 (我们的主程序在 src 目录下)
set ENTRY_POINT=src\main.py

rem 定义输出目录
set OUTPUT_DIR=dist

rem 定义生成的可执行文件名
set EXE_NAME=EchoNote

rem 设置为 1 隐藏控制台窗口 (GUI程序必备)
set WINDOWED_MODE=1

rem 定义图标文件路径 (确保 src\icon.png 文件存在)
set ICON_FILE=src\icon.png

rem --- 配置结束 ---


rem 激活虚拟环境
if exist "%VIRTUAL_ENV_DIR%\Scripts\activate.bat" (
    echo 发现虚拟环境，正在激活...
    call "%VIRTUAL_ENV_DIR%\Scripts\activate.bat"
) else (
    echo 未找到虚拟环境，将使用系统 Python 环境。
)

echo 正在执行 PyInstaller...
rem 构建 PyInstaller 命令
set PYINSTALLER_COMMAND=pyinstaller --onefile --noconfirm

rem 设置窗口模式
if "%WINDOWED_MODE%"=="1" (
    set PYINSTALLER_COMMAND=%PYINSTALLER_COMMAND% --windowed
)

rem 设置图标
if exist "%ICON_FILE%" (
    set PYINSTALLER_COMMAND=%PYINSTALLER_COMMAND% --icon="%ICON_FILE%"
) else (
    echo.
    echo [警告] 未在 %ICON_FILE% 找到图标文件，将使用默认图标。
    echo.
)

rem 设置可执行文件名
if defined EXE_NAME (
    set PYINSTALLER_COMMAND=%PYINSTALLER_COMMAND% --name "%EXE_NAME%"
)

rem 设置输出目录
set PYINSTALLER_COMMAND=%PYINSTALLER_COMMAND% --distpath "%OUTPUT_DIR%"

rem --- 2. 添加项目特定的资源文件 ---
rem [重要] 我们的托盘图标 icon.png 是一个外部资源，必须手动添加。
rem 格式为 --add-data "源路径;目标路径"
rem "." 表示打包到 .exe 所在的根目录
set PYINSTALLER_COMMAND=%PYINSTALLER_COMMAND% --add-data "src\icon.png;."

rem 指定入口文件
set PYINSTALLER_COMMAND=%PYINSTALLER_COMMAND% "%ENTRY_POINT%"

echo.
echo ==========================================================
echo 即将执行以下命令:
echo %PYINSTALLER_COMMAND%
echo ==========================================================
echo.

rem 执行打包
%PYINSTALLER_COMMAND%

rem 检查打包是否成功
if %errorlevel% neq 0 (
    echo.
    echo [错误] PyInstaller 打包失败。请检查上面的错误信息。
    goto cleanup
)

echo.
echo PyInstaller 打包成功！
echo 可执行文件位于 %OUTPUT_DIR% 目录中。
echo.

:cleanup
echo 正在清理临时文件...
rem 清理 build 目录
if exist "build" (
    echo  - 正在删除 build 目录...
    rmdir /s /q "build"
)

rem 清理 spec 文件
if exist "%EXE_NAME%.spec" (
    echo  - 正在删除 %EXE_NAME%.spec 文件...
    del /f /q "%EXE_NAME%.spec"
)
echo 临时文件清理完成。

rem 如果激活了虚拟环境，则取消激活
if defined VIRTUAL_ENV (
    echo 正在取消激活虚拟环境...
    call deactivate
)

echo.
pause