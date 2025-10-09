
import io
import os
import re
from dataclasses import dataclass
from typing import Optional
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont

try:
    from PIL import Image, ImageTk
    # Disable decompression bomb guard explicitly
    Image.MAX_IMAGE_PIXELS = None
except Exception as e:
    raise SystemExit("Missing dependency: Pillow. Install with: pip install pillow") from e

HAVE_PYWIN32 = True
try:
    import win32clipboard
    import win32con
except Exception:
    HAVE_PYWIN32 = False

try:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib import rcParams
except Exception as e:
    raise SystemExit("Missing dependency: matplotlib. Install with: pip install matplotlib") from e

try:
    from latex2mathml.converter import convert as latex_to_mathml
except Exception:
    latex_to_mathml = None

# -----------------------------
# Helpers
# -----------------------------
TEXT_MACROS = (
    "text",
    "textbf",
    "textit",
    "textrm",
    "textsf",
    "texttt",
    "operatorname",
    "mathrm",
    "mathbf",
    "mathit",
    "mathsf",
    "mathtt",
)


def latex_to_plaintext(s: str) -> str:
    out = s
    out = out.replace("\r\n", "\n").replace("\r", "\n")
    out = out.replace(r"\{", "__LACE_BRACE__").replace(r"\}", "__RACE_BRACE__")
    escaped_amp_placeholder = "__LATEXCLIP_ESC_AMP__"
    out = out.replace(r"\&", escaped_amp_placeholder)
    out = re.sub(r"\$\$(.*?)\$\$", r"\1", out, flags=re.DOTALL)
    out = re.sub(r"\$(.*?)\$", r"\1", out, flags=re.DOTALL)

    def unwrap_text(match: re.Match[str]) -> str:
        inner = match.group(1)
        inner = inner.replace(r"\ ", " ")
        inner = re.sub(r"\s+", " ", inner).strip()
        inner = inner.replace(escaped_amp_placeholder, "&")
        return inner

    text_macro_pattern = r"\\(?:" + "|".join(TEXT_MACROS) + r")\*?\{([^}]*)\}"
    out = re.sub(text_macro_pattern, unwrap_text, out)

    space_cmds = {
        r"\,": " ",
        r"\;": " ",
        r"\:": " ",
        r"\!": "",
        r"\quad": " ",
        r"\qquad": " ",
        r"~": " ",
    }
    for cmd, replacement in space_cmds.items():
        out = out.replace(cmd, replacement)

    structured_envs = {
        "matrix": "matrix",
        "pmatrix": "matrix",
        "bmatrix": "matrix",
        "Bmatrix": "matrix",
        "vmatrix": "matrix",
        "Vmatrix": "matrix",
        "smallmatrix": "matrix",
        "array": "matrix",
        "cases": "cases",
        "aligned": "aligned",
        "align": "aligned",
        "align*": "aligned",
        "alignat": "aligned",
        "alignat*": "aligned",
        "alignedat": "aligned",
        "gather": "aligned",
        "gather*": "aligned",
        "split": "aligned",
        "multline": "aligned",
        "multline*": "aligned",
    }
    env_pattern = "|".join(re.escape(env) for env in structured_envs)
    matrix_pattern = re.compile(
        r"\\begin\{(?P<env>" + env_pattern + r")\}"
        r"(?P<colspec>\{[^}]*\})?"
        r"(?P<body>.*?)"
        r"\\end\{\1\}",
        flags=re.DOTALL,
    )
    matrix_delims = {
        "matrix": ("[", "]"),
        "pmatrix": ("(", ")"),
        "bmatrix": ("[", "]"),
        "Bmatrix": ("{", "}"),
        "vmatrix": ("|", "|"),
        "Vmatrix": ("‖", "‖"),
        "smallmatrix": ("[", "]"),
        "cases": ("{", "}"),
        "array": ("[", "]"),
    }

    def format_matrix(match: re.Match[str]) -> str:
        env = match.group("env")
        body = match.group("body") or ""
        env_kind = structured_envs.get(env, "matrix")
        body = body.replace(r"\hline", "")
        rows = re.split(r"(?<!\\)\\\\", body)
        formatted_rows = []
        for row in rows:
            row = row.strip()
            if not row:
                continue
            cols = [c.strip() for c in re.split(r"(?<!\\)&", row)]
            cols = [c.replace(escaped_amp_placeholder, "&") for c in cols if c]
            if env_kind == "aligned":
                formatted_rows.append(" ".join(cols))
                continue
            if env_kind == "cases":
                value = cols[0] if cols else ""
                if value.endswith((",", ";")):
                    value = value[:-1].rstrip()
                condition = " ".join(cols[1:]).lstrip(",; ") if len(cols) > 1 else ""
                if condition:
                    if condition.lower().startswith("otherwise"):
                        formatted_rows.append(f"{value} {condition}")
                    else:
                        formatted_rows.append(f"{value} if {condition}")
                else:
                    formatted_rows.append(value)
                continue
            formatted_rows.append(", ".join(cols))
        if env_kind == "aligned":
            return "; ".join(formatted_rows)
        if env_kind == "cases":
            inner = "; ".join(formatted_rows)
            left, right = ("{", "}")
            return f"{left}{inner}{right}"
        left, right = matrix_delims.get(env.rstrip("*"), ("[", "]"))
        inner = "; ".join(formatted_rows)
        return f"{left}{inner}{right}"

    while True:
        match = matrix_pattern.search(out)
        if not match:
            break
        out = out[: match.start()] + format_matrix(match) + out[match.end():]

    out = re.sub(r"(?<!\\)\\\\", "; ", out)
    out = re.sub(r"\s*&\s*", " & ", out)

    out = re.sub(r"\\(sin|cos|tan|log|ln|det|dim|lim|exp|deg|sec|csc|cot)\b", r"\1", out)

    replacements = {
        r"\\cdot": "·",
        r"\\times": "×",
        r"\\pm": "±",
        r"\\mp": "∓",
        r"\\leq": "≤",
        r"\\geq": "≥",
        r"\\neq": "≠",
        r"\\approx": "≈",
        r"\\sim": "~",
        r"\\infty": "∞",
        r"\\partial": "∂",
        r"\\nabla": "∇",
    }
    for pattern, repl in replacements.items():
        out = re.sub(pattern, repl, out)

    greek = r"alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega"
    greek += r"|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega"
    out = re.sub(r"\\(" + greek + r")", r"\1", out)

    out = re.sub(r"\\sqrt\[([^\]]*)\]\{([^}]*)\}", r"(\2)^(1/\1)", out)
    out = re.sub(r"\\sqrt\{([^}]*)\}", r"sqrt(\1)", out)

    def extract_braced(text: str, start: int) -> tuple[Optional[str], int]:
        if start >= len(text) or text[start] != "{":
            return None, start
        depth = 0
        i = start
        buf: list[str] = []
        while i < len(text):
            ch = text[i]
            if ch == "{":
                depth += 1
                if depth > 1:
                    buf.append(ch)
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return "".join(buf), i + 1
                buf.append(ch)
            else:
                buf.append(ch)
            i += 1
        return None, start

    def skip_ws(text: str, idx: int) -> int:
        while idx < len(text) and text[idx].isspace():
            idx += 1
        return idx

    def replace_frac_like(text: str) -> str:
        commands = ("\\frac", "\\dfrac", "\\tfrac")
        i = 0
        pieces: list[str] = []
        while i < len(text):
            cmd = next((c for c in commands if text.startswith(c, i)), None)
            if not cmd:
                pieces.append(text[i])
                i += 1
                continue
            pos = skip_ws(text, i + len(cmd))
            num, pos = extract_braced(text, pos)
            if num is None:
                pieces.append(text[i])
                i += 1
                continue
            pos = skip_ws(text, pos)
            den, pos = extract_braced(text, pos)
            if den is None:
                pieces.append(text[i])
                i += 1
                continue
            num = replace_frac_like(num)
            den = replace_frac_like(den)
            pieces.append(f"({num})/({den})")
            i = pos
        return "".join(pieces)

    out = replace_frac_like(out)

    def replace_binomials(text: str) -> str:
        commands = ("\\binom", "\\dbinom", "\\tbinom")
        i = 0
        pieces: list[str] = []
        while i < len(text):
            cmd = next((c for c in commands if text.startswith(c, i)), None)
            if not cmd:
                pieces.append(text[i])
                i += 1
                continue
            pos = skip_ws(text, i + len(cmd))
            upper, pos = extract_braced(text, pos)
            if upper is None:
                pieces.append(text[i])
                i += 1
                continue
            pos = skip_ws(text, pos)
            lower, pos = extract_braced(text, pos)
            if lower is None:
                pieces.append(text[i])
                i += 1
                continue
            upper = replace_binomials(upper)
            lower = replace_binomials(lower)
            pieces.append(f"C({upper}, {lower})")
            i = pos
        return "".join(pieces)

    out = replace_binomials(out)

    out = re.sub(r"\^\{([^}]*)\}", r"^\1", out)
    out = re.sub(r"_(\{[^}]*\}|[A-Za-z0-9])", lambda m: "_" + m.group(1).strip("{}"), out)
    out = re.sub(r"\^(\{[^}]*\}|[A-Za-z0-9+\-*/])", lambda m: "^" + m.group(1).strip("{}"), out)

    out = out.replace(r"\left", "").replace(r"\right", "")

    out = out.replace("{", "(").replace("}", ")")

    out = out.replace("__LACE_BRACE__", "{").replace("__RACE_BRACE__", "}")
    out = out.replace(escaped_amp_placeholder, "&")
    out = re.sub(r"\s+", " ", out).strip()
    return out

