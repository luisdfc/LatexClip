# Conversor de LaTeX a Imagen

LaTeX Clip es un conversor de LaTeX a imagen para escritorio que te permite obtener ecuaciones bien presentadas en segundos. Copia fórmulas desde ChatGPT, Gemini, Claude, artículos académicos u otras fuentes y transpórtalas como imágenes de alta resolución para Word, OneNote o PowerPoint, marcado MathML/HTML compatible con Microsoft Office o texto simplificado para documentación técnica. El proyecto está optimizado para Windows, pero funciona en cualquier sistema con Python, por lo que es ideal para estudiantes, docentes, investigadores, creadores de contenido técnico y cualquier persona que necesite renderizados fiables sin instalar una distribución completa de LaTeX.

## Características destacadas

* **Renderiza lo que copias de la IA:** Pega expresiones que vengan de ChatGPT u otros asistentes y revisa la vista previa antes de incorporarlas a Word, PowerPoint, OneNote, Google Docs o Notion.
* **Distintos formatos de salida:** Guarda como imagen para presentaciones, copia MathML listo para Office o utiliza la vista en texto plano para manuales y wikis.
* **Flujo de trabajo local y rápido:** Abre una ventana ligera de Tkinter en vez de depender de compiladores LaTeX en la nube o flujos complejos de PDF.
* **Renderizado ampliable:** Activa una cadena LaTeX completa cuando necesites compatibilidad con paquetes avanzados y resultados de calidad editorial.
* **Código abierto y automatizable:** Clona o bifurca el repositorio para integrarlo en tus propios scripts y pipelines de generación de contenidos matemáticos.

## Guía rápida (sin conocimientos de programación)

Sigue estos pasos para ejecutar la aplicación en Windows.

### Paso 1: Instala Python

1. Visita [python.org/downloads/windows](https://www.python.org/downloads/windows/).
2. Descarga la versión estable más reciente (por ejemplo, Python 3.12).
3. Ejecuta el instalador y marca la casilla **"Add Python to PATH"** en la primera pantalla.

### Paso 2: Descarga esta herramienta

1. Haz clic en el botón verde **"Code"** de la parte superior de GitHub.
2. Selecciona **"Download ZIP"**.
3. Extrae el archivo ZIP en una carpeta fácil de encontrar, por ejemplo `C:\\Users\\TuUsuario\\Documents\\LatexTool`.

### Paso 3: Instala las dependencias

1. Abre el **Símbolo del sistema** (busca "cmd" en el menú Inicio).
2. Navega hasta la carpeta donde extrajiste el proyecto:
   ```cmd
   cd C:\\Users\\TuUsuario\\Documents\\LatexTool
   ```
3. Instala las librerías necesarias listadas en `requirements.txt`:
   ```cmd
   pip install -r requirements.txt
   ```
   *En sistemas que no sean Windows, la dependencia `pywin32` es opcional y se omitirá automáticamente. La biblioteca `latex2mathml` habilita el botón "Copy for Word/OneNote"; si no necesitas copiar MathML al portapapeles puedes desinstalarla después con `pip uninstall latex2mathml`.*

### Paso 4: Ejecuta la aplicación

Haz doble clic sobre `latexclip.py` o ejecútalo desde la terminal:

```cmd
python latexclip.py
```

La ventana principal se abrirá y podrás comenzar a convertir tu LaTeX. Usa el botón **Copy for Word/OneNote** para copiar MathML/HTML compatible con los editores de ecuaciones de Office. La vista previa en texto plano muestra cómo quedará una versión simplificada para tu documentación.

---

## Consejos para fórmulas complejas

* Utiliza macros como `\text{...}` o `\mathrm{...}` alrededor de etiquetas con varias palabras; así conservas el espaciado tanto en Office como en la vista previa.
* Para expresiones por partes, mantén el formato estándar `valor , & condición`. LaTeX Clip lo convertirá en texto legible (por ejemplo, `f(x) = (x^2 si x > 0; 0 en otro caso)`).
* En matrices o arreglos puedes incluir separadores `\hline`. Se ignorarán en el texto plano, pero el MathML/HTML conservará la estructura.
* La vista previa reduce espacios repetidos automáticamente. Si necesitas espaciado explícito, usa comandos LaTeX como `\,`, `\;`, `\quad` o encapsula el contenido con `\text{ }`.

---

## Mejoras opcionales

### Renderizado LaTeX de alta calidad

El modo por defecto utiliza un motor integrado rápido, pero puede que no soporte todos los paquetes avanzados. Instala una distribución completa de LaTeX para resultados de calidad editorial.

1. **Instala una distribución LaTeX:**
   * **MiKTeX (recomendado en Windows):** descarga en [miktex.org/download](https://miktex.org/download).
   * **TeX Live (alternativa multiplataforma):** descarga en [tug.org/texlive](https://www.tug.org/texlive/acquire-netinstall.html).
2. **Instala Ghostscript:** disponible en [ghostscript.com](https://ghostscript.com/releases/gsdnld.html). El instalador suele añadirlo automáticamente al PATH.
3. Activa la casilla **"Use full LaTeX"** dentro de la aplicación para usar la nueva cadena de renderizado.

### Crear un ejecutable `.exe`

Si prefieres abrir la herramienta sin usar la terminal, puedes generar un ejecutable independiente con PyInstaller.

1. Instala PyInstaller:
   ```cmd
   pip install pyinstaller
   ```
2. Crea el ejecutable desde la carpeta del proyecto:
   ```cmd
   pyinstaller latexclip.spec
   ```
   o bien:
   ```cmd
   python -m PyInstaller --noconsole --onefile "latexclip.py"
   ```
3. El ejecutable `latexclip.exe` se ubicará en la carpeta `dist`. Puedes moverlo o crear un acceso directo en tu escritorio.

---

¿Listo para compartir tus notas? Copia tus fórmulas desde ChatGPT, pega en LaTeX Clip y obtén imágenes nítidas o marcado listo para tus documentos profesionales.
