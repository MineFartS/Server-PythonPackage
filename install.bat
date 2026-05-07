@echo off

cd /d "%~dp0"

:: Install/Update Package
pip install --upgrade .

:: Locate package directory using pip
for /f "delims=" %%i in ('pip show philh_myftp_biz ^| findstr "Location:"') do set "DIR=%%i"
Set "DIR=%DIR:~10%\philh_myftp_biz"

:: Precompile package
python -m compileall -f "%DIR%"
