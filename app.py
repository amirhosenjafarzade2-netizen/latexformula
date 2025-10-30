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
if "latex_edited" not in st.session_state:
    st.session_state.latex_edited = False

# --- Helper: Validate formula ---
def is_valid_formula(formula):
    if not formula.strip():
        return False, "Formula is empty."
    if formula.strip()[-1] in ['+', '-', '*', '/', '^']:
        return False, "Formula ends with an incomplete operator."
    if formula.count('(') != formula.count(')'):
        return False, "Unbalanced parentheses."
    return True, ""

# --- Function: Insert text at end ---
def insert_text(text):
    st.session_state.formula = st.session_state.formula + text
    st.session_state.latex_edited = False
    update_latex()

# --- Function: Clear formula ---
def clear_formula():
    st.session_state.formula = ""
    st.session_state.latex = ""
    st.session_state.latex_edited = False

# --- Function: Update LaTeX from formula or LaTeX input ---
def update_latex():
    if st.session_state.latex_edited:
        # If LaTeX was edited, use it directly if valid
        latex_str = st.session_state.latex.strip()
        if latex_str and (latex_str.startswith("\\") or re.search(r"\\frac|\\int|\\sqrt|\\left|\\sum", latex_str)):
            try:
                # Basic validation: attempt to render LaTeX
                fig = plt.figure(figsize=(2, 1))
                ax = fig.add_subplot(111)
                ax.axis('off')
                ax.text(0.5, 0.5, f'${latex_str}$', fontsize=12)
                fig.canvas.draw()
                plt.close(fig)
                return  # LaTeX is valid, keep it
            except Exception as e:
                st.session_state.latex = f"Invalid LaTeX: {str(e)}"
                return
        else:
            st.session_state.latex = "Invalid LaTeX: Must be valid LaTeX syntax"
            return

    formula = st.session_state.formula.strip()
    valid, error_msg = is_valid_formula(formula)
    if not valid:
        if formula:  # Only show error if there's actual input
            st.session_state.latex = f"Invalid formula: {error_msg}"
        else:
            st.session_state.latex = ""
        return

    # Auto-detect if formula is LaTeX
    if formula and (formula.startswith("\\") or re.search(r"\\frac|\\int|\\sqrt|\\left|\\sum", formula)):
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
            "E": sp.E,
            "phi": sp.Symbol(r'\phi'),
            "kappa": sp.Symbol(r'\kappa'),
            "mu": sp.Symbol(r'\mu'),
            "alpha": sp.Symbol(r'\alpha'),
            "beta": sp.Symbol(r'\beta'),
            "gamma": sp.Symbol(r'\gamma'),
            "delta": sp.Symbol(r'\delta'),
            "Delta": sp.Symbol(r'\Delta'),
            "epsilon": sp.Symbol(r'\epsilon'),
            "zeta": sp.Symbol(r'\zeta'),
            "eta": sp.Symbol(r'\eta'),
            "theta": sp.Symbol(r'\theta'),
            "Theta": sp.Symbol(r'\Theta'),
            "iota": sp.Symbol(r'\iota'),
            "lambda": sp.Symbol(r'\lambda'),
            "Lambda": sp.Symbol(r'\Lambda'),
            "nu": sp.Symbol(r'\nu'),
            "xi": sp.Symbol(r'\xi'),
            "rho": sp.Symbol(r'\rho'),
            "sigma": sp.Symbol(r'\sigma'),
            "Sigma": sp.Symbol(r'\Sigma'),
            "tau": sp.Symbol(r'\tau'),
            "Phi": sp.Symbol(r'\Phi'),
            "omega": sp.Symbol(r'\omega'),
            "Omega": sp.Symbol(r'\Omega'),
            "degree": sp.Symbol(r'\degree'),
            "approx": sp.Symbol(r'\approx'),
            "ne": sp.Symbol(r'\ne'),
            "ge": sp.Symbol(r'\ge'),
            "le": sp.Symbol(r'\le'),
            # Petroleum engineering symbols
            "porosity": sp.Symbol(r'\phi'),
            "permeability": sp.Symbol(r'\kappa'),
            "viscosity": sp.Symbol(r'\mu'),
            "density": sp.Symbol(r'\rho'),
            "shear_rate": sp.Symbol(r'\dot{\gamma}'),
            "k": sp.Symbol('k'),
            "P": sp.Symbol('P'),
            "q": sp.Symbol('q'),
            "v": sp.Symbol('v'),
            "S": sp.Symbol('S'),
            "c": sp.Symbol('c'),
            "B": sp.Symbol('B'),
            "z": sp.Symbol('z'),
            "R": sp.Symbol('R'),
            "h": sp.Symbol('h'),
            "A": sp.Symbol('A'),
            "L": sp.Symbol('L'),
        }

        # Reserved names to avoid parsing conflicts
        reserved = ['sqrt', 'log', 'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'asin', 'acos', 'atan',
                    'sinh', 'cosh', 'tanh', 'exp', 'Sum', 'Limit', 'Integral', 'Derivative', 'oo', 'pi', 'E']

        # Step 2: Handle subscripted variables
        subscript_pattern = r'\b([a-zA-Z]+)_([a-zA-Z0-9]+)\b'
        subscript_vars = set(re.findall(subscript_pattern, formula))
        for base, subscript in subscript_vars:
            var_name = f"{base}_{subscript}"
            if var_name not in local_dict and base not in reserved:
                local_dict[var_name] = sp.Symbol(var_name)

        # Step 3: Replace ^ with ** for exponentiation
        parsed_formula = formula.replace("^", "**")

        # Step 4: Detect if there's an '=' (equation)
        if "=" in parsed_formula:
            # Handle multiple equals by taking only first
            parts = parsed_formula.split("=", 1)
            if len(parts) == 2:
                lhs, rhs = parts
                transformations = standard_transformations + (
                    implicit_multiplication_application,
                    convert_xor
                )
                lhs_expr = parse_expr(lhs.strip(), local_dict=local_dict, transformations=transformations, evaluate=False)
                rhs_expr = parse_expr(rhs.strip(), local_dict=local_dict, transformations=transformations, evaluate=False)
                expr = sp.Eq(lhs_expr, rhs_expr)
            else:
                raise ValueError("Invalid equation format")
        else:
            transformations = standard_transformations + (
                implicit_multiplication_application,
                convert_xor
            )
            expr = parse_expr(parsed_formula, local_dict=local_dict, transformations=transformations, evaluate=False)

        # Step 5: Convert to LaTeX with order preserved
        latex_str = sp.latex(expr, order='none')
        st.session_state.latex = latex_str
        st.session_state.latex_edited = False

    except Exception as e:
        st.session_state.latex = f"Invalid formula: {str(e)}"

