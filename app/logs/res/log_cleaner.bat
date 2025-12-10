@echo off
set INPUT="..\meli_category_builder.log"
set OUTPUT=filtered.log

findstr /C:"[DEBUG] meli_category_builder: [DEBUG] Calling:" "%INPUT%" > "%OUTPUT%"
echo Done. Output saved in %OUTPUT%.