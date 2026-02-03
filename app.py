import streamlit as st
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
)
from functools import partial, lru_cache
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
import streamlit.components.v1 as components
import re

matplotlib.use('Agg')

# --- Page Configuration ---
st.set_page_config(
    page_title="Formula ↔ LaTeX Converter",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialize session state ---
if "formula" not in st.session_state:
    st.session_state.formula = ""
if "latex" not in st.session_state:
    st.session_state.latex = ""
if "cursor_pos" not in st.session_state:
    st.session_state.cursor_pos = 0
if "latex_edited" not in st.session_state:
    st.session_state.latex_edited = False
if "history" not in st.session_state:
    st.session_state.history = []

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
    
    # For functions with parentheses, place cursor inside
    if '()' in text:
        insert_text = text.replace('()', '(|)')
        parts = insert_text.split('|')
        st.session_state.formula = formula[:cursor_pos] + parts[0] + parts[1] + formula[cursor_pos:]
        st.session_state.cursor_pos = cursor_pos + len(parts[0])
    else:
        st.session_state.formula = formula[:cursor_pos] + text + formula[cursor_pos:]
        st.session_state.cursor_pos = cursor_pos + len(text)
    
    st.session_state.latex_edited = False
    update_latex()

# --- Function: Update cursor position ---
def update_cursor_pos():
    try:
        st.session_state.cursor_pos = len(st.session_state.formula)
    except:
        st.session_state.cursor_pos = 0

# --- Function: Update formula and cursor ---
def update_formula_and_cursor():
    update_cursor_pos()
    update_latex()

# --- Function: Clear formula ---
def clear_formula():
    st.session_state.formula = ""
    st.session_state.latex = ""
    st.session_state.cursor_pos = 0
    st.session_state.latex_edited = False

# --- Function: Backspace ---
def backspace_formula():
    if st.session_state.formula:
        st.session_state.formula = st.session_state.formula[:-1]
        st.session_state.cursor_pos = len(st.session_state.formula)
        update_latex()

# --- Function: Update LaTeX from formula or LaTeX input ---
def update_latex():
    if st.session_state.latex_edited:
        # If LaTeX was edited, use it directly if valid
        latex_str = st.session_state.latex.strip()
        if latex_str and (latex_str.startswith("\\") or re.search(r"\\frac|\\int|\\sqrt|\\left|\\sum", latex_str)):
            try:
                # Basic validation: attempt to render LaTeX
                plt.figure()
                plt.text(0, 0, f'${latex_str}$')
                plt.close()
                return  # LaTeX is valid, keep it
            except:
                st.session_state.latex = "Invalid LaTeX input"
                return
        else:
            st.session_state.latex = "Invalid LaTeX: Must be valid LaTeX syntax"
            return

    formula = st.session_state.formula.strip()
    valid, error_msg = is_valid_formula(formula)
    if not valid:
        st.session_state.latex = f"Invalid formula: {error_msg}"
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
            "e": sp.E,
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
        }

        # Reserved names to avoid parsing conflicts
        reserved = ['sqrt', 'log', 'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'asin', 'acos', 'atan',
                    'sinh', 'cosh', 'tanh', 'exp', 'Sum', 'Limit', 'Integral', 'Derivative', 'oo', 'pi', 'e']

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
        st.session_state.latex_edited = False
        
        # Add to history
        if latex_str and not latex_str.startswith("Invalid"):
            if st.session_state.formula not in [h[0] for h in st.session_state.history]:
                st.session_state.history.insert(0, (st.session_state.formula, latex_str))
                st.session_state.history = st.session_state.history[:10]  # Keep last 10

    except Exception as e:
        st.session_state.latex = f"Invalid formula: {str(e)}"

# --- Function: Handle LaTeX input change ---
def update_from_latex():
    st.session_state.latex_edited = True
    update_latex()

