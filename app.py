import streamlit as st
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
)
from functools import partial
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
import streamlit.components.v1 as components
import re

matplotlib.use('Agg')

# --- Initialize session state ---
if "formula" not in st.session_state:
    st.session_state.formula = ""
if "latex" not in st.session_state:
    st.session_state.latex = ""
if "cursor_pos" not in st.session_state:
    st.session_state.cursor_pos = 0

# --- Helper: Validate formula ---
def is_valid_formula(formula):
    if not formula.strip():
        return False, "Formula is empty."
    if formula.strip()[-1] in ['+', '-', '*', '/', '^']:
        return False, "Formula ends with an incomplete operator."
    if formula.count('(') != formula.count(')'):
        return False, "Unbalanced parentheses."
    return True, ""

# --- Function: Insert text at cursor position ---
def insert_at_cursor(text):
    cursor_pos = st.session_state.cursor_pos
    formula = st.session_state.formula
    st.session_state.formula = formula[:cursor_pos] + text + formula[cursor_pos:]
    st.session_state.cursor_pos = cursor_pos + len(text)
    update_latex()

# --- Function: Update cursor position ---
def update_cursor_pos():
    try:
        # Streamlit doesn't provide direct cursor position; approximate using input length
        st.session_state.cursor_pos = len(st.session_state.formula)
    except:
        st.session_state.cursor_pos = 0

# --- Function: Update LaTeX from formula ---
def update_latex():
    formula = st.session_state.formula.strip()
    valid, error_msg = is_valid_formula(formula)
    if not valid:
        st.session_state.latex = f"Invalid formula: {error_msg}"
        st.error(error_msg)
        return

    # Auto-detect if already LaTeX
    if formula.startswith("\\") or re.search(r"\\frac|\\int|\\sqrt|\\left|\\sum", formula):
        st.session_state.latex = formula
        return

    try:
        # Step 1: Define local dictionary with all symbols
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
            # Petroleum engineering symbols
            "porosity": sp.Symbol('phi'),
            "permeability": sp.Symbol('kappa'),
            "tension": sp.Symbol('sigma_t'),
            "shear_stress": sp.Symbol('tau_s'),
            "shear_rate": sp.Symbol('gamma_dot')
        }

        # Step 2: Handle subscripted variables
        subscript_pattern = r'\b([a-zA-Z]+)_([a-zA-Z0-9]+)\b'
        subscript_vars = set(re.findall(subscript_pattern, formula))
        for base, subscript in subscript_vars:
            var_name = f"{base}_{subscript}"
            if var_name not in local_dict:
                local_dict[var_name] = sp.Symbol(var_name)

        # Step 3: Replace ^ with ** for exponentiation
        parsed_formula = formula.replace("^", "**")

        # Step 4: Detect if there's an '=' (equation)
        if "=" in parsed_formula:
            lhs, rhs = parsed_formula.split("=", 1)
            transformations = standard_transformations + (
                implicit_multiplication_application,
                convert_xor
            )
            lhs_expr = parse_expr(lhs.strip(), local_dict=local_dict, transformations=transformations)
            rhs_expr = parse_expr(rhs.strip(), local_dict=local_dict, transformations=transformations)
            expr = sp.Eq(lhs_expr, rhs_expr)
        else:
            transformations = standard_transformations + (
                implicit_multiplication_application,
                convert_xor
            )
            expr = parse_expr(parsed_formula, local_dict=local_dict, transformations=transformations)

        # Step 5: Convert to LaTeX
        latex_str = sp.latex(expr, order='none')
        st.session_state.latex = latex_str

    except Exception as e:
        st.session_state.latex = f"Invalid formula: {str(e)}"
        st.error(f"Invalid formula: {str(e)}")

# --- Function: Convert LaTeX to image ---
def latex_to_image(latex_str):
    try:
        fig = plt.figure(figsize=(10, 2))
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', fontsize=20, ha='center', va='center')
        fig.canvas.draw()
        bbox = ax.get_window_extent(fig.canvas.get_renderer())
        bbox_inches = bbox.transformed(fig.dpi_scale_trans.inverted())
        plt.close(fig)

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

# --- UI ---
st.title("Formula ↔ LaTeX Converter")

# Custom CSS for better styling
st.markdown("""
    <style>
    .symbol-button {
        background-color: #f0f2f6;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 8px 12px;
        margin: 2px;
        font-size: 14px;
        cursor: pointer;
    }
    .symbol-button:hover {
        background-color: #e5e7eb;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 16px;
        padding: 10px 20px;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #0f80c1;
    }
    </style>
""", unsafe_allow_html=True)

# Text input with cursor tracking
st.text_input("Enter formula (e.g., x^2 + sqrt(y_1) or porosity = kappa)", key="formula", on_change=update_cursor_pos)

# Tabbed interface for symbol groups
tab1, tab2, tab3, tab4 = st.tabs(["Mathematical Symbols", "Greek Characters", "Engineering Symbols", "Petroleum Engineering"])

