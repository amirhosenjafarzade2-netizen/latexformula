import streamlit as st
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations
from functools import lru_cache
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
if "mode" not in st.session_state:
    st.session_state.mode = "SymPy"
if "history" not in st.session_state:
    st.session_state.history = []

# Validate formula
def is_valid_formula(formula):
    if not formula.strip():
        return False, "Formula is empty."
    if formula.strip()[-1] in ['+', '-', '*', '/', '^', '_']:
        return False, "Formula ends with an incomplete operator."
    if st.session_state.mode == "SymPy" and ('{' in formula or '}' in formula):
        return False, "LaTeX braces {} not allowed in SymPy mode. Use _sub (e.g., x_1)."
    incomplete_functions = ['sqrt(', 'log(', 'Integral(', 'Derivative(', 'Sum(', 'Limit(', 'sin(', 'cos(', 'tan(', 'cot(', 'sec(', 'csc(', 'asin(', 'acos(', 'atan(', 'sinh(', 'cosh(', 'tanh(', 'exp(']
    for func in incomplete_functions:
        if formula.strip().endswith(func):
            return False, f"Incomplete function call: '{func}' is missing arguments."
    if formula.count('(') != formula.count(')'):
        return False, "Unbalanced parentheses in formula."
    if formula.count('{') != formula.count('}'):
        return False, "Unbalanced LaTeX braces."
    if re.search(r',\s*,', formula):
        return False, "Invalid function arguments: consecutive commas detected."
    if re.search(r'\(\s*,', formula):
        return False, "Invalid function arguments: empty argument detected."
    if re.search(r'(Integral|Derivative)\(\s*,\s*\w+\s*\)', formula):
        return False, "Integral/Derivative is missing the function to integrate/differentiate."
    return True, ""

# Get locals with automatic symbol declaration
def get_locals(formula):
    local_dict = {
        "sp": sp, "sqrt": sp.sqrt, "log": sp.log, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
        "cot": sp.cot, "sec": sp.sec, "csc": sp.csc, "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
        "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh, "exp": sp.exp, "Sum": sp.Sum,
        "Limit": sp.Limit, "Integral": sp.Integral, "Derivative": sp.Derivative, "oo": sp.oo,
        "pi": sp.pi, "e": sp.E, "phi": sp.Symbol('phi'), "kappa": sp.Symbol('kappa'),
        "mu": sp.Symbol('mu'), "alpha": sp.Symbol('alpha'), "beta": sp.Symbol('beta'),
        "gamma": sp.Symbol('gamma'), "delta": sp.Symbol('delta'), "Delta": sp.Symbol('Delta'),
        "epsilon": sp.Symbol('epsilon'), "zeta": sp.Symbol('zeta'), "eta": sp.Symbol('eta'),
        "theta": sp.Symbol('theta'), "Theta": sp.Symbol('Theta'), "iota": sp.Symbol('iota'),
        "lambda": sp.Symbol('lambda'), "Lambda": sp.Symbol('Lambda'), "nu": sp.Symbol('nu'),
        "xi": sp.Symbol('xi'), "rho": sp.Symbol('rho'), "sigma": sp.Symbol('sigma'),
        "Sigma": sp.Symbol('Sigma'), "tau": sp.Symbol('tau'), "Phi": sp.Symbol('Phi'),
        "omega": sp.Symbol('omega'), "Omega": sp.Symbol('Omega'), "degree": sp.Symbol('degree'),
        "approx": sp.Symbol('approx'), "ne": sp.Symbol('ne'), "ge": sp.Symbol('ge'), "le": sp.Symbol('le')
    }
    variables = re.findall(r'\b[a-zA-Z]\w*(?:_\w+)?\b', formula)
    reserved = ['sqrt', 'log', 'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'asin', 'acos', 'atan',
                'sinh', 'cosh', 'tanh', 'exp', 'Sum', 'Limit', 'Integral', 'Derivative', 'oo', 'pi', 'e']
    for var in variables:
        if var not in local_dict and var not in reserved:
            symbol = sp.Symbol(var)
            if '_' in var and st.session_state.mode == "LaTeX":
                base, subscript = var.split('_', 1)
                symbol._latex_repr = f"{base}_{{{subscript}}}"
            local_dict[var] = symbol
    return local_dict

