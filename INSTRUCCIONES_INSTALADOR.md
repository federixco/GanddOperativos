# 🚀 Instalador Wizard para GanddOperativos

## ¿Qué es esto?

Este sistema crea un instalador profesional para tu programa GanddOperativos que funciona exactamente como los instaladores de programas comerciales (como Photoshop, Office, etc.). Los usuarios solo necesitan hacer doble clic y seguir el wizard: **Siguiente → Siguiente → Finalizar**.

## 📋 ¿Qué necesitas hacer?

### Paso 1: Instalar Inno Setup
1. Ve a: https://jrsoftware.org/isinfo.php
2. Descarga la versión más reciente de Inno Setup
3. Instálalo con las opciones por defecto
4. ¡Listo!

### Paso 2: Crear el instalador
Ejecuta este comando en tu terminal:
```bash
python crear_instalador_final.py
```

¡Eso es todo! El script hace todo automáticamente.

## 🎯 ¿Qué hace el script?

1. **Instala PyInstaller** (si no lo tienes)
2. **Crea el ejecutable** de tu programa
3. **Verifica todos los archivos** necesarios
4. **Genera el instalador wizard** usando Inno Setup
5. **¡Listo para distribuir!**

## 📁 Archivos que se crean

```
Instalador_Final/
└── GanddOperativos_Instalador.exe  ← Este es tu instalador wizard
```

## 🎮 Experiencia del usuario final

### Para el usuario que quiere instalar tu programa:

1. **Descarga** el archivo `GanddOperativos_Instalador.exe`
2. **Hace doble clic** en el archivo
3. **Aparece el wizard** de instalación
4. **Hace clic en "Siguiente"** varias veces
5. **Hace clic en "Finalizar"**
6. **¡El programa está instalado!**

### Lo que ve el usuario durante la instalación:

- ✅ Pantalla de bienvenida con información del programa
- ✅ Selección de carpeta de instalación (por defecto: Program Files)
- ✅ Opción de crear acceso directo en escritorio
- ✅ Barra de progreso durante la instalación
- ✅ Opción de ejecutar el programa al finalizar
- ✅ Mensaje de instalación completada

## 🎯 Características del instalador

- **Wizard profesional** con pantallas de bienvenida
- **Instalación en Program Files** (como cualquier programa profesional)
- **Acceso directo en el menú inicio** automáticamente
- **Opción de acceso directo en escritorio** (el usuario puede elegir)
- **Desinstalación completa** desde "Agregar o quitar programas"
- **No requiere Python** en la PC destino
- **Funciona en Windows 7, 8, 10, 11**

## 🔧 Personalización (opcional)

Si quieres cambiar algo del instalador, edita el archivo `instalador.iss`:

### Cambiar el nombre del programa:
```ini
#define MyAppName "Tu Nuevo Nombre"
```

### Cambiar la versión:
```ini
#define MyAppVersion "2.0"
```

### Cambiar el autor:
```ini
#define MyAppPublisher "Tu Nombre"
```

## 🚀 Distribución

### Opción 1: Compartir directamente
- Copia el archivo `GanddOperativos_Instalador.exe`
- Envíalo por email, WhatsApp, etc.
- Los usuarios lo descargan y ejecutan

### Opción 2: GitHub Releases
1. Ve a tu repositorio en GitHub
2. Clic en "Releases" → "Create a new release"
3. Sube el archivo `GanddOperativos_Instalador.exe`
4. Los usuarios descargan desde ahí

### Opción 3: Sitio web
- Sube el archivo a tu sitio web
- Los usuarios descargan desde ahí

## 🎉 ¡Resultado final!

Después de ejecutar el script, tendrás:

- ✅ Un archivo `.exe` que es un instalador profesional
- ✅ Los usuarios pueden instalarlo como cualquier programa comercial
- ✅ No necesitan conocimientos técnicos
- ✅ Solo hacen clic en "Siguiente" hasta el final
- ✅ El programa queda instalado y listo para usar

## 🆘 Si algo sale mal

### Error: "Inno Setup no encontrado"
- Instala Inno Setup desde: https://jrsoftware.org/isinfo.php
- Reinicia tu terminal
- Ejecuta el script nuevamente

### Error: "No se encontró main.py"
- Asegúrate de ejecutar el script desde la carpeta del proyecto
- Verifica que `main.py` existe en la carpeta

### Error: "PyInstaller falló"
- Ejecuta: `pip install pyinstaller`
- Ejecuta el script nuevamente

### El instalador no funciona en otra PC
- Verifica que la PC tiene Windows 7 o superior
- Ejecuta el instalador como administrador
- Verifica que el antivirus no lo está bloqueando

## 🎊 ¡Listo!

Con este sistema, tu programa GanddOperativos se puede instalar en cualquier PC de Windows de manera profesional, igual que cualquier programa comercial. Los usuarios solo necesitan hacer clic en "Siguiente" hasta el final y ¡ya tienen tu programa instalado y funcionando!
