import streamlit as st
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations
from functools import partial, lru_cache
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
import streamlit.components.v1 as components
import re

matplotlib.use('Agg')

# Initialize session state
if "formula" not in st.session_state:
    st.session_state.formula = ""
if "latex" not in st.session_state:
    st.session_state.latex = ""
if "temp_formula" not in st.session_state:
    st.session_state.temp_formula = ""
if "subscript_trigger" not in st.session_state:
    st.session_state.subscript_trigger = False
if "manual_edit" not in st.session_state:
    st.session_state.manual_edit = False

# Function to validate formula
def is_valid_formula(formula):
    if not formula.strip():
        return False, "Formula is empty."
    if formula.strip()[-1] in ['+', '-', '*', '/', '^', '_']:
        return False, "Formula ends with an incomplete operator."
    if '{' in formula or '}' in formula:
        return False, "LaTeX braces {} not allowed in formula input. Use SymPy syntax (e.g., x_1 instead of x_{1})."
    incomplete_functions = ['sqrt(', 'log(', 'Integral(', 'Derivative(', 'Sum(', 'Limit(', 'sin(', 'cos(', 'tan(', 'cot(', 'sec(', 'csc(', 'asin(', 'acos(', 'atan(', 'sinh(', 'cosh(', 'tanh(', 'exp(']
    for func in incomplete_functions:
        if formula.strip().endswith(func):
            return False, f"Incomplete function call: '{func}' is missing arguments."
    if formula.count('(') != formula.count(')'):
        return False, "Unbalanced parentheses in formula."
    if re.search(r',\s*,', formula):
        return False, "Invalid function arguments: consecutive commas detected."
    if re.search(r'\(\s*,', formula):
        return False, "Invalid function arguments: empty argument detected."
    if re.search(r'(Integral|Derivative)\(\s*,\s*\w+\s*\)', formula):
        return False, "Integral/Derivative is missing the function to integrate/differentiate."
    return True, ""

# Function to get locals with automatic symbol declaration
def get_locals(formula):
    local_dict = {
        "sp": sp,
        "sqrt": sp.sqrt,
        "log": sp.log,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "cot": sp.cot,
        "sec": sp.sec,
        "csc": sp.csc,
        "asin": sp.asin,
        "acos": sp.acos,
        "atan": sp.atan,
        "sinh": sp.sinh,
        "cosh": sp.cosh,
        "tanh": sp.tanh,
        "exp": sp.exp,
        "Sum": sp.Sum,
        "Limit": sp.Limit,
        "Integral": sp.Integral,
        "Derivative": sp.Derivative,
        "oo": sp.oo,
        "pi": sp.pi,
        "e": sp.E,
        "phi": sp.Symbol('phi'),
        "kappa": sp.Symbol('kappa'),
        "mu": sp.Symbol('mu'),
        "alpha": sp.Symbol('alpha'),
        "beta": sp.Symbol('beta'),
        "gamma": sp.Symbol('gamma'),
        "delta": sp.Symbol('delta'),
        "Delta": sp.Symbol('Delta'),
        "epsilon": sp.Symbol('epsilon'),
        "zeta": sp.Symbol('zeta'),
        "eta": sp.Symbol('eta'),
        "theta": sp.Symbol('theta'),
        "Theta": sp.Symbol('Theta'),
        "iota": sp.Symbol('iota'),
        "lambda": sp.Symbol('lambda'),
        "Lambda": sp.Symbol('Lambda'),
        "nu": sp.Symbol('nu'),
        "xi": sp.Symbol('xi'),
        "rho": sp.Symbol('rho'),
        "sigma": sp.Symbol('sigma'),
        "Sigma": sp.Symbol('Sigma'),
        "tau": sp.Symbol('tau'),
        "Phi": sp.Symbol('Phi'),
        "omega": sp.Symbol('omega'),
        "Omega": sp.Symbol('Omega'),
        "degree": sp.Symbol('degree'),
        "approx": sp.Symbol('approx'),
        "ne": sp.Symbol('ne'),
        "ge": sp.Symbol('ge'),
        "le": sp.Symbol('le'),
    }
    # Automatically add undefined variables as symbols
    variables = re.findall(r'\b[a-zA-Z]\w*(?:_\w+)?\b', formula)
    reserved = ['sqrt', 'log', 'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'asin', 'acos', 'atan',
                'sinh', 'cosh', 'tanh', 'exp', 'Sum', 'Limit', 'Integral', 'Derivative', 'oo', 'pi', 'e']
    for var in variables:
        if var not in local_dict and var not in reserved:
            local_dict[var] = sp.Symbol(var)
    return local_dict

