import streamlit as st
import sympy as sp
from functools import partial
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib as mpl
import streamlit.components.v1 as components
import re
import streamlit_ace as ace

mpl.use('Agg')

# Initialize session state
if "formula" not in st.session_state:
    st.session_state.formula = ""
if "latex" not in st.session_state:
    st.session_state.latex = ""
if "history" not in st.session_state:
    st.session_state.history = []
if "history_index" not in st.session_state:
    st.session_state.history_index = -1
if "color_map" not in st.session_state:
    st.session_state.color_map = {}  # {subexpression: hex_color}
if "error_highlight" not in st.session_state:
    st.session_state.error_highlight = ""
if "expr" not in st.session_state:
    st.session_state.expr = None
if "mobile_mode" not in st.session_state:
    st.session_state.mobile_mode = False  # Default to False to avoid user-agent issues

# Custom ColoredLatexPrinter
from sympy.printing.latex import LatexPrinter

class ColoredLatexPrinter(LatexPrinter):
    def __init__(self, colored_subexprs, settings=None):
        super().__init__(settings=settings)
        self.colored_subexprs = colored_subexprs

    def _print(self, expr):
        if expr in self.colored_subexprs:
            color = self.colored_subexprs[expr]
            return f"\\color{{{color}}}{{{super()._print(expr)}}}"
        return super()._print(expr)

# Sanitize formula input
def sanitize_formula(formula):
    return re.sub(r'[^\w\s+\-*/^()=,.{}\[\]]', '', formula.strip())

# Validate formula and identify error location
def is_valid_formula(formula):
    if not formula:
        return False, "Formula is empty.", (0, len(formula))
    if formula[-1] in ['+', '-', '*', '/', '^', '_', '÷']:
        error_char = formula[-1]
        return False, f"Formula ends with an incomplete operator '{error_char}'.", (len(formula) - 1, len(formula))
    incomplete_functions = ['sqrt(', 'log(', 'Sum(', 'Product(', 'Limit(', 'Integral(', 'Derivative(', 'sin(', 'cos(', 'tan(', 'cot(', 'sec(', 'csc(', 'arcsin(', 'arccos(', 'arctan(', 'sinh(', 'cosh(', 'tanh(']
    for func in incomplete_functions:
        if formula.endswith(func):
            return False, f"Incomplete function call: '{func}' is missing arguments.", (len(formula) - len(func), len(formula))
    if formula.count('(') != formula.count(')'):
        stack = []
        for i, char in enumerate(formula):
            if char == '(':
                stack.append(i)
            elif char == ')':
                if not stack:
                    return False, "Unbalanced parentheses: extra closing parenthesis.", (i, i + 1)
                stack.pop()
        if stack:
            return False, f"Unbalanced parentheses: unclosed parenthesis at position {stack[-1]}.", (stack[-1], stack[-1] + 1)
    if re.search(r',\s*,', formula):
        match = re.search(r',\s*,', formula)
        return False, "Invalid function arguments: consecutive commas detected.", (match.start(), match.end())
    if re.search(r'\(\s*,', formula):
        match = re.search(r'\(\s*,', formula)
        return False, "Invalid function arguments: empty argument detected.", (match.start(), match.end())
    if re.search(r'(Integral|Derivative|Sum|Product|Limit)\(\s*,', formula):
        match = re.search(r'(Integral|Derivative|Sum|Product|Limit)\(\s*,', formula)
        return False, f"{match.group(1)} is missing required arguments.", (match.start(), match.end())
    if re.search(r'[a-zA-Z]+_[a-zA-Z0-9]+', formula) and not re.search(r'(tau|mu|phi|rho|sigma|gamma|dot\{gamma\})_[a-zA-Z0-9]+', formula):
        match = re.search(r'[a-zA-Z]+_[a-zA-Z0-9]+', formula)
        return False, "Invalid subscripted symbol detected.", (match.start(), match.end())
    return True, "", None

# Highlight error in formula
def highlight_error(formula, error_span):
    if not error_span:
        return formula
    start, end = error_span
    return f"{formula[:start]}<span style='color: red;'>{formula[start:end]}</span>{formula[end:]}"

