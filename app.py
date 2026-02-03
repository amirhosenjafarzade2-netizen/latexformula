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
import json

matplotlib.use('Agg')

# --- Page Configuration ---
st.set_page_config(
    page_title="Formula ↔ LaTeX Converter Pro",
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
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "font_size" not in st.session_state:
    st.session_state.font_size = 20
if "show_help" not in st.session_state:
    st.session_state.show_help = False
if "auto_render" not in st.session_state:
    st.session_state.auto_render = True

# --- Helper: Validate formula ---
def is_valid_formula(formula):
    if not formula.strip():
        return False, "Formula is empty."
    if formula.strip()[-1] in ['+', '-', '*', '/', '^']:
        return False, "Formula ends with an incomplete operator."
    open_parens = formula.count('(')
    close_parens = formula.count(')')
    if open_parens != close_parens:
        return False, f"Unbalanced parentheses ({open_parens} open, {close_parens} close)."
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
    if st.session_state.auto_render:
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
    if st.session_state.auto_render:
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
        if st.session_state.auto_render:
            update_latex()

# --- Function: Add to favorites ---
def add_to_favorites():
    if st.session_state.formula and st.session_state.latex:
        if not st.session_state.latex.startswith("Invalid"):
            favorite = {
                "formula": st.session_state.formula,
                "latex": st.session_state.latex,
                "name": st.session_state.formula[:40]
            }
            if favorite not in st.session_state.favorites:
                st.session_state.favorites.append(favorite)
                st.success("Added to favorites! ⭐")

# --- Function: Export history as JSON ---
def export_history():
    if st.session_state.history:
        history_data = [{"formula": f, "latex": l} for f, l in st.session_state.history]
        return json.dumps(history_data, indent=2)
    return None

# --- Function: Import history from JSON ---
def import_history(json_str):
    try:
        data = json.loads(json_str)
        for item in data:
            if "formula" in item and "latex" in item:
                if (item["formula"], item["latex"]) not in st.session_state.history:
                    st.session_state.history.append((item["formula"], item["latex"]))
        st.success(f"Imported {len(data)} formulas!")
    except:
        st.error("Invalid JSON format")

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
            "ln": sp.log,
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
            "abs": sp.Abs,
            "floor": sp.floor,
            "ceiling": sp.ceiling,
            "Sum": sp.Sum,
            "Limit": sp.Limit,
            "Integral": sp.Integral,
            "Derivative": sp.Derivative,
            "oo": sp.oo,
            "pi": sp.pi,
            "e": sp.E,
            "I": sp.I,
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
        reserved = ['sqrt', 'log', 'ln', 'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'asin', 'acos', 'atan',
                    'sinh', 'cosh', 'tanh', 'exp', 'abs', 'floor', 'ceiling', 
                    'Sum', 'Limit', 'Integral', 'Derivative', 'oo', 'pi', 'e', 'I']

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
                st.session_state.history = st.session_state.history[:20]  # Keep last 20

    except Exception as e:
        st.session_state.latex = f"Invalid formula: {str(e)}"

# --- Function: Handle LaTeX input change ---
def update_from_latex():
    st.session_state.latex_edited = True
    update_latex()

# --- Function: Convert LaTeX to image with customizable font size ---
def latex_to_image(latex_str, font_size=20, bg_color='white', text_color='black'):
    try:
        # Create a temporary figure to measure the text
        fig, ax = plt.subplots(figsize=(1, 1))
        ax.axis('off')
        text = ax.text(0.5, 0.5, f'${latex_str}$', fontsize=font_size, 
                      ha='center', va='center', color=text_color)
        fig.canvas.draw()
        
        # Get the bounding box in pixels
        bbox = text.get_window_extent(renderer=fig.canvas.get_renderer())
        
        # Convert to inches (with padding)
        dpi = fig.dpi
        width_inches = (bbox.width / dpi) + 0.5
        height_inches = (bbox.height / dpi) + 0.3
        
        plt.close(fig)
        
        # Create the final figure with correct size
        fig = plt.figure(figsize=(width_inches, height_inches), facecolor=bg_color)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', fontsize=font_size, 
               ha='center', va='center', color=text_color)
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', 
                   pad_inches=0.1, facecolor=bg_color)
        plt.close(fig)
        buf.seek(0)
        
        return base64.b64encode(buf.read()).decode()
    except Exception as e:
        st.error(f"Image generation error: {str(e)}")
        return None

