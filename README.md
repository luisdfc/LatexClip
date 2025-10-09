# LaTeX-to-Image Converter

LaTeX Clip is a desktop LaTeX-to-image converter designed to give you beautiful, shareable math in
seconds. Quickly paste equations from ChatGPT, Gemini, Claude, academic papers, or other sources and
turn them into high-resolution images for Word, OneNote, or PowerPoint, Office-ready MathML/HTML
markup, or simplified text for documentation. The project is optimized for Windows but runs
anywhere Python does, making it a reliable companion for students, researchers, technical writers,
and anyone who needs accurate formula rendering without the overhead of a full LaTeX installation.

## Key features at a glance

* **Copy-and-render from AI assistants:** Paste raw LaTeX that you copied from ChatGPT or other LLMs
  and instantly preview the output before adding it to Word, OneNote, Google Docs, or Notion.
* **Multiple export formats:** Save as images for slides, copy Office-compatible MathML markup, or
  grab a plain-text description that reads well in documentation and wikis.
* **Fast local workflow:** Launch a lightweight Tkinter window instead of juggling online LaTeX
  compilers or complex PDF pipelines.
* **Upgradable rendering:** Toggle a full LaTeX toolchain when you need publication-grade output
  with packages beyond what the built-in renderer covers.
* **Open-source and scriptable:** Clone or fork the repository to automate math-image generation in
  your own tools or pipelines.

![Screenshot 1](Screenshots/1.png)
![Screenshot 2](Screenshots/2.png)

## Quick Start (No Programming Knowledge Needed)

Follow these steps to get the tool running on your Windows computer.

### Step 1: Install Python

If you don't have Python, you need to install it first.

1.  Go to the official Python website: [python.org/downloads/windows](https://www.python.org/downloads/windows/)
2.  Download the latest stable version (e.g., Python 3.12).
3.  Run the installer. **Important:** On the first screen of the installer, make sure to check the box that says **"Add Python to PATH"**. This will make the next steps much easier.

### Step 2: Download This Tool

1.  Click the green **"Code"** button at the top of this page.
2.  Select **"Download ZIP"**.
3.  Extract the ZIP file to a folder you can easily find, for example, `C:\Users\YourUser\Documents\LatexTool`.

### Step 3: Install Required Libraries

1.  Open the **Command Prompt**. You can find it by searching for "cmd" in the Start Menu.
2.  Navigate to the folder where you extracted the tool. For example:
    ```cmd
    cd C:\Users\YourUser\Documents\LatexTool
    ```
3.  Install the necessary Python libraries listed in `requirements.txt`:
    ```cmd
    pip install -r requirements.txt
    ```
    *On non-Windows systems the `pywin32` dependency from the requirements file
    is optional and will be skipped automatically. The `latex2mathml` library
    enables the "Copy for Word/OneNote" button; if you do not need MathML
    clipboard support you may uninstall it later with `pip uninstall
    latex2mathml`.*

### Step 4: Run the Application

Now, you can run the tool. Simply double-click the `latexclip.py` file, or run it from the Command Prompt:

```cmd
python latexclip.py
```

The application window will open, and you can start converting your LaTeX. Use the **Copy for Word/OneNote** button to place MathML/HTML markup on the clipboard that pastes directly into Office equation editors. A live plain-text preview shows you what the simplified version will look like for documentation.

---

## Tips for Complex Formulas

The converter now understands alignment environments (`align`, `align*`, `gather`), structured pieces (`cases`), and matrix-style layouts when producing plain text. A few quick guidelines will help you get the best results:

* Use LaTeX text macros such as `\text{...}` or `\mathrm{...}` around multi-word labels so that both the Office-friendly output and the plain-text preview preserve your spacing.
* When building piecewise expressions, keep the standard `value , & condition` layout—LaTeX Clip rewrites this to human-friendly prose (for example `f(x) = (x^2 if x > 0; 0 otherwise)`).
* For matrices or arrays, feel free to include `\hline` separators. They are ignored in the plain-text rendering while the MathML/HTML clipboard still carries the full structure for Office.
* The preview collapses repeated whitespace automatically. If you need deliberate spacing in exported text, prefer explicit LaTeX spacing commands (`\,`, `\;`, `\quad`) or wrap the content in `\text{ }`.

---

## Optional Upgrades

### For Full, High-Quality LaTeX Rendering

The default mode uses a built-in renderer that is fast but may not support all complex LaTeX packages. For publication-quality rendering, you can install a full LaTeX distribution.

**1. Install a LaTeX Distribution**

You only need one of the following:

*   **MiKTeX (Recommended for Windows):** It's free and automatically downloads packages as you need them, saving space.
    *   [**Download MiKTeX**](https://miktex.org/download)

*   **TeX Live (Alternative):** A larger, more comprehensive distribution.
    *   [**Download TeX Live**](https://www.tug.org/texlive/acquire-netinstall.html)

**2. Install Ghostscript**

This is a required companion for the LaTeX distribution.

*   [**Download Ghostscript**](https://ghostscript.com/releases/gsdnld.html)
    *   Make sure the installer adds Ghostscript to your system's PATH (it usually does this by default).

Once installed, simply check the **"Use full LaTeX"** box in the app to enable high-quality rendering.

### Create a Standalone `.exe` Application

If you want to run this tool without needing to open Command Prompt, you can bundle it into a single `.exe` file.

**1. Install PyInstaller**

Open Command Prompt and run:

```cmd
pip install pyinstaller
```

**2. Create the Executable**

In the Command Prompt, navigate to the tool's directory and run the following command:

Use the bundled spec file so PyInstaller collects the themed assets and
matplotlib backends automatically:

```cmd
pyinstaller latexclip.spec
or
python -m PyInstaller --noconsole --onefile "latexclip.py"
```

After a few moments, you will find a `dist` folder. Inside, `latexclip.exe` is your standalone application. You can move this file anywhere on your computer or create a shortcut to it on your desktop.
