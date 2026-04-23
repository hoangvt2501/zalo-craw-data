@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0stop-api.ps1" %*