# --- Function: Simplify expression ---
def simplify_expression():
    try:
        formula = st.session_state.formula.strip()
        parsed_formula = formula.replace("^", "**")
        local_dict = {"sp": sp, "sqrt": sp.sqrt, "pi": sp.pi, "e": sp.E}
        
        transformations = standard_transformations + (
            implicit_multiplication_application,
            convert_xor
        )
        expr = parse_expr(parsed_formula, local_dict=local_dict, transformations=transformations)
        simplified = sp.simplify(expr)
        
        st.session_state.formula = str(simplified).replace("**", "^")
        update_formula_and_cursor()
        st.success("Expression simplified!")
    except Exception as e:
        st.error(f"Cannot simplify: {str(e)}")

# --- Function: Expand expression ---
def expand_expression():
    try:
        formula = st.session_state.formula.strip()
        parsed_formula = formula.replace("^", "**")
        local_dict = {"sp": sp, "sqrt": sp.sqrt, "pi": sp.pi, "e": sp.E}
        
        transformations = standard_transformations + (
            implicit_multiplication_application,
            convert_xor
        )
        expr = parse_expr(parsed_formula, local_dict=local_dict, transformations=transformations)
        expanded = sp.expand(expr)
        
        st.session_state.formula = str(expanded).replace("**", "^")
        update_formula_and_cursor()
        st.success("Expression expanded!")
    except Exception as e:
        st.error(f"Cannot expand: {str(e)}")

# --- Function: Factor expression ---
def factor_expression():
    try:
        formula = st.session_state.formula.strip()
        parsed_formula = formula.replace("^", "**")
        local_dict = {"sp": sp, "sqrt": sp.sqrt, "pi": sp.pi, "e": sp.E}
        
        transformations = standard_transformations + (
            implicit_multiplication_application,
            convert_xor
        )
        expr = parse_expr(parsed_formula, local_dict=local_dict, transformations=transformations)
        factored = sp.factor(expr)
        
        st.session_state.formula = str(factored).replace("**", "^")
        update_formula_and_cursor()
        st.success("Expression factored!")
    except Exception as e:
        st.error(f"Cannot factor: {str(e)}")

# --- Custom CSS ---
st.markdown("""
    <style>
    /* General styling */
    .stTabs [data-baseweb="tab"] {
        font-size: 16px;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #0f80c1;
    }
    
    /* Buttons */
    .stButton button {
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .stColumns > div {
            min-width: 100% !important;
        }
    }
    
    /* Card styling */
    .formula-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin: 10px 0;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 10px 0;
    }
    
    /* Help text */
    .help-text {
        color: #666;
        font-size: 14px;
        font-style: italic;
    }
    </style>
""", unsafe_allow_html=True)

# --- UI Layout ---
st.title("📐 Formula ↔ LaTeX Converter Pro")

# Top bar with settings
col_top1, col_top2, col_top3, col_top4 = st.columns([3, 1, 1, 1])
with col_top1:
    st.markdown("**Transform mathematical formulas into beautiful LaTeX**")
with col_top2:
    st.session_state.auto_render = st.checkbox("Auto-render", value=st.session_state.auto_render, 
                                                help="Automatically render as you type")
with col_top3:
    st.session_state.font_size = st.selectbox("Font Size", [16, 18, 20, 22, 24, 28], 
                                              index=2, help="Adjust output font size")
with col_top4:
    if st.button("❓ Help", use_container_width=True):
        st.session_state.show_help = not st.session_state.show_help

# Help section
if st.session_state.show_help:
    with st.expander("📖 How to Use", expanded=True):
        st.markdown("""
        ### Quick Start Guide
        
        **Input Methods:**
        - Type formulas directly: `x^2 + 2*x + 1`
        - Use buttons to insert symbols
        - Edit LaTeX directly in the LaTeX field
        
        **Syntax:**
        - Powers: `x^2` or `x**2`
        - Fractions: `a/b`
        - Square root: `sqrt(x)`
        - Functions: `sin(x)`, `cos(x)`, `log(x)`
        - Integrals: `Integral(x^2, (x, 0, 1))`
        - Derivatives: `Derivative(sin(x), x)`
        - Summation: `Sum(1/n^2, (n, 1, oo))`
        - Limits: `Limit(sin(x)/x, x, 0)`
        
        **Special Symbols:**
        - Infinity: `oo`
        - Pi: `pi`
        - Euler's number: `e`
        - Subscripts: `x_1`, `alpha_max`
        
        **Keyboard Shortcuts:**
        - Clear: Clear button or delete all text
        - Backspace: Back button
        
        **Export Options:**
        - Copy LaTeX code
        - Copy formatted for Word (MathML)
        - Copy as PNG image
        - Download .tex file
        - Download PNG image
        """)