# Update LaTeX
def update_latex():
    if st.session_state.subscript_trigger:
        return
    formula = st.session_state.formula
    if st.session_state.mode == "LaTeX":
        st.session_state.latex = formula
        return
    valid, error_msg = is_valid_formula(formula)
    if not valid:
        st.session_state.latex = f"Invalid formula: {error_msg}"
        st.error(error_msg)
        return
    try:
        parsed_formula = formula.replace("^", "**")
        local_dict = get_locals(parsed_formula)
        expr = parse_expr(parsed_formula, local_dict=local_dict, transformations=standard_transformations)
        latex_str = sp.latex(expr, order='none')
        latex_str = re.sub(r'\\frac\{d\}\{d x\}\s*([a-zA-Z])', r'\\frac{d\1}{dx}', latex_str)
        latex_str = re.sub(r'\\frac\{d\}\{d x\}\s*\\left\(([^)]+)\\right\)', r'\\frac{d(\\1)}{dx}', latex_str)
        st.session_state.latex = latex_str
        st.session_state.history.append((formula, latex_str))
        if len(st.session_state.history) > 10:
            st.session_state.history.pop(0)
    except Exception as e:
        st.session_state.latex = f"Invalid formula: {str(e)}"
        st.error(str(e))

# LaTeX to SymPy
def sync_to_sympy():
    latex = st.session_state.latex
    if not latex or st.session_state.mode != "LaTeX":
        st.warning("Switch to LaTeX mode first.")
        return
    sympy_approx = re.sub(r'([a-zA-Z])_\{([^}]+)\}', r'\1_\2', latex)
    sympy_approx = re.sub(r'\^(\{?)([^}]+)(\}?)', r'^\2', sympy_approx)
    sympy_approx = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', sympy_approx)
    sympy_approx = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\1)', sympy_approx)
    sympy_approx = re.sub(r'\\sin\{([^}]+)\}', r'sin(\1)', sympy_approx)
    sympy_approx = re.sub(r'\\cos\{([^}]+)\}', r'cos(\1)', sympy_approx)
    sympy_approx = re.sub(r'\\sum_\{([^}]+)\}\^\{([^}]+)\}', r'sum(\1,\2)', sympy_approx)
    st.session_state.formula = sympy_approx
    st.session_state.mode = "SymPy"
    st.rerun()

# LaTeX to image
@lru_cache(maxsize=100)
def latex_to_image(latex_str):
    try:
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
        return base64.b64encode(buf.read()).decode()
    except Exception as e:
        st.error(f"Image generation error: {str(e)}")
        return None

