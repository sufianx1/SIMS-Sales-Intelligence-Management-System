@echo off
title Stop SIMS Servers
cd /d "%~dp0"

echo Stopping any running SIMS servers on port 8000 (Backend) and port 5173 (Frontend)...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000, 5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue; Write-Host 'Stopped process' $_ }"

echo.
echo All SIMS servers have been stopped.
timeout /t 2 /nobreak >nul
