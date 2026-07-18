@echo off
echo.
echo  Installing RHCT Agent dependencies...
echo  ======================================
pip install flask anthropic twilio requests
echo.
echo  Done! Now run:  run_agent.bat
pause