# Validate subexpression with strict parsing
def is_valid_subexpression(formula, subexpr):
    allowed = {
        "sqrt": sp.sqrt, "log": sp.log, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
        "cot": sp.cot, "sec": sp.sec, "csc": sp.csc, "arcsin": sp.asin, "arccos": sp.acos,
        "arctan": sp.atan, "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh, "exp": sp.exp,
        "Sum": sp.Sum, "Product": sp.Product, "Limit": sp.Limit, "Integral": sp.Integral,
        "Derivative": sp.Derivative, "pi": sp.pi, "e": sp.E, "alpha": sp.Symbol("alpha"),
        "beta": sp.Symbol("beta"), "gamma": sp.Symbol("gamma"), "delta": sp.Symbol("delta"),
        "mu": sp.Symbol("mu"), "rho": sp.Symbol("rho"), "sigma": sp.Symbol("sigma"),
        "tau": sp.Symbol("tau"), "phi": sp.Symbol("phi"), "omega": sp.Symbol("omega"),
        "k": sp.Symbol("k"), "x": sp.Symbol("x"), "dot{gamma}": sp.Symbol("dot{gamma}"),
        "tau_0": sp.Symbol("tau_0")
    }
    try:
        parsed_formula = formula.replace("^", "**").replace("÷", "/")
        parsed_subexpr = subexpr.replace("^", "**").replace("÷", "/")
        expr = sp.sympify(parsed_formula, locals=allowed)
        sub_expr = sp.sympify(parsed_subexpr, locals=allowed)
        def contains_subexpr(expr, sub_expr):
            if expr == sub_expr:
                return True
            for arg in expr.args:
                if contains_subexpr(arg, sub_expr):
                    return True
            return False
        valid = contains_subexpr(expr, sub_expr)
        return valid, "" if valid else "Subexpression not found in formula."
    except sp.SympifyError as e:
        return False, f"Invalid subexpression: {str(e)}"
    except Exception as e:
        return False, f"Error validating subexpression: {str(e)}"

# Cache LaTeX rendering
@st.cache_data
def get_latex(formula, color_map):
    allowed = {
        "sqrt": sp.sqrt, "log": sp.log, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
        "cot": sp.cot, "sec": sp.sec, "csc": sp.csc, "arcsin": sp.asin, "arccos": sp.acos,
        "arctan": sp.atan, "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh, "exp": sp.exp,
        "Sum": sp.Sum, "Product": sp.Product, "Limit": sp.Limit, "Integral": sp.Integral,
        "Derivative": sp.Derivative, "pi": sp.pi, "e": sp.E, "alpha": sp.Symbol("alpha"),
        "beta": sp.Symbol("beta"), "gamma": sp.Symbol("gamma"), "delta": sp.Symbol("delta"),
        "mu": sp.Symbol("mu"), "rho": sp.Symbol("rho"), "sigma": sp.Symbol("sigma"),
        "tau": sp.Symbol("tau"), "phi": sp.Symbol("phi"), "omega": sp.Symbol("omega"),
        "k": sp.Symbol("k"), "x": sp.Symbol("x"), "dot{gamma}": sp.Symbol("dot{gamma}"),
        "tau_0": sp.Symbol("tau_0")
    }
    try:
        parsed_formula = formula.replace("^", "**").replace("÷", "/")
        parsed_formula = re.sub(r'\blog\(', 'sp.log(', parsed_formula)
        parsed_formula = re.sub(r'Sum\(\s*([^,)]*?)\s*,\s*\(\s*x\s*,\s*([^,)]*?)\s*,\s*([^)]*?)\s*\)', 
                                lambda m: f'sp.Sum({m.group(1).strip() or "1"}, (x, {m.group(2).strip()}, {m.group(3).strip()}))', 
                                parsed_formula)
        parsed_formula = re.sub(r'Product\(\s*([^,)]*?)\s*,\s*\(\s*x\s*,\s*([^,)]*?)\s*,\s*([^)]*?)\s*\)', 
                                lambda m: f'sp.Product({m.group(1).strip() or "1"}, (x, {m.group(2).strip()}, {m.group(3).strip()}))', 
                                parsed_formula)
        parsed_formula = re.sub(r'Limit\(\s*([^,)]*?)\s*,\s*x\s*,\s*([^)]*?)\s*\)', 
                                lambda m: f'sp.Limit({m.group(1).strip() or "1"}, x, {m.group(2).strip()})', 
                                parsed_formula)
        parsed_formula = re.sub(r'Integral\(\s*([^,)]*?)\s*,\s*x\s*\)', 
                                lambda m: f'sp.Integral({m.group(1).strip() or "1"}, x)', 
                                parsed_formula)
        parsed_formula = re.sub(r'Derivative\(\s*([^,)]*?)\s*,\s*x\s*\)', 
                                lambda m: f'sp.Derivative({m.group(1).strip() or "1"}, x)', 
                                parsed_formula)
        parsed_formula = re.sub(r'dot\{gamma\}', 'sp.Symbol("dot{gamma}")', parsed_formula)
        parsed_formula = re.sub(r'tau_0', 'sp.Symbol("tau_0")', parsed_formula)

        expr = sp.sympify(parsed_formula, locals=allowed)

        colored_subexprs = {}
        for subexpr_str, color in color_map.items():
            try:
                sub_expr = sp.sympify(subexpr_str.replace("^", "**").replace("÷", "/"), locals=allowed)
                colored_subexprs[sub_expr] = color
            except sp.SympifyError:
                continue

        settings = {'mul_symbol': 'times', 'fold_short_frac': False, 'order': 'none'}
        printer = ColoredLatexPrinter(colored_subexprs, settings=settings)
        latex_str = printer.doprint(expr)

        latex_str = re.sub(r'\\frac\{d\}\{d x\}\s*([a-zA-Z])', r'\\frac{d\1}{dx}', latex_str)
        latex_str = re.sub(r'\\frac\{d\}\{d x\}\s*\\left\(([^)]+)\\right\)', r'\\frac{d(\\1)}{dx}', latex_str)
        latex_str = latex_str.replace(r'\dot{gamma}', r'\dot{\gamma}')

        has_colors = bool(colored_subexprs)
        if has_colors:
            latex_str = f"\\usepackage{{color}}\n{latex_str}"

        return latex_str, expr, has_colors
    except sp.SympifyError as e:
        return f"Parsing error: {str(e)}", None, False
    except ValueError as e:
        return f"Value error: {str(e)}", None, False
    except Exception as e:
        return f"Invalid formula: {str(e)}", None, False

