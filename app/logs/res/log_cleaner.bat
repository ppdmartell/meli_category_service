REM Clean the main log. This is the first script that must be executed

@echo off
set INPUT="..\meli_category_service_log_2025-12-10.log"
set OUTPUT=filtered.log

findstr /C:"[DEBUG] app.core.category_service: Calling:" "%INPUT%" > "%OUTPUT%"
echo Done. Output saved in %OUTPUT%.