# Function to update LaTeX from formula
def update_latex():
    if st.session_state.manual_edit:
        return  # Do not overwrite LaTeX in manual edit mode
    if st.session_state.subscript_trigger:
        return  # Skip update during subscript application
    formula = st.session_state.formula
    valid, error_msg = is_valid_formula(formula)
    if not valid:
        st.session_state.latex = f"Invalid formula: {error_msg}"
        st.error(error_msg)
        return
    try:
        # Replace ^ with ** for exponentiation
        parsed_formula = formula.replace("^", "**")
        local_dict = get_locals(parsed_formula)
        expr = parse_expr(parsed_formula, local_dict=local_dict, transformations=standard_transformations)
        latex_str = sp.latex(expr, order='none')
        latex_str = re.sub(r'\\frac\{d\}\{d x\}\s*([a-zA-Z])', r'\\frac{d\1}{dx}', latex_str)
        latex_str = re.sub(r'\\frac\{d\}\{d x\}\s*\\left\(([^)]+)\\right\)', r'\\frac{d(\\1)}{dx}', latex_str)
        st.session_state.latex = latex_str
    except Exception as e:
        error_msg = str(e).lower()
        if 'syntax' in error_msg or 'invalid' in error_msg or 'expected' in error_msg:
            if '_' in formula:
                error_msg = f"Parsing error (likely subscript issue): {str(e)}. Tip: Use simple _sub (e.g., x_1), avoid complex nesting."
            else:
                error_msg = f"Parsing error: {str(e)}. Check for typos in functions/operators."
        else:
            error_msg = f"Unexpected error: {str(e)}"
        st.session_state.latex = f"Invalid formula: {error_msg}"
        st.error(error_msg)

# Function to sync LaTeX back to formula (heuristic for sub/superscripts)
def sync_latex_to_formula():
    latex = st.session_state.latex
    if not latex or latex.startswith("Invalid"):
        st.warning("No valid LaTeX to sync.")
        return
    # Simple replacements: x_{1} -> x_1, x^{2} -> x^2, etc. (basic heuristic, not full parser)
    formula_approx = re.sub(r'([a-zA-Z])_\{([^}]+)\}', r'\1_\2', latex)
    formula_approx = re.sub(r'([a-zA-Z])\{([^}]+)\}', r'\1\2', formula_approx)  # Remove extra braces
    formula_approx = re.sub(r'\^(\{?)([^}]+)(\}?)', r'^\2', formula_approx)  # ^2 or ^{2} -> ^2
    formula_approx = formula_approx.replace(r'\mathrm{', '').replace(r'}', '').replace(r'\\', '')  # Strip common LaTeX
    # Replace ** back if needed, but keep simple
    st.session_state.formula = formula_approx
    st.rerun()

