@echo off
setlocal enabledelayedexpansion

:: Résolution cible
set WIDTH=608
set HEIGHT=1080

:: Parcourir tous les fichiers MP4 du dossier
for %%F in (*.mp4) do (
    echo Traitement de %%F ...
    ffmpeg -i "%%F" -vf scale=%WIDTH%:%HEIGHT% -c:a copy "resized_%WIDTH%_%%~nF.mp4"
)

echo.
echo Terminé !
pause