# Sidebar - Advanced Features
with st.sidebar:
    st.header("🎯 Quick Actions")
    
    # Transform tools
    st.subheader("Transform")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        if st.button("🔧 Simplify", use_container_width=True, help="Simplify the expression"):
            simplify_expression()
    with col_s2:
        if st.button("📈 Expand", use_container_width=True, help="Expand the expression"):
            expand_expression()
    with col_s3:
        if st.button("🔍 Factor", use_container_width=True, help="Factor the expression"):
            factor_expression()
    
    st.divider()
    
    # Favorites section
    st.header("⭐ Favorites")
    if st.button("➕ Add Current to Favorites", use_container_width=True):
        add_to_favorites()
    
    if st.session_state.favorites:
        for i, fav in enumerate(st.session_state.favorites):
            col_f1, col_f2 = st.columns([4, 1])
            with col_f1:
                display_name = fav['name'] if len(fav['name']) <= 30 else fav['name'][:27] + "..."
                if st.button(f"⭐ {display_name}", key=f"fav_{i}", use_container_width=True):
                    st.session_state.formula = fav['formula']
                    update_formula_and_cursor()
                    st.rerun()
            with col_f2:
                if st.button("🗑️", key=f"del_fav_{i}", help="Remove"):
                    st.session_state.favorites.pop(i)
                    st.rerun()
    else:
        st.info("No favorites yet")
    
    st.divider()
    
    # Examples
    st.header("📚 Examples")
    examples = {
        "Quadratic Formula": "x = (-b + sqrt(b^2 - 4*a*c))/(2*a)",
        "Darcy's Law": "q = (k*A*(P1-P2))/(mu*L)",
        "Pythagorean": "a^2 + b^2 = c^2",
        "Euler's Identity": "e^(I*pi) + 1 = 0",
        "Integral": "Integral(x^2, (x, 0, 1))",
        "Summation": "Sum(1/n^2, (n, 1, oo))",
        "Derivative": "Derivative(sin(x)*cos(x), x)",
        "Limit": "Limit(sin(x)/x, x, 0)",
        "Matrix": "((a, b), (c, d))",
        "Binomial": "(x + y)^n",
    }
    
    for name, formula in examples.items():
        if st.button(f"📝 {name}", use_container_width=True, key=f"example_{name}"):
            st.session_state.formula = formula
            update_formula_and_cursor()
            st.rerun()
    
    st.divider()
    
    # History
    st.header("🕐 History")
    
    # Export/Import history
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        if st.session_state.history:
            history_json = export_history()
            if history_json:
                st.download_button(
                    label="📥 Export",
                    data=history_json,
                    file_name="formula_history.json",
                    mime="application/json",
                    use_container_width=True
                )
    with col_h2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    
    # Upload history
    uploaded_history = st.file_uploader("📤 Import History", type=['json'], label_visibility="collapsed")
    if uploaded_history:
        json_str = uploaded_history.read().decode()
        import_history(json_str)
        st.rerun()
    
    # Display history
    if st.session_state.history:
        for i, (formula, latex) in enumerate(st.session_state.history[:10]):
            display_text = formula if len(formula) <= 30 else formula[:27] + "..."
            if st.button(f"{i+1}. {display_text}", key=f"history_{i}", use_container_width=True):
                st.session_state.formula = formula
                update_formula_and_cursor()
                st.rerun()
        if len(st.session_state.history) > 10:
            st.caption(f"... and {len(st.session_state.history) - 10} more")
    else:
        st.info("No history yet")

# Main input area
col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
with col1:
    st.text_input("Enter formula", key="formula", on_change=update_formula_and_cursor, 
                  placeholder="e.g., x^2 + 2*x + 1 or sqrt(a^2 + b^2)")
with col2:
    st.button("⌫ Clear", key="clear_btn", on_click=clear_formula, use_container_width=True, type="secondary")
with col3:
    st.button("← Back", key="back_btn", on_click=backspace_formula, use_container_width=True, type="secondary")
with col4:
    if not st.session_state.auto_render:
        if st.button("▶️ Render", use_container_width=True, type="primary"):
            update_latex()

# Status indicator with more details
if st.session_state.latex:
    if st.session_state.latex.startswith("Invalid"):
        st.error(f"❌ {st.session_state.latex}")
    else:
        col_status1, col_status2 = st.columns([3, 1])
        with col_status1:
            st.success(f"✓ Valid formula | Length: {len(st.session_state.latex)} chars")
        with col_status2:
            if st.button("⭐ Add to Favorites", use_container_width=True):
                add_to_favorites()