# --- Function: Handle LaTeX input change ---
def update_from_latex():
    st.session_state.latex_edited = True
    update_latex()

# --- Function: Handle formula input change ---
def update_formula():
    st.session_state.latex_edited = False
    update_latex()

# --- Function: Convert LaTeX to image ---
def latex_to_image(latex_str):
    try:
        # First pass: measure the size
        fig = plt.figure(figsize=(10, 2))
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', fontsize=20, ha='center', va='center')
        fig.canvas.draw()
        bbox = ax.get_window_extent(fig.canvas.get_renderer())
        bbox_inches = bbox.transformed(fig.dpi_scale_trans.inverted())
        plt.close(fig)

        # Calculate proportional padding (10% of width, min 0.2)
        padding_width = max(bbox_inches.width * 0.1, 0.2)
        padding_height = max(bbox_inches.height * 0.15, 0.15)
        
        width = bbox_inches.width + padding_width
        height = bbox_inches.height + padding_height
        
        # Create final figure with proper sizing
        fig = plt.figure(figsize=(width, height))
        fig.patch.set_facecolor('white')
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', fontsize=20, ha='center', va='center')

        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.02, facecolor='white')
        plt.close(fig)
        buf.seek(0)

        img_b64 = base64.b64encode(buf.read()).decode()
        buf.seek(0)
        return img_b64, buf
    except Exception as e:
        st.error(f"Image generation error: {str(e)}")
        return None, None

# --- UI ---
st.title("Formula → LaTeX Converter")

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

# Input and clear button in columns
col1, col2 = st.columns([4, 1])
with col1:
    st.text_input("Enter formula (e.g., q = (k*A*Delta*P)/(mu*L))", key="formula", on_change=update_formula, placeholder="Darcy's Law: q = (k*A*ΔP)/(μ*L)")