# Cache image generation with dynamic sizing
@st.cache_data
def latex_to_image(latex_str, has_colors):
    try:
        formula_length = len(latex_str)
        has_complex_structures = any(s in latex_str for s in [r'\frac', r'\sum', r'\int', r'\prod', r'\lim'])
        width = min(10 + formula_length * 0.05, 20)
        height = 2 + (1 if has_complex_structures else 0)

        rc_dict = {'text.usetex': True}
        if has_colors:
            rc_dict['text.latex.preamble'] = r'\usepackage{color}'
        with mpl.rc_context(rc_dict):
            temp_fig = plt.figure(figsize=(width, height))
            temp_ax = temp_fig.add_subplot(111)
            temp_ax.axis('off')
            t = temp_ax.text(0.5, 0.5, f'${latex_str}$', fontsize=20, ha='center', va='center')
            temp_fig.canvas.draw()
            bbox = t.get_window_extent(temp_fig.canvas.get_renderer())
            bbox_inches = bbox.transformed(temp_fig.dpi_scale_trans.inverted())
            plt.close(temp_fig)
            width = bbox_inches.width + 0.3
            height = bbox_inches.height + 0.2
            fig = plt.figure(figsize=(width, height))
            fig.patch.set_facecolor('white')
            ax = fig.add_axes([0, 0, 1, 1])
            ax.axis('off')
            ax.text(0.5, 0.5, f'${latex_str}$', fontsize=20, ha='center', va='center')
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.05, facecolor='white')
            plt.close(fig)
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode()
            return img_b64
    except Exception as e:
        st.error(f"Image generation error: {str(e)}")
        return None

# Update formula and history
def update_formula():
    new_formula = sanitize_formula(st.session_state.formula_input)
    if new_formula != st.session_state.formula:
        if st.session_state.history_index < len(st.session_state.history) - 1:
            st.session_state.history = st.session_state.history[:st.session_state.history_index + 1]
        st.session_state.history.append(new_formula)
        st.session_state.history_index += 1
        st.session_state.formula = new_formula
        valid, error_msg, error_span = is_valid_formula(new_formula)
        if not valid:
            st.session_state.latex = f"Invalid formula: {error_msg}"
            st.session_state.error_highlight = highlight_error(new_formula, error_span)
            st.session_state.expr = None
            st.error(error_msg)
            return
        st.session_state.error_highlight = ""
        latex_str, expr, has_colors = get_latex(new_formula, st.session_state.color_map)
        st.session_state.latex = latex_str
        st.session_state.expr = expr
        st.session_state.has_colors = has_colors

