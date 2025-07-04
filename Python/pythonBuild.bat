@echo off
setlocal enabledelayedexpansion

:: Folder skryptu
set "SCRIPT_DIR=%~dp0"

:: Wczytaj komendę z pliku bez rozszerzenia o nazwie 'komenda'
set "CMD_FILE=%SCRIPT_DIR%pythonBuild"
if not exist "%CMD_FILE%" (
    echo Plik z komenda '%CMD_FILE%' nie istnieje!
    pause
    exit /b
)

set /p CMD_LINE=<"%CMD_FILE%"

if "%CMD_LINE%"=="" (
    echo Plik komenda jest pusty!
    pause
    exit /b
)

:: Wybór pliku .py przez PowerShell
for /f "usebackq delims=" %%F in (`powershell -command "Add-Type -AssemblyName System.Windows.Forms; $ofd = New-Object System.Windows.Forms.OpenFileDialog; $ofd.Filter = 'Python Files (*.py)|*.py'; if($ofd.ShowDialog() -eq 'OK') { Write-Output $ofd.FileName }"`) do set "PYFILE=%%F"

if "%PYFILE%"=="" (
    echo Nie wybrano pliku. Koniec.
    pause
    exit /b
)

echo Wybrano plik: %PYFILE%
echo Uruchamiam komendę: %CMD_LINE%

:: Zamień w CMD_LINE znaki %FILE% na wybraną ścieżkę pliku
set "CMD_LINE=!CMD_LINE:%%FILE%%=%PYFILE%!"

:: Uruchom polecenie
cmd /c "!CMD_LINE! %PYFILE%"


pause
