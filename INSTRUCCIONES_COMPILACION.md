# 🚀 Instrucciones de Compilación - GanddOperativos

Este documento explica cómo compilar el proyecto GanddOperativos (TimeSlice) y generar un instalador ejecutable.

## 📋 Requisitos Previos

### Software Necesario:
1. **Python 3.8+** - [Descargar desde python.org](https://python.org)
2. **Inno Setup 6** - [Descargar desde jrsoftware.org](https://jrsoftware.org/isinfo.php)
3. **Git** (opcional) - Para clonar el repositorio

### Dependencias de Python:
- customtkinter >= 5.2.0
- matplotlib >= 3.5.0
- pandas >= 1.3.0
- openpyxl >= 3.0.0
- pyinstaller >= 5.0.0

## 🛠️ Métodos de Compilación

### Método 1: Script Automático (Recomendado)

#### Opción A: Usando el archivo batch (Windows)
```bash
# Simplemente ejecuta:
build.bat
```

#### Opción B: Usando Python directamente
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar script de compilación
python build_installer.py
```

### Método 2: Compilación Manual

#### Paso 1: Instalar dependencias
```bash
pip install -r requirements.txt
```

#### Paso 2: Compilar ejecutable
```bash
pyinstaller --clean --noconfirm TimeSlice.spec
```

#### Paso 3: Compilar instalador
```bash
# Buscar la ruta de Inno Setup (ejemplo):
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss
```

## 📁 Estructura de Archivos Generados

Después de la compilación exitosa, encontrarás:

```
GanddOperativos/
├── dist/
│   └── TimeSlice.exe          # Ejecutable principal
├── build/                     # Archivos temporales de PyInstaller
├── Instalador_Final/
│   └── TimeSlice_Instalador.exe  # Instalador final
└── requirements.txt           # Dependencias del proyecto
```

## 🔧 Configuración del Proyecto

### Archivos de Configuración:

1. **`TimeSlice.spec`** - Configuración de PyInstaller
   - Define qué archivos incluir en el ejecutable
   - Configura las dependencias ocultas
   - Establece el icono y nombre del ejecutable

2. **`instalador.iss`** - Script de Inno Setup
   - Configura el instalador de Windows
   - Define la información de la aplicación
   - Establece los archivos a incluir en la instalación

3. **`requirements.txt`** - Dependencias de Python
   - Lista todas las librerías necesarias
   - Especifica versiones mínimas

## 🐛 Solución de Problemas

### Error: "Python no encontrado"
- Asegúrate de que Python esté instalado y en el PATH
- Reinicia la terminal después de instalar Python

### Error: "Inno Setup no encontrado"
- Instala Inno Setup desde el sitio oficial
- El script busca automáticamente en las ubicaciones comunes

### Error: "Módulo no encontrado"
- Ejecuta: `pip install -r requirements.txt`
- Verifica que todas las dependencias estén instaladas

### Error: "Archivo faltante"
- Asegúrate de que todos los archivos del proyecto estén presentes:
  - `LICENSE`
  - `README.md`
  - `INFO.txt`
  - `AFTER_INSTALL.txt`
  - `icon.ico`
  - `sistema_completo.txt`
  - `utils/input_historial.json`

### El ejecutable no funciona
- Verifica que todas las dependencias estén incluidas en el .spec
- Revisa los logs de PyInstaller para errores específicos
- Prueba ejecutar el programa desde la terminal para ver errores

## 📊 Información del Instalador

El instalador generado incluye:
- ✅ Ejecutable principal (TimeSlice.exe)
- ✅ Archivos de documentación
- ✅ Datos del sistema
- ✅ Iconos del programa
- ✅ Desinstalador automático
- ✅ Creación de accesos directos
- ✅ Configuración de permisos

## 🎯 Personalización

### Cambiar el nombre de la aplicación:
1. Edita `instalador.iss` - línea 4: `#define MyAppName`
2. Edita `TimeSlice.spec` - línea 25: `name='TimeSlice'`

### Cambiar la versión:
1. Edita `instalador.iss` - línea 5: `#define MyAppVersion`

### Agregar archivos adicionales:
1. Edita `TimeSlice.spec` - sección `datas`
2. Edita `instalador.iss` - sección `[Files]`

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs de compilación
2. Verifica que todos los requisitos estén cumplidos
3. Consulta la documentación de PyInstaller e Inno Setup
4. Revisa los archivos de configuración

---

**¡Listo!** 🎉 Con estos pasos deberías poder compilar exitosamente tu aplicación y generar un instalador profesional.