def undo():
    if st.session_state.history_index > 0:
        st.session_state.history_index -= 1
        st.session_state.formula = st.session_state.history[st.session_state.history_index]
        st.session_state.formula_input = st.session_state.formula
        update_formula()

def redo():
    if st.session_state.history_index < len(st.session_state.history) - 1:
        st.session_state.history_index += 1
        st.session_state.formula = st.session_state.history[st.session_state.history_index]
        st.session_state.formula_input = st.session_state.formula
        update_formula()

def clear_formula():
    st.session_state.formula = ""
    st.session_state.formula_input = ""
    st.session_state.latex = ""
    st.session_state.color_map = {}
    st.session_state.error_highlight = ""
    st.session_state.expr = None
    st.session_state.history.append("")
    st.session_state.history_index += 1

def append_to_formula(text):
    st.session_state.formula += text
    st.session_state.formula_input = st.session_state.formula
    update_formula()

def add_color():
    subexpr = sanitize_formula(st.session_state.color_subexpr)
    color = st.session_state.color_picker
    valid, error_msg = is_valid_subexpression(st.session_state.formula, subexpr)
    if not valid:
        st.error(error_msg)
        return
    st.session_state.color_map[subexpr] = color
    update_formula()

def remove_color(subexpr):
    if subexpr in st.session_state.color_map:
        del st.session_state.color_map[subexpr]
        update_formula()

# UI
st.set_page_config(page_title="Advanced Formula to LaTeX Converter", layout="wide")
st.title("Advanced Formula to LaTeX Converter")