with col2:
    st.button("Clear", on_click=clear_formula, type="secondary", use_container_width=True)

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
        ("∫", "Integral(, x)"),
        ("d/dx", "Derivative(, x)"),
        ("∑", "Sum(, x)"),
        ("lim", "Limit(, x, oo)"),
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
        ("e", "E"),
        ("∞", "oo"),
        ("_", "_"),
        ("(", "("),
        (")", ")"),
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
        ("Ω", "Omega"),
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
        ("μ", "mu"),
        ("ν (Poisson)", "nu"),
        ("G (shear)", "G"),
    ],
    "Petroleum Engineering": [
        ("φ (porosity)", "phi"),
        ("κ (permeability)", "kappa"),
        ("σ (tension)", "sigma"),
        ("τ (shear stress)", "tau"),
        ("γ̇ (shear rate)", "shear_rate"),
        ("k (perm)", "k"),
        ("μ (viscosity)", "mu"),
        ("ρ (density)", "rho"),
        ("γ (sp. gravity)", "gamma"),
        ("P (pressure)", "P"),
        ("q (flow rate)", "q"),
        ("v (velocity)", "v"),
        ("S (saturation)", "S"),
        ("c (compress.)", "c"),
        ("B (FVF)", "B"),
        ("z (z-factor)", "z"),
        ("R (GOR)", "R"),
        ("h (net pay)", "h"),
        ("A (area)", "A"),
        ("L (length)", "L"),
    ]
}

# Render buttons for each tab
for tab, group_name in [(tab1, "Mathematical Symbols"), (tab2, "Greek Characters"), 
                        (tab3, "Engineering Symbols"), (tab4, "Petroleum Engineering")]:
    with tab:
        cols = st.columns(5)
        for i, (label, text) in enumerate(button_groups[group_name]):
            with cols[i % 5]:
                st.button(label, key=f"{group_name}_{i}", 
                          on_click=partial(insert_text, text),
                          help=f"Insert {text}", 
                          use_container_width=True, type="secondary")

# LaTeX input, editable
st.text_input("LaTeX version (edit to modify directly)", key="latex", on_change=update_from_latex)

st.write("**Rendered:**")

if st.session_state.latex and not st.session_state.latex.startswith("Invalid"):
    try:
        st.latex(st.session_state.latex)
        img_b64, img_buffer = latex_to_image(st.session_state.latex)

        if img_b64:
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
                }).catch(() => {
                    button.style.backgroundColor = '#ff1744';
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
            <div style="max-height:500px; overflow-y:auto; background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0;">
                <div id="latex-content" style="display:none;">{st.session_state.latex}</div>
                <img id="latex-image" src="data:image/png;base64,{img_b64}" 
                     style="max-width: 100%; display: block; margin: 0 auto;" />
                <div style="display:flex; gap:10px; margin-top:15px; flex-wrap: wrap;">
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

            components.html(html_content, height=500)
            
            # Download button
            if img_buffer:
                st.download_button(
                    label="📥 Download Image",
                    data=img_buffer.getvalue(),
                    file_name="formula.png",
                    mime="image/png",
                    use_container_width=False
                )
        else:
            st.error("Unable to generate image. Please check your formula.")
            
    except Exception as e:
        st.error(f"Unable to render LaTeX: {str(e)}")
elif st.session_state.latex.startswith("Invalid"):
    st.error(st.session_state.latex)
else:
    st.info("Enter a valid formula or LaTeX to see the rendering.")

# Help section
with st.expander("ℹ️ Help & Tips"):
    st.markdown("""
    **How to use:**
    - Type your formula in the input box or use the symbol buttons
    - Use `_` for subscripts (e.g., `P_1`, `sigma_max`)
    - Use `^` for exponents (e.g., `x^2`, `e^(-t)`)
    - Use `*` for multiplication (e.g., `2*pi*r`)
    
    **Examples:**
    - Darcy's Law: `q = (k*A*Delta*P)/(mu*L)`
    - Area of circle: `A = pi*r^2`
    - Reynolds number: `Re = (rho*v*L)/mu`
    - Quadratic formula: `x = (-b + sqrt(b^2 - 4*a*c))/(2*a)`
    
    **Tips:**
    - Symbols are inserted at the end of your formula
    - Greek letters: Click the Greek Characters tab
    - For fractions: Use parentheses, e.g., `(a+b)/(c+d)`
    - For derivatives: `Derivative(x^2, x)`
    - For integrals: `Integral(x^2, x)`
    """)
