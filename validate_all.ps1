$ErrorActionPreference = "Stop"

Write-Host "====================================="
Write-Host "ELIOS-SAR FULL VALIDATION"
Write-Host "====================================="

Write-Host "`n[1/5] Python version"
& ".\.venv-experimental-ai\Scripts\python.exe" --version

Write-Host "`n[2/5] Compile source"
& ".\.venv-experimental-ai\Scripts\python.exe" -m compileall src apps tests

Write-Host "`n[3/5] Import validation"
& ".\.venv-experimental-ai\Scripts\python.exe" apps\validate_system.py

Write-Host "`n[4/5] Unit tests"
& ".\.venv-experimental-ai\Scripts\python.exe" -m pytest tests/ -v

Write-Host "`n[5/5] Self test"
& ".\.venv-experimental-ai\Scripts\python.exe" apps\self_test.py

Write-Host "`n====================================="
Write-Host "ALL VALIDATION STEPS PASSED"
Write-Host "====================================="
