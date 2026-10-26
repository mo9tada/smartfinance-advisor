@echo off
REM Get the directory of this script
SET SCRIPTPATH=%~dp0
cd /d "%SCRIPTPATH%data_pipeline"
echo Running Data Pipeline...
python main.py
echo Pipeline execution finished.
pause