# LaTeX to PDF
def latex_to_pdf(latex_str):
    try:
        fig = plt.figure(figsize=(8, 2))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', ha='center', va='center', fontsize=18)
        buf = BytesIO()
        plt.savefig(buf, format='pdf', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        return None

# Append to formula
def append_to_formula(text):
    temp_formula = st.session_state.formula
    if st.session_state.mode == "LaTeX":
        temp_formula += text
    else:
        text = text.replace('_{}', '_').replace('^{}', '^')
        temp_formula += text
    st.session_state.temp_formula = temp_formula
    st.session_state.formula = temp_formula
    update_latex()

# Add subscript
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
    param_positions = [m.start() for m in re.finditer(r'\b' + re.escape(selected_param) + r'\b', formula)]
    if param_positions:
        last_pos = param_positions[-1]
        st.session_state.subscript_trigger = True
        new_formula = formula[:last_pos] + f"{selected_param}_{subscript}" + formula[last_pos + len(selected_param):]
        st.session_state.temp_formula = new_formula
        st.session_state.formula = new_formula
        st.session_state.subscript_trigger = False
        update_latex()
    else:
        st.error("Selected parameter not found in formula.")

# UI
st.title("Formula to LaTeX Converter")

# Mode and sync
col1, col2 = st.columns([3, 1])
with col2:
    st.session_state.mode = st.selectbox("Mode:", ["SymPy (parseable)", "LaTeX (direct)"], index=0 if st.session_state.mode == "SymPy" else 1)
    if st.button("Sync LaTeX → SymPy", key="sync_btn"):
        sync_to_sympy()
    if st.button("View History", key="history_btn"):
        st.write("Recent Formulas:", st.session_state.history)

# Formula input and subscript
st.text_input("Enter formula (e.g., x^2 + sqrt(y))", key="formula", on_change=update_latex)
parameters = re.findall(r'\b[a-zA-Z]\w*(?:_\w+)?\b', st.session_state.formula)
if parameters:
    st.write("Add subscript to a parameter:")
    selected_param = st.selectbox("Select parameter:", parameters, key="param_select")
    subscript_input = st.text_input("Enter subscript (e.g., 1, oil)", key="subscript_input")
    if st.button("Apply Subscript", key="apply_subscript"):
        add_subscript(subscript_input, selected_param)

# Tabs
tab_names = ["Basic", "Brackets", "Trigonometry", "Hyperbolic", "Calculus", "Constants", "Greek", "Engineering", "Petroleum", "Matrices", "Chemistry", "Physics"]
tabs = st.tabs(tab_names)

# Symbol definitions
symbols_basic = [
    ("√", "sqrt()"), ("log", "log()"), ("exp", "exp()"), ("÷", "/"), ("×", "*"),
    ("^", "^{}" if st.session_state.mode == "LaTeX" else "^"), ("_", "_{}" if st.session_state.mode == "LaTeX" else "_"),
    ("+", "+"), ("-", "-")
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
symbols_calculus = {
    "∫": "Integral(, x)" if st.session_state.mode == "SymPy" else "\\int_{}^{} \\, dx",
    "∑": "Sum(, (n, 0, oo))" if st.session_state.mode == "SymPy" else "\\sum_{}^{}",
    "lim": "Limit(, x, 0)" if st.session_state.mode == "SymPy" else "\\lim_{x \\to }",
    "d/dx": "Derivative(, x)" if st.session_state.mode == "SymPy" else "\\frac{d}{dx}",
    "∂": "\\partial"
}
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

# Display symbols
symbol_lists = [
    symbols_basic, symbols_brackets, symbols_trig, symbols_hyperbolic, symbols_calculus,
    symbols_constants, symbols_greek, symbols_engineering, symbols_petroleum
]
for idx, tab in enumerate(tabs[:9]):  # Basic to Petroleum
    with tab:
        symbols = symbol_lists[idx]
        num_cols = min(5, len(symbols))  # Adjust columns dynamically to avoid empty placeholders
        cols = st.columns(num_cols) if num_cols > 0 else [st]
        if tab_names[idx] == "Calculus":
            for i, (label, text) in enumerate(symbols_calculus.items()):
                col_idx = i % num_cols
                with cols[col_idx]:
                    if st.button(label, key=f"btn_{tab_names[idx]}_{i}"):
                        append_to_formula(text)
        else:
            for i, (label, text) in enumerate(symbols):
                col_idx = i % num_cols
                with cols[col_idx]:
                    if st.button(label, key=f"btn_{tab_names[idx]}_{i}"):
                        append_to_formula(text)

# Matrices
with tabs[9]:
    with st.expander("Insert Matrix"):
        matrix_type = st.selectbox("Matrix Type", ["pmatrix", "bmatrix", "vmatrix", "Bmatrix"], key="matrix_type")
        rows = st.number_input("Rows", 1, 5, 2, key="matrix_rows")
        cols = st.number_input("Cols", 1, 5, 2, key="matrix_cols")
        elements = []
        for i in range(rows):
            row = []
            for j in range(cols):
                row.append(st.text_input(f"Element [{i+1},{j+1}]", key=f"matrix_{i}_{j}"))
            elements.append(row)
        if st.button("Insert Matrix", key="insert_matrix"):
            matrix_content = " \\\\ ".join(" & ".join(row) for row in elements if any(row))
            matrix = f"\\begin{{{matrix_type}}} {matrix_content} \\end{{{matrix_type}}}"
            append_to_formula(matrix)

# Chemistry
with tabs[10]:
    with st.expander("Chemistry (\\ce{})"):
        cols = st.columns(3)
        chem = ["\\ce{H2O}", "\\ce{CO2}", "\\ce{A -> B}", "\\ce{A + B <=> C}", "\\ce{H2SO4}"]
        for i, c in enumerate(chem):
            with cols[i % 3]:
                if st.button(c, key=f"chem_btn_{i}"):
                    append_to_formula(c)
        custom_chem = st.text_input("Custom \\ce{}", key="custom_chem")
        if st.button("Insert Custom Chemistry", key="insert_chem"):
            append_to_formula(f"\\ce{{{custom_chem}}}")

# Physics
with tabs[11]:
    with st.expander("Physics (\\dv, \\grad, etc.)"):
        cols = st.columns(3)
        physics = ["\\dv{f}{x}", "\\grad{\\psi}", "\\curl{\\mathbf{A}}", "\\div{\\mathbf{F}}", "\\pdv{f}{x,y}"]
        for i, p in enumerate(physics):
            with cols[i % 3]:
                if st.button(p, key=f"physics_btn_{i}"):
                    append_to_formula(p)
        custom_deriv = st.text_input("Custom Derivative (e.g., f,x)", placeholder="function,variable", key="custom_deriv")
        if st.button("Insert Custom Derivative", key="insert_deriv"):
            if "," in custom_deriv:
                f, x = custom_deriv.split(",", 1)
                append_to_formula(f"\\dv{{{f}}}{{{x}}}")

# Output
st.text_area("LaTeX Output:", st.session_state.latex, key="latex_out", height=100)

# Preview
st.write("Preview:")
img_b64 = None  # Initialize to avoid NameError
if st.session_state.latex and not st.session_state.latex.startswith("Invalid") and not st.session_state.latex.startswith("Parse error"):
    st.latex(st.session_state.latex)
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
    <div id="mathjax-preview">$${st.session_state.latex}$</div>
    <script>MathJax.typeset();</script>
    """
    img_b64 = latex_to_image(st.session_state.latex)
    if img_b64:
        html_content += f"""
        <img id="latex-image" src="data:image/png;base64,{img_b64}" style="max-width: 100%; margin-top: 10px;" />
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
else:
    st.info("Enter a valid formula to see the LaTeX rendering.")

# Export
col1, col2 = st.columns(2)
with col1:
    if img_b64:
        if st.button("Download Image", key="download_img"):
            st.download_button("Download PNG", data=base64.b64decode(img_b64), file_name="equation.png", mime="image/png", key="download_png")
with col2:
    pdf_b64 = latex_to_pdf(st.session_state.latex)
    if pdf_b64:
        if st.button("Download PDF", key="download_pdf"):
            st.download_button("Download PDF", data=base64.b64decode(pdf_b64), file_name="equation.pdf", mime="application/pdf", key="download_pdf_btn")

# Reset and undo
col1, col2 = st.columns(2)
with col1:
    if st.button("Reset", key="reset_btn"):
        for key in ["formula", "latex", "temp_formula"]:
            setattr(st.session_state, key, "")
        st.session_state.subscript_trigger = False
        st.rerun()
with col2:
    if st.button("Undo", key="undo_btn") and st.session_state.history:
        st.session_state.formula, st.session_state.latex = st.session_state.history[-1]
        st.session_state.history.pop(-1)
        st.rerun()