def sanitize_for_mathtext(s: str) -> str:
    text = s.strip()
    if text.startswith("$$") and text.endswith("$$"):
        text = text[2:-2].strip()
    if text.startswith(r"\[") and text.endswith(r"\]"):
        text = text[2:-2].strip()
    already_math = text.startswith("$") and text.endswith("$")

    def escape_literals(segment: str) -> str:
        return re.sub(r"(?<!\\)([%&#$])", r"\\\1", segment)

    def convert_text_block(match: re.Match[str]) -> str:
        content = match.group(2)
        content = content.replace(r"\ ", " ")
        content = content.replace("~", " ")
        content = re.sub(r"\s+", " ", content).strip()
        content = re.sub(r"(?<!\\)([%&#$])", r"\\\1", content)
        content = content.replace(" ", r"\ ")
        return r"\mathrm{" + content + "}"

    text = re.sub(r"\\(text|operatorname)\*?\{([^}]*)\}", convert_text_block, text)
    text = escape_literals(text)
    text = text.replace(r"\left", "").replace(r"\right", "")
    text = re.sub(r"\s+", " ", text).strip()
    if not already_math and "\n" not in text:
        text = f"${text}$"
    return text

def clamp_image(img, max_megapixels=10, max_side=6000):
    """Downscale overly large images to safe sizes."""
    w, h = img.size
    if w*h <= max_megapixels*1_000_000 and max(w,h) <= max_side:
        return img
    scale = min((max_side / max(w, h)), ( (max_megapixels*1_000_000) / (w*h) ) ** 0.5)
    if scale >= 1.0:
        return img
    new_size = (max(1, int(w*scale)), max(1, int(h*scale)))
    return img.resize(new_size, Image.LANCZOS)

