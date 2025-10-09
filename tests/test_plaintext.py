"""Regression tests for the LaTeX to plain-text helpers."""

from __future__ import annotations

import sys
import types
from importlib import util
from pathlib import Path

import pytest


def _install_test_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide lightweight shims for optional runtime dependencies."""

    # ttkthemes is only required for the GUI, so a simple placeholder works.
    themed_module = types.ModuleType("ttkthemes")
    themed_module.ThemedTk = type("DummyThemedTk", (), {})
    monkeypatch.setitem(sys.modules, "ttkthemes", themed_module)

    # Pillow stubs that satisfy the module-level imports without shipping the
    # heavyweight dependency in the test environment.
    pil_module = types.ModuleType("PIL")
    pil_image = types.ModuleType("PIL.Image")
    pil_image.MAX_IMAGE_PIXELS = None
    pil_image.LANCZOS = 1

    def _unavailable(*_args, **_kwargs):  # pragma: no cover - defensive helper
        raise RuntimeError("Image operations are not available in tests.")

    pil_image.open = _unavailable
    pil_imagetk = types.ModuleType("PIL.ImageTk")
    pil_module.Image = pil_image
    pil_module.ImageTk = pil_imagetk
    monkeypatch.setitem(sys.modules, "PIL", pil_module)
    monkeypatch.setitem(sys.modules, "PIL.Image", pil_image)
    monkeypatch.setitem(sys.modules, "PIL.ImageTk", pil_imagetk)

    # Matplotlib shims that keep rcParams available and provide inert pyplot
    # helpers so module import succeeds.
    mpl_module = types.ModuleType("matplotlib")
    mpl_module.rcParams = {}
    mpl_module.use = lambda _backend: None

    pyplot = types.ModuleType("matplotlib.pyplot")

    class _DummyFigure:
        def __init__(self) -> None:
            self.patch = types.SimpleNamespace(set_alpha=lambda *_a, **_k: None)

        def add_axes(self, _rect):
            return types.SimpleNamespace(
                axis=lambda *_a, **_k: None,
                text=lambda *_a, **_k: None,
            )

    pyplot.figure = lambda *_a, **_k: _DummyFigure()
    pyplot.savefig = lambda *_a, **_k: None
    pyplot.close = lambda *_a, **_k: None
    mpl_module.pyplot = pyplot
    monkeypatch.setitem(sys.modules, "matplotlib", mpl_module)
    monkeypatch.setitem(sys.modules, "matplotlib.pyplot", pyplot)


@pytest.fixture
def latexclip(monkeypatch: pytest.MonkeyPatch):
    """Import the module under test with lightweight dependency shims."""

    # Ensure a clean import each time the fixture initialises.
    sys.modules.pop("latexclip", None)
    _install_test_stubs(monkeypatch)

    spec = util.spec_from_file_location("latexclip", Path(__file__).resolve().parent.parent / "latexclip.py")
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Unable to load latexclip module for testing.")

    module = util.module_from_spec(spec)
    sys.modules["latexclip"] = module
    spec.loader.exec_module(module)
    return module


def test_plaintext_preserves_nested_fractions(latexclip):
    result = latexclip.latex_to_plaintext(r"\frac{1+\frac{1}{x}}{y}")
    assert result == "(1+(1)/(x))/(y)"


def test_plaintext_handles_nested_sqrt(latexclip):
    result = latexclip.latex_to_plaintext(r"\sqrt{\frac{a}{b}}")
    assert result == r"sqrt(\frac(a)(b))"


def test_plaintext_expands_text_blocks(latexclip):
    result = latexclip.latex_to_plaintext(r"\text{Area} = \frac{1}{2} b h")
    assert result == "Area = (1)/(2) b h"


def test_sanitizer_escapes_plain_text_specials(latexclip):
    result = latexclip.sanitize_for_mathtext("Save 50% & more #1")
    assert result == r"$Save 50\% \& more \#1$"


def test_sanitizer_retains_existing_escapes(latexclip):
    result = latexclip.sanitize_for_mathtext(r"Already escaped \% value")
    assert result == r"$Already escaped \% value$"


def test_plaintext_maps_common_symbols(latexclip):
    result = latexclip.latex_to_plaintext(r"\alpha \cdot \beta \leq \gamma")
    assert result == "alpha · beta ≤ gamma"


def test_plaintext_handles_binomials(latexclip):
    result = latexclip.latex_to_plaintext(r"\binom{n}{k}")
    assert result == "C(n, k)"


def test_plaintext_handles_displaystyle_binomials(latexclip):
    result = latexclip.latex_to_plaintext(r"\dbinom{\dfrac{n}{2}}{k}")
    assert result == "C((n)/(2), k)"


def test_plaintext_handles_displaystyle_fractions(latexclip):
    result = latexclip.latex_to_plaintext(r"\dfrac{a}{\tfrac{b}{c}}")
    assert result == "(a)/((b)/(c))"


def test_plaintext_handles_ampersands_in_text(latexclip):
    latex = r"$$NOI = \text{Gross Potential Income} - \text{Vacancy & Collection Losses} - \text{Operating Expenses}$$"
    result = latexclip.latex_to_plaintext(latex)
    assert (
        result
        == "NOI = Gross Potential Income - Vacancy & Collection Losses - Operating Expenses"
    )


def test_plaintext_renders_matrix_structure(latexclip):
    latex = r"\begin{bmatrix} a & b \\ c & d \end{bmatrix}"
    result = latexclip.latex_to_plaintext(latex)
    assert result == "[a, b; c, d]"


def test_plaintext_handles_matrix_vector_equation(latexclip):
    latex = r"""A\mathbf{x} =
\begin{bmatrix}
1 & 2 \\
3 & 4
\end{bmatrix}
\begin{bmatrix}
x_1 \\ x_2
\end{bmatrix}
=
\begin{bmatrix}
5 \\ 11
\end{bmatrix}"""

    result = latexclip.latex_to_plaintext(latex)

    assert result == "Ax = [1, 2; 3, 4] [x_1; x_2] = [5; 11]"


def test_sanitizer_preserves_spaces_inside_text(latexclip):
    latex = r"$$NOI = \text{Operating Expenses}$$"
    result = latexclip.sanitize_for_mathtext(latex)
    assert result == r"$NOI = \mathrm{Operating\ Expenses}$"


def test_sanitizer_escapes_ampersands_inside_text(latexclip):
    latex = r"$$\text{Vacancy & Collection}$$"
    result = latexclip.sanitize_for_mathtext(latex)
    assert result == r"$\mathrm{Vacancy\ \&\ Collection}$"


def test_plaintext_supports_cases_environments(latexclip):
    latex = r"\begin{cases} x^2, & x > 0 \\ 0, & \text{otherwise} \end{cases}"
    result = latexclip.latex_to_plaintext(latex)
    assert result == "(x^2 if x > 0; 0 otherwise)"


def test_plaintext_handles_align_star(latexclip):
    latex = r"\begin{align*} a &= b + c \\ d &= e - f \end{align*}"
    result = latexclip.latex_to_plaintext(latex)
    assert result == "a = b + c; d = e - f"


def test_plaintext_trims_hlines_in_arrays(latexclip):
    latex = r"\begin{array}{cc} \hline a & b \\ \hline c & d \end{array}"
    result = latexclip.latex_to_plaintext(latex)
    assert result == "[a, b; c, d]"


def test_plaintext_flattens_additional_text_macros(latexclip):
    latex = r"\mathbf{Net}~\mathrm{Income}"
    result = latexclip.latex_to_plaintext(latex)
    assert result == "Net Income"