# Button groups
button_groups = {
    "Mathematical Symbols": [
        ("√", "sqrt()"),
        ("÷", "/"),
        ("×", "*"),
        ("^", "^"),
        ("=", "="),
        ("∫", "Integral(1, x)"),
        ("d/dx", "Derivative(1, x)"),
        ("∑", "Sum(1, x)"),
        ("lim", "Limit(1, x)"),
        ("log", "log()"),
        ("sin", "sin()"),
        ("cos", "cos()"),
        ("tan", "tan()"),
        ("cot", "cot()"),
        ("sec", "sec()"),
        ("csc", "csc()"),
        ("asin", "asin()"),
        ("acos", "acos()"),
        ("atan", "atan()"),
        ("sinh", "sinh()"),
        ("cosh", "cosh()"),
        ("tanh", "tanh()"),
        ("exp", "exp()"),
        ("π", "pi"),
        ("e", "e")
    ],
    "Greek Characters": [
        ("α", "alpha"),
        ("β", "beta"),
        ("γ", "gamma"),
        ("Γ", "Gamma"),
        ("δ", "delta"),
        ("Δ", "Delta"),
        ("ε", "epsilon"),
        ("ζ", "zeta"),
        ("η", "eta"),
        ("θ", "theta"),
        ("Θ", "Theta"),
        ("ι", "iota"),
        ("λ", "lambda"),
        ("Λ", "Lambda"),
        ("μ", "mu"),
        ("ν", "nu"),
        ("ξ", "xi"),
        ("ρ", "rho"),
        ("σ", "sigma"),
        ("Σ", "Sigma"),
        ("τ", "tau"),
        ("φ", "phi"),
        ("Φ", "Phi"),
        ("ω", "omega"),
        ("Ω", "Omega")
    ],
    "Engineering Symbols": [
        ("°", "degree"),
        ("≈", "approx"),
        ("≠", "ne"),
        ("≥", "ge"),
        ("≤", "le"),
        ("σ", "sigma"),
        ("τ", "tau"),
        ("E", "E"),
        ("μ", "mu")
    ],
    "Petroleum Engineering": [
        ("φ (porosity)", "porosity"),
        ("κ (permeability)", "permeability"),
        ("σ_t (tension)", "tension"),
        ("τ_s (shear stress)", "shear_stress"),
        ("γ̇ (shear rate)", "shear_rate")
    ]
}

# Render buttons for each tab
for tab, group_name in [(tab1, "Mathematical Symbols"), (tab2, "Greek Characters"), 
                        (tab3, "Engineering Symbols"), (tab4, "Petroleum Engineering")]:
    with tab:
        cols = st.columns(5)  # 5 buttons per row
        for i, (label, text) in enumerate(button_groups[group_name]):
            with cols[i % 5]:
                st.button(label, key=f"{group_name}_{i}", on_click=partial(insert_at_cursor, text), 
                          args=None, kwargs=None, help=f"Insert {text}", 
                          use_container_width=True, type="secondary")

# Update LaTeX after button clicks
update_latex()

st.text_input("LaTeX version", key="latex", disabled=True)

st.write("Rendered:")

if st.session_state.latex and not st.session_state.latex.startswith("Invalid formula"):
    try:
        st.latex(st.session_state.latex)
        img_b64 = latex_to_image(st.session_state.latex)

        # JS + HTML block for clipboard functionality
        copy_js = """
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
        <script>
        function copyLatexText() {
            const button = document.getElementById('copy-latex-btn');
            const latexCode = document.getElementById('latex-content').innerText;
            navigator.clipboard.writeText(latexCode).then(() => {
                button.style.backgroundColor = '#00c853';
                button.innerText = '✓ Copied!';
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
                button.style.backgroundColor = '#00c853';
                button.innerText = '✓ Copied!';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy for Word';
                }, 1500);
            } catch (err) {
                button.style.backgroundColor = '#ff1744';
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
                button.style.backgroundColor = '#ff1744';
                button.innerText = 'No Image';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy as Image';
                }, 1500);
                return;
            }
            try {
                const response = await fetch(imgElement.src);
                const blob = await response.blob();
                const clipboardItem = new ClipboardItem({ 'image/png': blob });
                await navigator.clipboard.write([clipboardItem]);
                button.style.backgroundColor = '#00c853';
                button.innerText = '✓ Copied!';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy as Image';
                }, 1500);
            } catch (err) {
                button.style.backgroundColor = '#ff1744';
                button.innerText = 'Failed';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy as Image';
                }, 1500);
            }
        }
        </script>
        """

        html_content = f"""
        {copy_js}
        <div style="max-height:500px; overflow-y:auto;">
            <div id="latex-content" style="display:none;">{st.session_state.latex}</div>
        """

        if img_b64:
            html_content += f"""
            <img id="latex-image" src="data:image/png;base64,{img_b64}" 
                 style="max-width: 100%; margin-top: 10px;" />
            """
        else:
            html_content += "<p style='color:red;'>No image available.</p>"

        html_content += """
            <div style="display:flex; gap:10px; margin-top:10px;">
                <button id="copy-latex-btn" onclick="copyLatexText()" 
                        style="background-color:#0f80c1;color:white;padding:10px 20px;
                               border:none;border-radius:4px;cursor:pointer;font-weight:bold;">
                    Copy LaTeX
                </button>
                <button id="copy-word-btn" onclick="copyForWord()" 
                        style="background-color:#0f80c1;color:white;padding:10px 20px;
                               border:none;border-radius:4px;cursor:pointer;font-weight:bold;">
                    Copy for Word
                </button>
                <button id="copy-image-btn" onclick="copyAsImage()" 
                        style="background-color:#0f80c1;color:white;padding:10px 20px;
                               border:none;border-radius:4px;cursor:pointer;font-weight:bold;">
                    Copy as Image
                </button>
            </div>
        </div>
        """

        dynamic_height = 400 + min(len(st.session_state.latex) // 10, 600)
        components.html(html_content, height=dynamic_height)
    except Exception as e:
        st.error(f"Unable to render LaTeX: {str(e)}")
else:
    st.write("Enter a valid formula to see the LaTeX rendering.")
