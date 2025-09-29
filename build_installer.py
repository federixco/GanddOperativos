#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de compilación automática para GanddOperativos
Genera el ejecutable y compila el instalador con Inno Setup
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

class BuildInstaller:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.installer_dir = self.project_root / "Instalador_Final"
        
        # Configuración del proyecto
        self.app_name = "TimeSlice"
        self.app_version = "1.0"
        self.spec_file = "TimeSlice.spec"
        self.iss_file = "instalador.iss"
        
    def print_step(self, message):
        """Imprime un paso del proceso con formato"""
        print(f"\n{'='*60}")
        print(f"🔧 {message}")
        print(f"{'='*60}")
    
    def check_dependencies(self):
        """Verifica que las dependencias estén instaladas"""
        self.print_step("Verificando dependencias")
        
        required_packages = [
            'pyinstaller',
            'customtkinter',
            'matplotlib',
            'pandas',
            'openpyxl'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"✅ {package} - OK")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} - FALTANTE")
        
        if missing_packages:
            print(f"\n⚠️  Paquetes faltantes: {', '.join(missing_packages)}")
            print("Instalando paquetes faltantes...")
            for package in missing_packages:
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
                print(f"✅ {package} instalado")
        
        # Verificar Inno Setup
        inno_paths = [
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            r"C:\Program Files\Inno Setup 6\ISCC.exe",
            r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
            r"C:\Program Files\Inno Setup 5\ISCC.exe"
        ]
        
        self.inno_compiler = None
        for path in inno_paths:
            if os.path.exists(path):
                self.inno_compiler = path
                print(f"✅ Inno Setup encontrado: {path}")
                break
        
        if not self.inno_compiler:
            print("❌ Inno Setup no encontrado. Por favor instálalo desde:")
            print("   https://jrsoftware.org/isinfo.php")
            return False
        
        return True
    
    def clean_build_dirs(self):
        """Limpia directorios de compilación anteriores"""
        self.print_step("Limpiando directorios de compilación")
        
        dirs_to_clean = [self.dist_dir, self.build_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"🗑️  Eliminado: {dir_path}")
        
        # Crear directorios limpios
        self.dist_dir.mkdir(exist_ok=True)
        self.build_dir.mkdir(exist_ok=True)
        self.installer_dir.mkdir(exist_ok=True)
    
    def update_spec_file(self):
        """Actualiza el archivo .spec con todas las dependencias"""
        self.print_step("Actualizando archivo .spec")
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('utils/input_historial.json', 'utils'),
        ('sistema_completo.txt', '.'),
        ('icon.ico', '.'),
        ('LICENSE', '.'),
        ('README.md', '.'),
        ('INFO.txt', '.'),
        ('AFTER_INSTALL.txt', '.')
    ],
    hiddenimports=[
        'customtkinter',
        'matplotlib.backends.backend_tkagg',
        'pandas',
        'openpyxl',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'matplotlib.pyplot',
        'matplotlib.figure',
        'matplotlib.backends.backend_tkagg',
        'json',
        'datetime',
        'pathlib'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='{self.app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
'''
        
        with open(self.spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"✅ Archivo {self.spec_file} actualizado")
    
    def build_executable(self):
        """Compila el ejecutable con PyInstaller"""
        self.print_step("Compilando ejecutable con PyInstaller")
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            self.spec_file
        ]
        
        print(f"Ejecutando: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Error en la compilación:")
            print(result.stderr)
            return False
        
        print("✅ Ejecutable compilado exitosamente")
        
        # Verificar que el ejecutable existe
        exe_path = self.dist_dir / f"{self.app_name}.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📦 Ejecutable generado: {exe_path} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"❌ No se encontró el ejecutable: {exe_path}")
            return False
    
    def prepare_installer_files(self):
        """Prepara archivos adicionales para el instalador"""
        self.print_step("Preparando archivos para el instalador")
        
        # Verificar archivos requeridos
        required_files = [
            "LICENSE",
            "README.md", 
            "INFO.txt",
            "AFTER_INSTALL.txt",
            "icon.ico",
            "sistema_completo.txt",
            "utils/input_historial.json"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                print(f"❌ Archivo faltante: {file_path}")
            else:
                print(f"✅ {file_path}")
        
        if missing_files:
            print(f"\n⚠️  Archivos faltantes: {', '.join(missing_files)}")
            return False
        
        return True
    
    def build_installer(self):
        """Compila el instalador con Inno Setup"""
        self.print_step("Compilando instalador con Inno Setup")
        
        if not self.inno_compiler:
            print("❌ Compilador de Inno Setup no disponible")
            return False
        
        cmd = [self.inno_compiler, str(self.project_root / self.iss_file)]
        
        print(f"Ejecutando: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Error en la compilación del instalador:")
            print(result.stderr)
            return False
        
        print("✅ Instalador compilado exitosamente")
        
        # Verificar que el instalador existe
        installer_path = self.installer_dir / f"{self.app_name}_Instalador.exe"
        if installer_path.exists():
            size_mb = installer_path.stat().st_size / (1024 * 1024)
            print(f"📦 Instalador generado: {installer_path} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"❌ No se encontró el instalador: {installer_path}")
            return False
    
    def create_requirements_file(self):
        """Crea archivo requirements.txt"""
        self.print_step("Creando archivo requirements.txt")
        
        requirements = [
            "customtkinter>=5.2.0",
            "matplotlib>=3.5.0",
            "pandas>=1.3.0",
            "openpyxl>=3.0.0",
            "pyinstaller>=5.0.0"
        ]
        
        with open("requirements.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(requirements))
        
        print("✅ requirements.txt creado")
    
    def run_build(self):
        """Ejecuta todo el proceso de compilación"""
        print("🚀 Iniciando proceso de compilación de GanddOperativos")
        print(f"📁 Directorio del proyecto: {self.project_root}")
        
        try:
            # Paso 1: Verificar dependencias
            if not self.check_dependencies():
                return False
            
            # Paso 2: Crear requirements.txt
            self.create_requirements_file()
            
            # Paso 3: Limpiar directorios
            self.clean_build_dirs()
            
            # Paso 4: Actualizar archivo .spec
            self.update_spec_file()
            
            # Paso 5: Compilar ejecutable
            if not self.build_executable():
                return False
            
            # Paso 6: Preparar archivos del instalador
            if not self.prepare_installer_files():
                return False
            
            # Paso 7: Compilar instalador
            if not self.build_installer():
                return False
            
            # Éxito
            self.print_step("🎉 COMPILACIÓN COMPLETADA EXITOSAMENTE")
            print(f"📦 Ejecutable: {self.dist_dir / f'{self.app_name}.exe'}")
            print(f"📦 Instalador: {self.installer_dir / f'{self.app_name}_Instalador.exe'}")
            print("\n✨ El instalador está listo para distribuir")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error durante la compilación: {e}")
            return False

def main():
    """Función principal"""
    builder = BuildInstaller()
    success = builder.run_build()
    
    if success:
        print("\n🎯 Proceso completado exitosamente")
        sys.exit(0)
    else:
        print("\n💥 Proceso falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