def render_latex_to_png_bytes(latex: str, fontsize: int = 28, usetex: bool = False) -> bytes:
    rcParams["text.usetex"] = bool(usetex)
    rcParams["mathtext.default"] = "regular"
    content = latex.strip()
    if not usetex:
        content = sanitize_for_mathtext(content)
    else:
        if content.startswith("$$") and content.endswith("$$"):
            content = content[2:-2].strip()
        if not (content.startswith(r"\[") and content.endswith(r"\]")) and not (content.startswith("$") and content.endswith("$")):
            content = r"\[" + content + r"\]"

    # Use a sensible figure size and tight bbox instead of manual bbox math
    fig = plt.figure(figsize=(6, 2), dpi=300)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    try:
        # Left-align to reduce chance of off-canvas metrics
        ax.text(0.01, 0.5, content, ha="left", va="center", fontsize=fontsize)
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=300, transparent=True, bbox_inches='tight', pad_inches=0.02)
        buf.seek(0)
        # Trim transparent padding then clamp to safe size
        img = Image.open(buf).convert("RGBA")
        alpha = img.getchannel("A")
        bbox = alpha.getbbox()
        if bbox:
            img = img.crop(bbox)
        img = clamp_image(img)
        out = io.BytesIO()
        img.save(out, format="PNG")
        out.seek(0)
        return out.getvalue()
    except Exception as e:
        # Add context to the error message
        raise RuntimeError(f"Matplotlib error: {e}\nCheck LaTeX syntax or for missing packages.") from e
    finally:
        # Ensure the figure is always closed to conserve memory
        plt.close(fig)