# --- Function: Convert LaTeX to image (IMPROVED) ---
def latex_to_image(latex_str):
    try:
        # Create a temporary figure to measure the text
        fig, ax = plt.subplots(figsize=(1, 1))
        ax.axis('off')
        text = ax.text(0.5, 0.5, f'${latex_str}$', fontsize=20, ha='center', va='center')
        fig.canvas.draw()
        
        # Get the bounding box in pixels
        bbox = text.get_window_extent(renderer=fig.canvas.get_renderer())
        
        # Convert to inches (with padding)
        dpi = fig.dpi
        width_inches = (bbox.width / dpi) + 0.5  # Add padding
        height_inches = (bbox.height / dpi) + 0.3
        
        plt.close(fig)
        
        # Create the final figure with correct size
        fig = plt.figure(figsize=(width_inches, height_inches), facecolor='white')
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', fontsize=20, ha='center', va='center')
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                   pad_inches=0.1, facecolor='white')
        plt.close(fig)
        buf.seek(0)
        
        return base64.b64encode(buf.read()).decode()
    except Exception as e:
        st.error(f"Image generation error: {str(e)}")
        return None

# --- UI ---
st.title("📐 Formula ↔ LaTeX Converter")
st.markdown("Convert mathematical formulas to LaTeX and vice versa")

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
    @media (max-width: 768px) {
        .stColumns > div {
            min-width: 100% !important;
        }
        .symbol-button {
            font-size: 12px;
            padding: 6px 8px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar - History and Examples
with st.sidebar:
    st.header("📚 Quick Examples")
    examples = {
        "Quadratic Formula": "x = (-b + sqrt(b^2 - 4*a*c))/(2*a)",
        "Darcy's Law": "q = (k*A*(P1-P2))/(mu*L)",
        "Integral": "Integral(x^2, (x, 0, 1))",
        "Summation": "Sum(1/n^2, (n, 1, oo))",
        "Derivative": "Derivative(sin(x)*cos(x), x)",
        "Limit": "Limit(sin(x)/x, x, 0)",
    }
    
    for name, formula in examples.items():
        if st.button(f"📝 {name}", use_container_width=True, key=f"example_{name}"):
            st.session_state.formula = formula
            update_formula_and_cursor()
            st.rerun()
    
    st.divider()
    
    if st.session_state.history:
        st.header("🕐 Recent Formulas")
        for i, (formula, latex) in enumerate(st.session_state.history):
            display_text = formula if len(formula) <= 30 else formula[:27] + "..."
            if st.button(f"{i+1}. {display_text}", key=f"history_{i}", use_container_width=True):
                st.session_state.formula = formula
                update_formula_and_cursor()
                st.rerun()
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()

# Main input area
col1, col2, col3 = st.columns([6, 1, 1])
with col1:
    st.text_input("Enter formula", key="formula", on_change=update_formula_and_cursor, 
                  placeholder="e.g., x^2 + 2*x + 1 or sqrt(a^2 + b^2)")
with col2:
    st.button("⌫ Clear", key="clear_btn", on_click=clear_formula, use_container_width=True, type="secondary")
with col3:
    st.button("← Back", key="back_btn", on_click=backspace_formula, use_container_width=True, type="secondary")

# Status indicator
if st.session_state.latex:
    if st.session_state.latex.startswith("Invalid"):
        st.error(f"❌ {st.session_state.latex}")
    else:
        st.success("✓ Valid formula")

# Tabbed interface for symbol groups
tab1, tab2, tab3, tab4 = st.tabs(["🔢 Mathematical", "🔤 Greek", "⚙️ Engineering", "🛢️ Petroleum"])

# Button groups
button_groups = {
    "Mathematical": [
        ("√", "sqrt()"),
        ("÷", "/"),
        ("×", "*"),
        ("^", "^"),
        ("=", "="),
        ("∫", "Integral(, x)"),
        ("d/dx", "Derivative(, x)"),
        ("∑", "Sum(, (n, 1, oo))"),
        ("lim", "Limit(, x, 0)"),
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
        ("e", "e"),
        ("∞", "oo"),
        ("_", "_"),
        ("(", "("),
        (")", ")"),
    ],
    "Greek": [
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
    "Engineering": [
        ("°", "degree"),
        ("≈", "approx"),
        ("≠", "ne"),
        ("≥", "ge"),
        ("≤", "le"),
        ("σ", "sigma"),
        ("τ", "tau"),
        ("E", "E"),
        ("μ", "mu"),
        ("ν", "nu"),
        ("G", "G"),
    ],
    "Petroleum": [
        ("φ (porosity)", "phi"),
        ("κ (permeability)", "kappa"),
        ("σ (tension)", "sigma"),
        ("τ (shear stress)", "tau"),
        ("γ̇ (shear rate)", "shear_rate"),
        ("k", "k"),
        ("μ (viscosity)", "mu"),
        ("ρ (density)", "rho"),
        ("γ", "gamma"),
        ("P (pressure)", "P"),
        ("q (flow rate)", "q"),
        ("v (velocity)", "v"),
        ("S (saturation)", "S"),
        ("c (compressibility)", "c"),
        ("B (FVF)", "B"),
        ("z (deviation)", "z"),
        ("R (GOR)", "R"),
        ("h (net pay)", "h"),
    ]
}

# Render buttons for each tab
tab_mapping = {tab1: "Mathematical", tab2: "Greek", tab3: "Engineering", tab4: "Petroleum"}

for tab, group_name in tab_mapping.items():
    with tab:
        cols = st.columns(6)
        for i, (label, text) in enumerate(button_groups[group_name]):
            with cols[i % 6]:
                st.button(label, key=f"{group_name}_{i}", on_click=partial(insert_at_cursor, text), 
                          help=f"Insert {text}", use_container_width=True, type="secondary")

st.divider()

# LaTeX input, editable
st.text_input("LaTeX version (edit to modify directly)", key="latex", on_change=update_from_latex,
              placeholder="LaTeX code will appear here")

st.write("### Rendered Output:")

if st.session_state.latex and not st.session_state.latex.startswith("Invalid"):
    try:
        st.latex(st.session_state.latex)
        img_b64 = latex_to_image(st.session_state.latex)

        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download LaTeX (.tex)",
                data=st.session_state.latex,
                file_name="formula.tex",
                mime="text/plain",
                use_container_width=True
            )
        with col2:
            if img_b64:
                png_data = base64.b64decode(img_b64)
                st.download_button(
                    label="📥 Download Image (.png)",
                    data=png_data,
                    file_name="formula.png",
                    mime="image/png",
                    use_container_width=True
                )

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
        <div style="max-height:600px; overflow-y:auto; border: 1px solid #e0e0e0; padding: 20px; border-radius: 8px; background-color: #fafafa;">
            <div id="latex-content" style="display:none;">{st.session_state.latex}</div>
        """

        if img_b64:
            html_content += f"""
            <div style="text-align: center; background-color: white; padding: 20px; border-radius: 4px;">
                <img id="latex-image" src="data:image/png;base64,{img_b64}" 
                     style="max-width: 100%; height: auto;" />
            </div>
            """
        else:
            html_content += "<p style='color:red;'>No image available.</p>"

        html_content += """
            <div style="display:flex; gap:10px; margin-top:20px; justify-content: center;">
                <button id="copy-latex-btn" onclick="copyLatexText()" 
                        style="background-color:#0f80c1;color:white;padding:12px 24px;
                               border:none;border-radius:6px;cursor:pointer;font-weight:bold;
                               font-size:14px;transition:all 0.3s;">
                    📋 Copy LaTeX
                </button>
                <button id="copy-word-btn" onclick="copyForWord()" 
                        style="background-color:#0f80c1;color:white;padding:12px 24px;
                               border:none;border-radius:6px;cursor:pointer;font-weight:bold;
                               font-size:14px;transition:all 0.3s;">
                    📄 Copy for Word
                </button>
                <button id="copy-image-btn" onclick="copyAsImage()" 
                        style="background-color:#0f80c1;color:white;padding:12px 24px;
                               border:none;border-radius:6px;cursor:pointer;font-weight:bold;
                               font-size:14px;transition:all 0.3s;">
                    🖼️ Copy as Image
                </button>
            </div>
        </div>
        """

        # Better dynamic height calculation
        latex_length = len(st.session_state.latex)
        dynamic_height = max(400, min(700, 400 + (latex_length // 20) * 10))
        components.html(html_content, height=dynamic_height)
        
    except Exception as e:
        st.error(f"Unable to render LaTeX: {str(e)}")
else:
    st.info("👆 Enter a valid formula or LaTeX code above to see the rendering.")

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; font-size: 12px;'>
        <p>💡 Tip: Click symbol buttons to insert them at the cursor position | Use examples in the sidebar to get started</p>
    </div>
""", unsafe_allow_html=True)
