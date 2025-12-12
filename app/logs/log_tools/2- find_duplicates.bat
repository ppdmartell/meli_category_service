@echo off
setlocal enabledelayedexpansion

REM === Generate timestamp: YYYYMMDD_HHMMSS ===
for /f "tokens=1-3 delims=/" %%a in ("%date%") do set d=%%c%%a%%b
for /f "tokens=1-3 delims=:." %%a in ("%time%") do set t=%%a%%b%%c
set "TIMESTAMP=%d%_%t%"


REM === Config ===
set "LOGFILE=filtered.log"
set "IDFILE=mlu_freq_%TIMESTAMP%.tmp"       REM final output file
set "DUPFILE=mlu_dup.tmp"
set "WORKFILE=mlu_work.tmp"

if not exist "%LOGFILE%" (
    echo Log file not found: %LOGFILE%
    exit /b 1
)

del "%IDFILE%" 2>nul
del "%DUPFILE%" 2>nul
del "%WORKFILE%" 2>nul

echo Extracting MLU codes...

for /f "delims=" %%L in ('findstr /i "Calling:" "%LOGFILE%"') do (
    for %%A in (%%L) do set "last=%%A"
    if defined last echo !last!>>"%WORKFILE%"
)

if not exist "%WORKFILE%" (
    echo No categories found.
    exit /b 0
)

del "%DUPFILE%" 2>nul
del "%IDFILE%.tmp" 2>nul

set "prev="
set /a count=0
set /a total=0

for /f "usebackq delims=" %%A in (`sort "%WORKFILE%"`) do (
    if "%%A"=="!prev!" (
        set /a count+=1
    ) else (
        if defined prev (
            >>"%IDFILE%.tmp" echo !prev! : !count!
            set /a total+=1
            if !count! GTR 1 (
                >>"%DUPFILE%" echo !prev! : !count!
            )
        )
        set "prev=%%A"
        set /a count=1
    )
)

REM Handle last entry
if defined prev (
    >>"%IDFILE%.tmp" echo !prev! : !count!
    set /a total+=1
    if !count! GTR 1 (
        >>"%DUPFILE%" echo !prev! : !count!
    )
)

(
    type "%IDFILE%.tmp"
    echo.
    echo ======== Categories repeated ========
    if exist "%DUPFILE%" (
        type "%DUPFILE%"
    ) else (
        echo No repeated categories found.
    )
    echo.
    echo ========= Categories analyzed ========
    echo %total%
) > "%IDFILE%"

del "%WORKFILE%" 2>nul
del "%IDFILE%.tmp" 2>nul
del "%DUPFILE%" 2>nul

echo Done. Output saved to %IDFILE%.
endlocal