def png_bytes_to_pil(png_bytes):
    from PIL import Image
    return Image.open(io.BytesIO(png_bytes))


@dataclass
class RenderResult:
    image: "Image.Image"
    latex: str
    plain_text: str


def copy_image_to_windows_clipboard(img):
    if not HAVE_PYWIN32:
        raise RuntimeError("pywin32 not installed. Install with: pip install pywin32")

    # For apps that support transparent PNGs (e.g., Word, OneNote)
    with io.BytesIO() as png_output:
        img.save(png_output, "PNG")
        png_data = png_output.getvalue()

    # For older apps, provide a DIB (BMP) without transparency
    with io.BytesIO() as bmp_output:
        # BMP format requires RGB
        bmp = img.convert("RGB")
        bmp.save(bmp_output, "BMP")
        # The DIB format is the BMP content without the 14-byte file header
        bmp_data = bmp_output.getvalue()[14:]

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        # Register the PNG format. Older versions of pywin32 only expose
        # RegisterClipboardFormat without the explicit "W" (wide) suffix,
        # so fall back to that name if the Unicode-specific helper is
        # unavailable.
        register_format = getattr(win32clipboard, "RegisterClipboardFormatW", None)
        if register_format is None:
            register_format = win32clipboard.RegisterClipboardFormat
        CF_PNG = register_format("PNG")
        # Set both formats. Apps can choose which one they prefer.
        win32clipboard.SetClipboardData(CF_PNG, png_data)
        win32clipboard.SetClipboardData(win32con.CF_DIB, bmp_data)
    finally:
        win32clipboard.CloseClipboard()


def build_html_clipboard_fragment(mathml: str) -> bytes:
    fragment = mathml.strip()
    if not fragment:
        raise ValueError("Empty MathML fragment")
    if "<math" not in fragment:
        fragment = f"<math xmlns='http://www.w3.org/1998/Math/MathML'>{fragment}</math>"

    html = (
        "<html><body>\r\n"
        "<!--StartFragment-->"
        f"{fragment}"
        "<!--EndFragment-->\r\n"
        "</body></html>"
    )

    header_template = (
        "Version:0.9\r\n"
        "StartHTML:{start_html:08d}\r\n"
        "EndHTML:{end_html:08d}\r\n"
        "StartFragment:{start_fragment:08d}\r\n"
        "EndFragment:{end_fragment:08d}\r\n"
    )

    # Preliminary header with zero offsets to determine actual positions
    preliminary_header = header_template.format(
        start_html=0, end_html=0, start_fragment=0, end_fragment=0
    )
    start_html = len(preliminary_header)
    start_fragment = start_html + html.index("<!--StartFragment-->") + len("<!--StartFragment-->")
    end_fragment = start_html + html.index("<!--EndFragment-->")
    end_html = start_html + len(html)

    header = header_template.format(
        start_html=start_html,
        end_html=end_html,
        start_fragment=start_fragment,
        end_fragment=end_fragment,
    )
    payload = (header + html).encode("utf-8")
    return payload