# Cached function to create image from LaTeX
@lru_cache(maxsize=100)
def latex_to_image(latex_str):
    try:
        # Dynamic sizing based on length
        char_count = len(latex_str)
        fontsize = min(20, max(12, 20 - char_count // 10))
        temp_fig = plt.figure(figsize=(10, 2))
        temp_ax = temp_fig.add_subplot(111)
        temp_ax.axis('off')
        t = temp_ax.text(0.5, 0.5, f'${latex_str}$', fontsize=fontsize, ha='center', va='center')
        temp_fig.canvas.draw()
        bbox = t.get_window_extent(temp_fig.canvas.get_renderer())
        bbox_inches = bbox.transformed(temp_fig.dpi_scale_trans.inverted())
        plt.close(temp_fig)
        
        width = max(bbox_inches.width + 0.3, 4)
        height = max(bbox_inches.height + 0.2, 1)
        fig = plt.figure(figsize=(width, height))
        fig.patch.set_facecolor('white')
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', fontsize=fontsize, ha='center', va='center')
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.05, facecolor='white')
        plt.close(fig)
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode()
        return img_b64
    except Exception as e:
        st.error(f"Image generation error: {str(e)}")
        return None

# Function to append text to formula
def append_to_formula(text):
    st.session_state.temp_formula = st.session_state.formula + text
    st.session_state.formula = st.session_state.temp_formula
    update_latex()

# Function to get parameters from formula
def get_parameters(formula):
    return re.findall(r'\b[a-zA-Z]\w*(?:_\w+)?\b', formula)

# Function to add subscript to selected parameter
def add_subscript(subscript, selected_param):
    if not subscript.strip():
        st.error("Subscript cannot be empty.")
        return
    if not re.match(r'^[\w\d]+$', subscript):
        st.error("Subscript must be alphanumeric.")
        return
    formula = st.session_state.formula
    if not formula.strip():
        st.error("Formula is empty. Enter a parameter to subscript.")
        return
    if '{' in formula or '}' in formula:
        st.error("Formula contains LaTeX braces. Clear and re-enter using SymPy syntax.")
        return
    # Replace all occurrences of the selected parameter with subscripted version
    st.session_state.subscript_trigger = True
    new_formula = re.sub(r'\b' + re.escape(selected_param) + r'\b', f"{selected_param}_{subscript}", formula)
    st.session_state.temp_formula = new_formula
    st.session_state.formula = new_formula
    st.session_state.subscript_trigger = False
    update_latex()

# UI
st.title("Formula to LaTeX Converter")

st.info("💡 **Tip**: Use SymPy syntax in the formula field (e.g., `x_1 + y^2`). For LaTeX-style edits like `x_{1}`, use the manual LaTeX field below.")

# Formula input
st.text_input("Enter formula (e.g., x^2 + sqrt(y))", key="formula", value=st.session_state.formula, on_change=update_latex)

# Manual edit checkbox
st.checkbox("Edit LaTeX manually (prevents automatic updates from formula)", key="manual_edit")

# Sync button for LaTeX -> formula
if st.button("Sync LaTeX back to Formula (approximate)"):
    sync_latex_to_formula()

# Subscript input
st.write("Add subscript to a parameter:")
parameters = get_parameters(st.session_state.formula)
if parameters:
    selected_param = st.selectbox("Select parameter to subscript:", parameters)
    subscript_input = st.text_input("Enter subscript (e.g., 1, oil, gas)", key="subscript_input")
    if st.button("Apply Subscript", key="apply_subscript"):
        add_subscript(subscript_input, selected_param)
else:
    st.write("No parameters found in formula.")

# Reset button
if st.button("Reset Formula"):
    st.session_state.formula = ""
    st.session_state.latex = ""
    st.session_state.temp_formula = ""
    st.session_state.subscript_trigger = False
    st.session_state.manual_edit = False
    st.rerun()

# Symbol selection
st.write("Math tools:")
tab_names = ["Basic", "Brackets", "Trigonometry", "Hyperbolic", "Calculus", "Constants", "Greek", "Engineering", "Petroleum"]
tabs = st.tabs(tab_names)

# Define symbol options for radio buttons
symbols_basic = [
    ("√", "sqrt()"), ("log", "log()"), ("exp", "exp()"),
    ("÷", "/"), ("×", "*"), ("^", "^"), ("_", "_"), ("+", "+"), ("-", "-")
]
symbols_brackets = [
    ("(", "("), (")", ")"), ("[", "["), ("]", "]"), ("{", "{"), ("}", "}")
]
symbols_trig = [
    ("sin", "sin()"), ("cos", "cos()"), ("tan", "tan()"), ("cot", "cot()"),
    ("sec", "sec()"), ("csc", "csc()"), ("asin", "asin()"), ("acos", "acos()"), ("atan", "atan()")
]
symbols_hyperbolic = [
    ("sinh", "sinh()"), ("cosh", "cosh()"), ("tanh", "tanh()")
]
symbols_calculus = [
    ("∫", "Integral(, x)"), ("d/dx", "Derivative(, x)"),
    ("∑", "Sum(, (n, 0, oo))"), ("lim", "Limit(, x, 0)")
]
symbols_constants = [
    ("π", "pi"), ("e", "e"), ("∞", "oo")
]
symbols_greek = [
    ("α", "alpha"), ("β", "beta"), ("γ", "gamma"), ("δ", "delta"), ("Δ", "Delta"),
    ("ε", "epsilon"), ("ζ", "zeta"), ("η", "eta"), ("θ", "theta"), ("Θ", "Theta"),
    ("ι", "iota"), ("κ", "kappa"), ("λ", "lambda"), ("Λ", "Lambda"), ("μ", "mu"),
    ("ν", "nu"), ("ξ", "xi"), ("π", "pi"), ("ρ", "rho"), ("σ", "sigma"),
    ("Σ", "Sigma"), ("τ", "tau"), ("φ", "phi"), ("Φ", "Phi"), ("ω", "omega"), ("Ω", "Omega")
]
symbols_engineering = [
    ("Ω (ohm)", "Omega"), ("µ (micro)", "mu"), ("° (degree)", "degree"),
    ("≈", "approx"), ("≠", "ne"), ("≥", "ge"), ("≤", "le")
]
symbols_petroleum = [
    ("φ (porosity)", "phi"), ("κ (permeability)", "kappa"), ("μ (viscosity)", "mu"),
    ("ρ (density)", "rho"), ("P (pressure)", "P"), ("Q (flow rate)", "Q")
]

# Map tabs to symbol lists
symbol_lists = [
    symbols_basic, symbols_brackets, symbols_trig, symbols_hyperbolic,
    symbols_calculus, symbols_constants, symbols_greek, symbols_engineering, symbols_petroleum
]

# Display radio buttons in each tab
for idx, tab in enumerate(tabs):
    with tab:
        selected_symbol = st.radio(
            f"Select a {tab_names[idx].lower()} symbol/function:",
            options=[label for label, _ in symbol_lists[idx]],
            key=f"radio_{tab_names[idx].lower()}_{idx}",
            horizontal=True
        )
        if selected_symbol:
            for label, text in symbol_lists[idx]:
                if label == selected_symbol:
                    st.button(f"Insert {label}", key=f"btn_{tab_names[idx].lower()}_{text}_{idx}", on_click=partial(append_to_formula, text))
                    break

# LaTeX output
st.text_input("LaTeX version", key="latex", on_change=lambda: st.rerun() if st.session_state.manual_edit else None)

# Render LaTeX and copy buttons
st.write("Rendered:")
if st.session_state.latex and not st.session_state.latex.startswith("Invalid formula"):
    try:
        st.latex(st.session_state.latex)
        img_b64 = latex_to_image(st.session_state.latex)
        copy_js = """
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
                if (!window.MathJax || !window.MathJax.tex2mmlPromise) {
                    throw new Error('MathJax not loaded');
                }
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
            if (!window.ClipboardItem) {
                button.style.backgroundColor = '#ff0000';
                button.innerText = 'Not Supported';
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
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js" onerror="console.error('MathJax failed to load')"></script>
        """
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