# Tabbed interface for symbol groups
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔢 Mathematical", "🔤 Greek", "⚙️ Engineering", "🛢️ Petroleum", "➕ Advanced"])

# Button groups
button_groups = {
    "Mathematical": [
        ("√", "sqrt()"),
        ("∛", "()^(1/3)"),
        ("÷", "/"),
        ("×", "*"),
        ("^", "^"),
        ("=", "="),
        ("≠", "ne"),
        ("≈", "approx"),
        ("<", "<"),
        (">", ">"),
        ("≤", "le"),
        ("≥", "ge"),
        ("±", "±"),
        ("|x|", "abs()"),
        ("∫", "Integral(, x)"),
        ("d/dx", "Derivative(, x)"),
        ("∑", "Sum(, (n, 1, oo))"),
        ("∏", "Product(, (n, 1, oo))"),
        ("lim", "Limit(, x, 0)"),
        ("log", "log()"),
        ("ln", "ln()"),
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
        ("i", "I"),
        ("_", "_"),
        ("(", "("),
        (")", ")"),
        ("[", "["),
        ("]", "]"),
        ("{", "{"),
        ("}", "}"),
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
        ("κ", "kappa"),
        ("λ", "lambda"),
        ("Λ", "Lambda"),
        ("μ", "mu"),
        ("ν", "nu"),
        ("ξ", "xi"),
        ("ρ", "rho"),
        ("σ", "sigma"),
        ("Σ", "Sigma"),
        ("τ", "tau"),
        ("υ", "upsilon"),
        ("φ", "phi"),
        ("Φ", "Phi"),
        ("χ", "chi"),
        ("ψ", "psi"),
        ("ω", "omega"),
        ("Ω", "Omega"),
    ],
    "Engineering": [
        ("°", "degree"),
        ("σ (stress)", "sigma"),
        ("τ (torque)", "tau"),
        ("E (modulus)", "E"),
        ("μ (friction)", "mu"),
        ("ν (Poisson)", "nu"),
        ("G (shear)", "G"),
        ("F (force)", "F"),
        ("M (moment)", "M"),
        ("V (shear)", "V"),
        ("ε (strain)", "epsilon"),
    ],
    "Petroleum": [
        ("φ (porosity)", "phi"),
        ("κ (perm)", "kappa"),
        ("σ (tension)", "sigma"),
        ("τ (shear)", "tau"),
        ("γ̇ (shear rate)", "shear_rate"),
        ("k (perm)", "k"),
        ("μ (viscosity)", "mu"),
        ("ρ (density)", "rho"),
        ("γ (sp. gravity)", "gamma"),
        ("P (pressure)", "P"),
        ("q (flow rate)", "q"),
        ("v (velocity)", "v"),
        ("S (saturation)", "S"),
        ("c (compress)", "c"),
        ("B (FVF)", "B"),
        ("z (Z-factor)", "z"),
        ("R (GOR)", "R"),
        ("h (net pay)", "h"),
    ],
    "Advanced": [
        ("∂", "partial"),
        ("∇", "nabla"),
        ("∇²", "laplacian"),
        ("⊗", "otimes"),
        ("⊕", "oplus"),
        ("∈", "in"),
        ("∉", "notin"),
        ("⊂", "subset"),
        ("⊆", "subseteq"),
        ("∪", "cup"),
        ("∩", "cap"),
        ("∅", "emptyset"),
        ("∀", "forall"),
        ("∃", "exists"),
        ("¬", "neg"),
        ("∧", "wedge"),
        ("∨", "vee"),
        ("⇒", "implies"),
        ("⇔", "iff"),
    ]
}

# Render buttons for each tab
tab_mapping = {tab1: "Mathematical", tab2: "Greek", tab3: "Engineering", tab4: "Petroleum", tab5: "Advanced"}

for tab, group_name in tab_mapping.items():
    with tab:
        cols = st.columns(6)
        for i, (label, text) in enumerate(button_groups[group_name]):
            with cols[i % 6]:
                st.button(label, key=f"{group_name}_{i}", on_click=partial(insert_at_cursor, text), 
                          help=f"Insert {text}", use_container_width=True, type="secondary")

st.divider()

# LaTeX input, editable
col_latex1, col_latex2 = st.columns([4, 1])
with col_latex1:
    st.text_input("LaTeX version (edit to modify directly)", key="latex", on_change=update_from_latex,
                  placeholder="LaTeX code will appear here")
with col_latex2:
    if st.session_state.latex and not st.session_state.latex.startswith("Invalid"):
        if st.button("📋 Copy LaTeX", use_container_width=True, type="primary"):
            st.code(st.session_state.latex, language="latex")
            st.info("LaTeX code displayed above - copy manually")