def copy_mathml_to_windows_clipboard(mathml: str, plain_text: str) -> None:
    if not HAVE_PYWIN32:
        raise RuntimeError("pywin32 not installed. Install with: pip install pywin32")

    payload = build_html_clipboard_fragment(mathml)

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        register_format = getattr(win32clipboard, "RegisterClipboardFormatW", None)
        if register_format is None:
            register_format = win32clipboard.RegisterClipboardFormat
        cf_html = register_format("HTML Format")
        cf_mathml = register_format("MathML")
        win32clipboard.SetClipboardData(cf_html, payload)
        try:
            win32clipboard.SetClipboardData(cf_mathml, mathml.encode("utf-8"))
        except Exception:
            # Not all Windows versions/applications accept MathML directly.
            pass
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, plain_text)
        win32clipboard.SetClipboardData(win32con.CF_TEXT, plain_text.encode("utf-8"))
    finally:
        win32clipboard.CloseClipboard()

# -----------------------------
# GUI
# -----------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LaTeX Clip")
        self.geometry("960x640")
        self.minsize(880, 560)

        available_fonts = set(tkfont.families(self))

        def pick_font(options, fallback):
            for name in options:
                if name in available_fonts:
                    return name
            return fallback

        ui_family = pick_font(
            ("SF Pro Text", "SF UI Text", "Helvetica Neue", "Segoe UI", "Arial"),
            "Helvetica",
        )
        display_family = pick_font(
            ("SF Pro Display", "SF Pro Text", "Helvetica Neue", "Segoe UI", ui_family),
            ui_family,
        )
        mono_family = pick_font(
            ("SFMono-Regular", "SF Mono", "Menlo", "Consolas", "Courier New"),
            "Consolas",
        )

        font_ui = (ui_family, 11)
        font_editor = (mono_family, 12)
        self.option_add("*Font", font_ui)

        self.last_render: Optional[RenderResult] = None
        self.last_photo = None

        style = ttk.Style(self)
        style.theme_use("clam")

        base_bg = "#f5f5f7"
        surface_bg = "#ffffff"
        inset_bg = "#f2f2f7"
        accent = "#0a84ff"
        text_color = "#1d1d1f"
        muted = "#6e6e73"
        outline = "#d2d2d7"

        self.configure(background=base_bg)
        style.configure("TFrame", background=base_bg)
        style.configure("TLabel", background=base_bg, foreground=text_color)
        style.configure(
            "Surface.TFrame",
            background=surface_bg,
            borderwidth=1,
            relief="solid",
            bordercolor=outline,
        )
        style.configure(
            "Inset.TFrame",
            background=inset_bg,
            borderwidth=1,
            relief="solid",
            bordercolor=outline,
        )
        style.configure("Card.TFrame", background=surface_bg)
        style.configure("Surface.TLabel", background=surface_bg, foreground=text_color)
        style.configure("Title.TLabel", font=(display_family, 22, "bold"), foreground=text_color)
        style.configure("Subtitle.TLabel", font=(ui_family, 12), foreground=muted)
        style.configure("Section.TLabel", font=(ui_family, 13, "bold"), background=surface_bg, foreground=text_color)
        style.configure("Status.TLabel", foreground=muted, background=base_bg, font=(ui_family, 10))
        style.configure("Caption.TLabel", background=inset_bg, foreground=muted, font=(ui_family, 11))
        style.configure(
            "Preview.TLabel",
            background=surface_bg,
            anchor="center",
            foreground=muted,
            padding=16,
        )
        style.configure(
            "Accent.TButton",
            background=accent,
            foreground="#ffffff",
            font=(ui_family, 11, "bold"),
            borderwidth=0,
            padding=(18, 10),
            relief="flat",
            focusthickness=3,
            focuscolor=accent,
        )
        style.configure(
            "Secondary.TButton",
            background="#e5e5ea",
            foreground=text_color,
            font=(ui_family, 11),
            borderwidth=0,
            padding=(16, 10),
            relief="flat",
            focusthickness=3,
            focuscolor=outline,
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#0066d6"), ("pressed", "#0056b8")],
            foreground=[("disabled", "#ffffff")],
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#d7d7dc"), ("pressed", "#c8c8cd")],
            foreground=[("disabled", "#9c9ca1")],
        )
        style.configure(
            "TCheckbutton",
            background=surface_bg,
            foreground=text_color,
            focuscolor=surface_bg,
            padding=2,
        )
        style.configure(
            "TSpinbox",
            arrowsize=14,
            bordercolor=outline,
            background=surface_bg,
            fieldbackground=surface_bg,
        )

        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=32, pady=28)

        header = ttk.Frame(main_frame)
        header.pack(fill=tk.X, pady=(0, 18))
        ttk.Label(header, text="LaTeX Clip", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Create presentation-ready equations and copy them anywhere with a single click.",
            style="Subtitle.TLabel",
            wraplength=720,
        ).pack(anchor="w", pady=(6, 0))

        content = ttk.Frame(main_frame, style="Surface.TFrame", padding=24)
        content.pack(fill=tk.BOTH, expand=True)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(5, weight=1)

        ttk.Label(content, text="Equation Source", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self.txt = tk.Text(
            content,
            wrap="word",
            height=6,
            font=font_editor,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=outline,
            highlightcolor=accent,
            padx=14,
            pady=10,
            background=inset_bg,
            foreground=text_color,
            insertbackground=accent,
        )
        self.txt.grid(row=1, column=0, sticky="nsew", pady=(12, 18))

        options_frame = ttk.Frame(content, style="Card.TFrame")
        options_frame.grid(row=2, column=0, sticky="w", pady=(0, 12))
        self.fontsize_var = tk.IntVar(value=28)
        self.usetex_var = tk.BooleanVar(value=False)

        ttk.Label(options_frame, text="Font size:", style="Surface.TLabel").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Spinbox(
            options_frame,
            from_=10,
            to=96,
            textvariable=self.fontsize_var,
            width=5,
        ).pack(side=tk.LEFT)
        ttk.Checkbutton(
            options_frame,
            text="Use full LaTeX (MiKTeX/TeX Live)",
            variable=self.usetex_var,
        ).pack(side=tk.LEFT, padx=(20, 0))

        btns_frame = ttk.Frame(content, style="Card.TFrame")
        btns_frame.grid(row=3, column=0, sticky="w", pady=(0, 16))
        ttk.Button(btns_frame, text="Preview", style="Accent.TButton", command=self.on_preview).pack(side=tk.LEFT)
        ttk.Button(
            btns_frame,
            text="Copy as Image",
            style="Secondary.TButton",
            command=self.on_copy_image,
        ).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(
            btns_frame,
            text="Copy as Plain Text",
            style="Secondary.TButton",
            command=self.on_copy_text,
        ).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(
            btns_frame,
            text="Copy for Word/OneNote",
            style="Secondary.TButton",
            command=self.on_copy_equation,
        ).pack(side=tk.LEFT, padx=(10, 0))

        self.status = tk.StringVar(value="Ready")
        ttk.Label(content, textvariable=self.status, style="Status.TLabel").grid(
            row=4, column=0, sticky="w"
        )

        preview_container = ttk.Frame(content, style="Card.TFrame")
        preview_container.grid(row=5, column=0, sticky="nsew", pady=(20, 0))
        preview_container.columnconfigure(0, weight=1)
        preview_container.columnconfigure(1, weight=1)
        preview_container.rowconfigure(0, weight=1)

        image_panel = ttk.Frame(preview_container, style="Card.TFrame")
        image_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        image_panel.configure(padding=16)
        ttk.Label(image_panel, text="Rendered Preview", style="Section.TLabel").pack(anchor="w")
        holder = ttk.Frame(image_panel, style="Inset.TFrame", padding=12)
        holder.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.preview = ttk.Label(holder, style="Preview.TLabel")
        self.preview.pack(fill=tk.BOTH, expand=True)
        self.preview.configure(text="Rendered output will appear here")

        text_panel = ttk.Frame(preview_container, style="Card.TFrame")
        text_panel.grid(row=0, column=1, sticky="nsew")
        text_panel.configure(padding=16)
        ttk.Label(text_panel, text="Plain Text Preview", style="Section.TLabel").pack(anchor="w")
        text_holder = ttk.Frame(text_panel, style="Inset.TFrame", padding=12)
        text_holder.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.plain_preview = tk.Text(
            text_holder,
            wrap="word",
            height=6,
            relief=tk.FLAT,
            borderwidth=0,
            background=inset_bg,
            font=(ui_family, 11),
            state="disabled",
            foreground=text_color,
        )
        self.plain_preview.pack(fill=tk.BOTH, expand=True)
        self.update_plain_preview("Plain text preview will appear here")

    def get_input(self) -> str:
        return self.txt.get("1.0", "end-1c").strip()

    def set_status(self, msg: str):
        self.status.set(msg); self.update_idletasks()

    def render(self) -> RenderResult:
        latex = self.get_input()
        if not latex:
            raise ValueError("Enter some LaTeX first.")
        png = render_latex_to_png_bytes(
            latex,
            fontsize=self.fontsize_var.get(),
            usetex=self.usetex_var.get(),
        )
        img = png_bytes_to_pil(png)
        plain = latex_to_plaintext(latex)
        result = RenderResult(image=img, latex=latex, plain_text=plain)
        self.last_render = result

        max_w, max_h = 820, 320
        disp = img
        if img.width > max_w or img.height > max_h:
            disp = img.copy()
            disp.thumbnail((max_w, max_h))
        self.last_photo = ImageTk.PhotoImage(disp)
        self.preview.configure(image=self.last_photo, text="")
        self.update_plain_preview(plain)
        return result

    def on_preview(self):
        try:
            self.render(); self.set_status("Preview updated ✔")
        except Exception as e:
            messagebox.showerror("Render error", str(e)); self.set_status("Render failed")

    def on_copy_image(self):
        try:
            # Re-render if text changed since last render
            if self.last_render is None or self.get_input() != self.last_render.latex:
                current = self.render()
            else:
                current = self.last_render
            if HAVE_PYWIN32:
                copy_image_to_windows_clipboard(current.image); self.set_status("Image (with transparency) copied to clipboard ✔  (Ctrl+V into Word/OneNote)")
            else:
                out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "latex_output.png")
                current.image.save(out, "PNG")
                messagebox.showinfo("Saved image", f"pywin32 not found. Saved image to:\n{out}\nYou can insert this file into Word/OneNote.")
                self.set_status(f"Saved image to {out}")
        except Exception as e:
            messagebox.showerror("Copy error", str(e)); self.set_status("Copy failed")

    def on_copy_text(self):
        try:
            raw = self.get_input()
            if not raw: raise ValueError("Enter some LaTeX first.")
            txt = latex_to_plaintext(raw)
            self.clipboard_clear(); self.clipboard_append(txt)
            self.set_status("Plain text copied to clipboard ✔  (Ctrl+V into Word/OneNote)")
        except Exception as e:
            messagebox.showerror("Copy error", str(e)); self.set_status("Copy failed")

    def update_plain_preview(self, plain: str) -> None:
        self.plain_preview.configure(state="normal")
        self.plain_preview.delete("1.0", tk.END)
        self.plain_preview.insert("1.0", plain)
        self.plain_preview.configure(state="disabled")

    def on_copy_equation(self):
        try:
            latex = self.get_input()
            if not latex:
                raise ValueError("Enter some LaTeX first.")
            plain = latex_to_plaintext(latex)
            if latex_to_mathml is None:
                raise RuntimeError(
                    "Copying equations requires the optional 'latex2mathml' package.\n"
                    "Install it with: pip install latex2mathml"
                )
            mathml = latex_to_mathml(latex)
            if HAVE_PYWIN32:
                copy_mathml_to_windows_clipboard(mathml, plain)
                self.set_status("Equation markup copied ✔  (Paste directly into Word/OneNote)")
            else:
                self.clipboard_clear()
                # Provide MathML as a fallback for platforms without pywin32.
                self.clipboard_append(mathml)
                messagebox.showinfo(
                    "Limited clipboard support",
                    "MathML copied as plain text. Some apps may require Windows for direct equation pasting.",
                )
                self.set_status("MathML copied to clipboard")
        except Exception as e:
            messagebox.showerror("Copy error", str(e))
            self.set_status("Copy failed")

if __name__ == "__main__":
    app = App()
    app.mainloop()



