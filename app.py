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
if "subscript_mode" not in st.session_state:
    st.session_state.subscript_mode = False  # Default: off

# --- Helper: Validate formula ---
def is_valid_formula(formula):
    if not formula.strip():
        return False, "Formula is empty."
    if formula.strip()[-1] in ['+', '-', '*', '/', '^', '_']:
        return False, "Formula ends with an incomplete operator or subscript."
    if formula.count('(') != formula.count(')'):
        return False, "Unbalanced parentheses."
    if re.search(r'_\b', formula):  # Check for dangling underscore
        return False, "Incomplete subscript (e.g., 'x_' without a subscript value)."
    return True, ""

# --- Function: Update LaTeX from formula ---
def update_latex():
    formula = st.session_state.formula.strip()
    valid, error_msg = is_valid_formula(formula)
    if not valid:
        st.session_state.latex = f"Invalid formula: {error_msg}"
        st.error(error_msg)
        return

    # Auto-detect LaTeX input
    if formula.startswith("\\") or re.search(r"\\frac|\\int|\\sqrt|\\left", formula):
        st.session_state.latex = formula
        return

    try:
        # Step 1: Find all subscript variables (e.g., x_2, var_name)
        subscript_pattern = r'\b([a-zA-Z]+)_([a-zA-Z0-9]+)\b'
        subscript_vars = set(re.findall(subscript_pattern, formula))
        
        # Step 2: Create SymPy symbols with underscores directly
        local_dict = {
            "sp": sp,
            "sqrt": sp.sqrt,
            "log": sp.log,
            "sin": sp.sin,
            "cos": sp.cos,
            "tan": sp.tan,
            "exp": sp.exp
        }
        
        for base, subscript in subscript_vars:
            var_name = f"{base}_{subscript}"
            local_dict[var_name] = sp.Symbol(var_name)
        
        # Step 3: Handle equations with '='
        if '=' in formula:
            left, right = [part.strip() for part in formula.split('=', 1)]
            # Replace ^ with ** for SymPy parsing
            left_parsed = left.replace("^", "**")
            right_parsed = right.replace("^", "**")
            
            transformations = standard_transformations + (
                implicit_multiplication_application,
                convert_xor
            )
            
            # Parse both sides
            left_expr = parse_expr(left_parsed, local_dict=local_dict, transformations=transformations)
            right_expr = parse_expr(right_parsed, local_dict=local_dict, transformations=transformations)
            
            # Combine into LaTeX equation
            latex_str = f"{sp.latex(left_expr, order='none')} = {sp.latex(right_expr, order='none')}"
        else:
            # Original parsing for non-equations
            parsed_formula = formula.replace("^", "**")
            expr = parse_expr(parsed_formula, local_dict=local_dict, transformations=transformations)
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

# --- Function: Append text to formula ---
def append_to_formula(text):
    if text == "_" and not st.session_state.subscript_mode:
        return  # Do nothing if subscript mode is off
    st.session_state.formula += text
    update_latex()

# --- Function: Toggle subscript mode ---
def toggle_subscript_mode():
    st.session_state.subscript_mode = not st.session_state.subscript_mode

# --- UI ---
st.title("Formula ↔ LaTeX Converter")

st.text_input("Enter formula (e.g., x^2 + sqrt(y) or x_2 for subscripts)", key="formula", on_change=update_latex)

st.write("Math tools:")
cols = st.columns(9)
buttons = [
    ("√", "sqrt()"),
    ("÷", "/"),
    ("∫", "Integral(1, x)"),
    ("d/dx", "Derivative(1, x)"),
    ("log", "log()"),
    ("×", "*"),
    ("^", "^"),
    ("ₓ Sub", "toggle_subscript"),  # Special handling for subscript
    ("=", "=")
]

# Custom CSS for subscript button colors
st.markdown("""
    <style>
    .subscript-on {
        background-color: #00c853 !important;
        color: white !important;
    }
    .subscript-off {
        background-color: #ff1744 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

for i, (label, text) in enumerate(buttons):
    with cols[i]:
        if label == "ₓ Sub":
            # Display button with dynamic class based on subscript_mode
            button_class = "subscript-on" if st.session_state.subscript_mode else "subscript-off"
            button_label = "ₓ Sub (ON)" if st.session_state.subscript_mode else "ₓ Sub (OFF)"
            st.button(button_label, on_click=toggle_subscript_mode, key=f"button_{i}", help="Toggle subscript mode")
            # Inject CSS to style this specific button
            st.markdown(f"""
                <script>
                document.querySelector('button[kind="secondary"][aria-label="Toggle subscript mode"]').classList.add('{button_class}');
                </script>
            """, unsafe_allow_html=True)
        else:
            st.button(label, on_click=partial(append_to_formula, text), key=f"button_{i}")

st.text_input("LaTeX version", key="latex")

st.write("Rendered:")

if st.session_state.latex and not st.session_state.latex.startswith("Invalid formula"):
    try:
        st.latex(st.session_state.latex)
        img_b64 = latex_to_image(st.session_state.latex)

        # JS + HTML block
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