st.write("### 📊 Rendered Output:")

if st.session_state.latex and not st.session_state.latex.startswith("Invalid"):
    try:
        # Show LaTeX render
        st.latex(st.session_state.latex)
        
        # Generate image with custom settings
        bg_color = 'white'
        text_color = 'black'
        
        img_b64 = latex_to_image(st.session_state.latex, st.session_state.font_size, bg_color, text_color)

        # Download buttons
        col1, col2, col3 = st.columns(3)
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
                    label="📥 Download PNG",
                    data=png_data,
                    file_name="formula.png",
                    mime="image/png",
                    use_container_width=True
                )
        with col3:
            # Download as SVG (placeholder - would need actual SVG generation)
            st.download_button(
                label="📥 LaTeX Source",
                data=f"\\documentclass{{article}}\\usepackage{{amsmath}}\\begin{{document}}\n${st.session_state.latex}$\n\\end{{document}}",
                file_name="formula_document.tex",
                mime="text/plain",
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
                    button.innerText = '📋 Copy LaTeX';
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
                    button.innerText = '📄 Copy for Word';
                }, 1500);
            } catch (err) {
                button.style.backgroundColor = '#ff1744';
                button.innerText = 'Failed';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = '📄 Copy for Word';
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
                    button.innerText = '🖼️ Copy as Image';
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
                    button.innerText = '🖼️ Copy as Image';
                }, 1500);
            } catch (err) {
                button.style.backgroundColor = '#ff1744';
                button.innerText = 'Failed';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = '🖼️ Copy as Image';
                }, 1500);
            }
        }
        </script>
        """

        html_content = f"""
        {copy_js}
        <div style="max-height:600px; overflow-y:auto; border: 2px solid #e0e0e0; padding: 25px; 
                    border-radius: 12px; background: linear-gradient(to bottom, #ffffff, #f8f9fa); 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div id="latex-content" style="display:none;">{st.session_state.latex}</div>
        """

        if img_b64:
            html_content += f"""
            <div style="text-align: center; background-color: white; padding: 30px; 
                        border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <img id="latex-image" src="data:image/png;base64,{img_b64}" 
                     style="max-width: 100%; height: auto;" />
            </div>
            """
        else:
            html_content += "<p style='color:red; text-align:center;'>⚠️ Image generation failed</p>"

        html_content += """
            <div style="display:flex; gap:12px; margin-top:25px; justify-content: center; flex-wrap: wrap;">
                <button id="copy-latex-btn" onclick="copyLatexText()" 
                        style="background-color:#0f80c1;color:white;padding:14px 28px;
                               border:none;border-radius:8px;cursor:pointer;font-weight:600;
                               font-size:15px;transition:all 0.3s;box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    📋 Copy LaTeX
                </button>
                <button id="copy-word-btn" onclick="copyForWord()" 
                        style="background-color:#0f80c1;color:white;padding:14px 28px;
                               border:none;border-radius:8px;cursor:pointer;font-weight:600;
                               font-size:15px;transition:all 0.3s;box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    📄 Copy for Word
                </button>
                <button id="copy-image-btn" onclick="copyAsImage()" 
                        style="background-color:#0f80c1;color:white;padding:14px 28px;
                               border:none;border-radius:8px;cursor:pointer;font-weight:600;
                               font-size:15px;transition:all 0.3s;box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    🖼️ Copy as Image
                </button>
            </div>
        </div>
        """

        # Better dynamic height calculation
        latex_length = len(st.session_state.latex)
        dynamic_height = max(450, min(750, 450 + (latex_length // 20) * 10))
        components.html(html_content, height=dynamic_height)
        
        # Show LaTeX code in expandable section
        with st.expander("📝 View LaTeX Source Code"):
            st.code(st.session_state.latex, language="latex")
        
    except Exception as e:
        st.error(f"❌ Unable to render LaTeX: {str(e)}")
else:
    st.info("👆 Enter a valid formula or LaTeX code above to see the rendering.")

# Footer with tips
st.divider()
st.markdown("""
    <div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px;'>
        <h4 style='margin: 0; color: #333;'>💡 Pro Tips</h4>
        <p style='margin: 10px 0; color: #666;'>
            • Use symbol buttons for quick insertion • Enable auto-render for live preview •
            Save favorites for frequently used formulas • Export history to backup your work •
            Use simplify/expand/factor for algebraic manipulation
        </p>
    </div>
""", unsafe_allow_html=True)
