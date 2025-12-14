@echo off
REM build.bat - Compila main.tex mettendo tutti i file di lavoro in build\

setlocal enabledelayedexpansion

REM Nome del file tex principale (modifica se serve)
set "TEXFILE=main.tex"
REM Estrae il basename senza estensione
for %%F in ("%TEXFILE%") do set "BASENAME=%%~nF"
set "OUTDIR=build"

REM crea cartella di output se non esiste
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

echo Compiling %TEXFILE% -> %OUTDIR%\%BASENAME%.pdf

REM Prima passata pdflatex (genera .bcf se usi biblatex)
pdflatex -interaction=nonstopmode -synctex=1 -output-directory="%OUTDIR%" "%TEXFILE%"
if errorlevel 1 echo pdflatex first pass returned nonzero code.

REM Se esiste .bcf nella cartella di output, usa biber su build\basename
if exist "%OUTDIR%\%BASENAME%.bcf" (
    echo Running biber on %OUTDIR%\%BASENAME%
    biber "%OUTDIR%\%BASENAME%"
) else (
    echo No .bcf found, skipping biber.
)

REM Seconda/terza passata per riferimenti incrociati
pdflatex -interaction=nonstopmode -synctex=1 -output-directory="%OUTDIR%" "%TEXFILE%"
pdflatex -interaction=nonstopmode -synctex=1 -output-directory="%OUTDIR%" "%TEXFILE%"

REM Copia PDF in root per comodita' (sovrascrive se esiste)
copy /Y "%OUTDIR%\%BASENAME%.pdf" "%~dp0%BASENAME%.pdf" >nul

echo Build finished. PDF: %~dp0%BASENAME%.pdf
endlocal
