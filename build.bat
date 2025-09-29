@echo off
chcp 65001 >nul
echo ========================================
echo   Compilador de GanddOperativos
echo ========================================
echo.

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado o no está en el PATH
    echo Por favor instala Python desde: https://python.org
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo.

REM Ejecutar el script de compilación
echo 🚀 Iniciando proceso de compilación...
python build_installer.py

REM Verificar el resultado
if errorlevel 1 (
    echo.
    echo ❌ La compilación falló
    pause
    exit /b 1
) else (
    echo.
    echo ✅ Compilación completada exitosamente
    echo.
    echo 📁 Archivos generados:
    echo    - Ejecutable: dist\TimeSlice.exe
    echo    - Instalador: Instalador_Final\TimeSlice_Instalador.exe
    echo.
    echo ¿Deseas abrir la carpeta del instalador? (S/N)
    set /p choice=
    if /i "%choice%"=="S" (
        explorer Instalador_Final
    )
)

pause