# Responsive CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 40px;
        font-size: 16px;
    }
    @media (max-width: 600px) {
        .stButton>button {
            font-size: 14px;
            padding: 8px;
        }
    }
    .tooltip {
        position: relative;
        display: inline-block;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 120px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -60px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# Formula input with syntax highlighting and placeholder
st.write("Enter your formula")
formula_input = ace.st_ace(
    value=st.session_state.formula,
    language="python",
    theme="monokai",
    key="formula_input",
    auto_update=False,
    height=100,
    placeholder="e.g., (x+2)/(x-1), sin(x^2), Integral(x^2, x)"
)
if formula_input != st.session_state.formula:
    update_formula()

# Display error highlighting
if st.session_state.error_highlight:
    st.markdown(f"**Error in formula:** {st.session_state.error_highlight}", unsafe_allow_html=True)

# Undo, Redo, Clear buttons
col_undo, col_redo, col_clear = st.columns(3)
with col_undo:
    st.button("Undo (Ctrl+Z)", on_click=undo, disabled=st.session_state.history_index <= 0, key="undo", help="Undo last action")
with col_redo:
    st.button("Redo (Ctrl+Y)", on_click=redo, disabled=st.session_state.history_index >= len(st.session_state.history) - 1, key="redo", help="Redo last action")
with col_clear:
    st.button("Clear", on_click=clear_formula, key="clear", help="Clear the formula")

# Color selection UI
with st.expander("Color Subexpressions", expanded=False):
    st.write("Select a subexpression and color:")
    col_subexpr, col_color, col_add = st.columns([3, 2, 1])
    with col_subexpr:
        st.text_input("Subexpression (e.g., (x+2))", key="color_subexpr")
    with col_color:
        st.color_picker("Choose color", key="color_picker")
    with col_add:
        st.button("Add Color", on_click=add_color, key="add_color", help="Add color to subexpression")
    if st.session_state.color_map:
        st.write("Current color assignments:")
        for subexpr, color in st.session_state.color_map.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{subexpr}: {color}")
            with col2:
                st.button("Remove", key=f"remove_{hash(subexpr)}", on_click=partial(remove_color, subexpr), help="Remove color")

# Symbol buttons in collapsible sections
num_cols = 3 if st.session_state.get("mobile_mode", False) else 5
with st.expander("Mathematical Symbols", expanded=True):
    cols = st.columns(num_cols)
    buttons = [
        ("√ Square Root", "sqrt()", "Insert square root"),
        ("÷ Division", "/", "Insert division"),
        ("× Multiplication", "*", "Insert multiplication"),
        ("^ Exponent", "^", "Insert exponent"),
        ("_ Subscript", "_", "Insert subscript"),
        ("∫ Integral", "Integral(1, x)", "Insert integral w.r.t. x"),
        ("d/dx Derivative", "Derivative(1, x)", "Insert derivative w.r.t. x"),
        ("∑ Sum", "Sum(1, (x, 0, n))", "Insert summation"),
        ("∏ Product", "Product(1, (x, 0, n))", "Insert product"),
        ("lim Limit", "Limit(1, x, a)", "Insert limit"),
        ("π Pi", "pi", "Insert pi"),
        ("e Exponential", "exp(1)", "Insert exponential")
    ]
    for i, (label, text, tooltip) in enumerate(buttons):
        with cols[i % num_cols]:
            st.button(label, on_click=partial(append_to_formula, text), key=f"math_{i}", help=tooltip)

with st.expander("Trigonometric Functions"):
    cols_trig = st.columns(num_cols)
    trig_buttons = [
        ("sin Sine", "sin()", "Insert sine"),
        ("cos Cosine", "cos()", "Insert cosine"),
        ("tan Tangent", "tan()", "Insert tangent"),
        ("cot Cotangent", "cot()", "Insert cotangent"),
        ("sec Secant", "sec()", "Insert secant"),
        ("csc Cosecant", "csc()", "Insert cosecant"),
        ("sin⁻¹ Arcsine", "arcsin()", "Insert arcsine"),
        ("cos⁻¹ Arccosine", "arccos()", "Insert arccosine"),
        ("tan⁻¹ Arctangent", "arctan()", "Insert arctangent")
    ]
    for i, (label, text, tooltip) in enumerate(trig_buttons):
        with cols_trig[i % num_cols]:
            st.button(label, on_click=partial(append_to_formula, text), key=f"trig_{i}", help=tooltip)

with st.expander("Hyperbolic Functions"):
    cols_hyp = st.columns(min(num_cols, 3))
    hyp_buttons = [
        ("sinh Sinh", "sinh()", "Insert hyperbolic sine"),
        ("cosh Cosh", "cosh()", "Insert hyperbolic cosine"),
        ("tanh Tanh", "tanh()", "Insert hyperbolic tangent")
    ]
    for i, (label, text, tooltip) in enumerate(hyp_buttons):
        with cols_hyp[i % min(num_cols, 3)]:
            st.button(label, on_click=partial(append_to_formula, text), key=f"hyp_{i}", help=tooltip)

with st.expander("Greek and Engineering Symbols"):
    cols_eng = st.columns(num_cols)
    eng_buttons = [
        ("α Alpha", "alpha", "Insert alpha"),
        ("β Beta", "beta", "Insert beta"),
        ("γ Gamma", "gamma", "Insert gamma"),
        ("γ̇ Gamma Dot", "dot{gamma}", "Insert gamma dot"),
        ("δ Delta", "delta", "Insert delta"),
        ("μ Mu", "mu", "Insert mu"),
        ("ρ Rho", "rho", "Insert rho"),
        ("σ Sigma", "sigma", "Insert sigma"),
        ("τ Tau", "tau", "Insert tau"),
        ("φ Phi", "phi", "Insert phi")
    ]
    for i, (label, text, tooltip) in enumerate(eng_buttons):
        with cols_eng[i % num_cols]:
            st.button(label, on_click=partial(append_to_formula, text), key=f"eng_{i}", help=tooltip)

# LaTeX output and rendering
st.write("LaTeX Output:")
st.text_area("LaTeX code", value=st.session_state.latex, height=100, key="latex_output", disabled=True)

# Render the LaTeX and copy buttons
st.write("Rendered Formula:")
if st.session_state.latex and not st.session_state.latex.startswith("Invalid formula"):
    try:
        display_latex = st.session_state.latex
        if "\\usepackage{color}" in display_latex:
            display_latex = display_latex.replace("\\usepackage{color}\n", "")
        st.latex(display_latex)
        
        # Generate image version
        has_colors = hasattr(st.session_state, 'has_colors') and st.session_state.has_colors
        img_b64 = latex_to_image(display_latex, has_colors)
        
        # JavaScript for clipboard operations
        copy_js = """
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
        <script>
        function copyLatexText() {
            const button = document.getElementById('copy-latex-btn');
            const latexCode = document.getElementById('latex-content').innerText;
            navigator.clipboard.writeText(latexCode).then(() => {
                button.style.backgroundColor = '#00ff00';
                button.innerText = '✓ Copied!';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy LaTeX';
                }, 1500);
            }, (err) => {
                console.error('Failed to copy:', err);
                button.style.backgroundColor = '#ff0000';
                button.innerText = 'Failed';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy LaTeX';
                }, 1500);
            });
        }

        async function copyForWord() {
            const button = document.getElementById('copy-word-btn');
            const latexCode = document.getElementById('latex-content').innerText;
            try {
                const mathml = await MathJax.tex2mmlPromise(latexCode);
                const htmlContent = `<!DOCTYPE html><html><body>${mathml}</body></html>`;
                const blob = new Blob([htmlContent], { type: 'text/html' });
                const clipboardItem = new ClipboardItem({ 'text/html': blob });
                await navigator.clipboard.write([clipboardItem]);
                button.style.backgroundColor = '#00ff00';
                button.innerText = '✓ Copied!';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy for Word';
                }, 1500);
            } catch (err) {
                console.error('Failed to copy:', err);
                button.style.backgroundColor = '#ff0000';
                button.innerText = 'Failed';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy for Word';
                }, 1500);
            }
        }

        async function copyAsImage() {
            const button = document.getElementById('copy-image-btn');
            const imgElement = document.getElementById('latex-image');
            if (!imgElement) {
                button.style.backgroundColor = '#ff0000';
                button.innerText = 'No Image';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy as Image';
                }, 1500);
                return;
            }
            try {
                button.innerText = 'Copying...';
                const response = await fetch(imgElement.src);
                const blob = await response.blob();
                const clipboardItem = new ClipboardItem({ 'image/png': blob });
                await navigator.clipboard.write([clipboardItem]);
                button.style.backgroundColor = '#00ff00';
                button.innerText = '✓ Copied!';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy as Image';
                }, 1500);
            } catch (err) {
                console.error('Failed to copy:', err);
                button.style.backgroundColor = '#ff0000';
                button.innerText = 'Failed';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy as Image';
                }, 1500);
            }
        }
        </script>
        """
        
        # HTML content for buttons
        html_content = f"""
        {copy_js}
        <div id="latex-content" style="display: none;">{st.session_state.latex}</div>
        """
        if img_b64:
            html_content += f"""
            <img id="latex-image" src="data:image/png;base64,{img_b64}" style="max-width: 100%; margin-top: 10px;" />
            """
        else:
            html_content += """
            <p style="color: #ff0000;">No image available.</p>
            """
        
        html_content += """
        <div style="display: flex; gap: 10px; margin-top: 10px;">
            <button id="copy-latex-btn" onclick="copyLatexText()" 
                    style="background-color: #0f80c1; color: white; padding: 10px 20px; 
                           border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                Copy LaTeX
            </button>
            <button id="copy-word-btn" onclick="copyForWord()" 
                    style="background-color: #0f80c1; color: white; padding: 10px 20px; 
                           border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                Copy for Word
            </button>
            <button id="copy-image-btn" onclick="copyAsImage()" 
                    style="background-color: #0f80c1; color: white; padding: 10px 20px; 
                           border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                Copy as Image
            </button>
        </div>
        <p style="font-size: 12px; color: #666; margin-top: 10px;">
            • <strong>Copy LaTeX</strong>: Copies the LaTeX code as text<br>
            • <strong>Copy for Word</strong>: Copies MathML for direct pasting into Word<br>
            • <strong>Copy as Image</strong>: Copies as PNG image (works in most applications)
        </p>
        """
        
        components.html(html_content, height=320)
        
    except Exception as e:
        st.error(f"Unable to render LaTeX: {str(e)}")
else:
    st.write("Enter a valid formula to see the LaTeX rendering.")

# Example formulas
with st.expander("Example Formulas"):
    st.markdown("""
    Try these examples:
    - `[(x+2) * (x+6)] / [(x+4) + (x/5)]` → Fraction with nested parentheses
    - `sin(x^2) + cos(x)` → Trigonometric expression
    - `Integral(x^2, x)` → Integral of x²
    - `Sum(k^2, (k, 1, n))` → Summation of k² from 1 to n
    """)

# Debugging: Display session state for troubleshooting
# st.write("Debug: Session State:", st.session_state)
