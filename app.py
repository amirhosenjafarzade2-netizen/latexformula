import streamlit as st
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations
from functools import partial, lru_cache
import base64
from io import BytesIO
import streamlit.components.v1 as components
import re
import matplotlib.pyplot as plt

# Initialize session state
if "formula" not in st.session_state:
    st.session_state.formula = ""
if "latex" not in st.session_state:
    st.session_state.latex = ""
if "mode" not in st.session_state:
    st.session_state.mode = "SymPy"  # "SymPy" or "LaTeX"
if "manual_edit" not in st.session_state:
    st.session_state.manual_edit = False

# Function to validate SymPy formula
def is_valid_formula(formula):
    if not formula.strip():
        return False, "Formula is empty."
    if formula.strip()[-1] in ['+', '-', '*', '/', '^', '_']:
        return False, "Formula ends with an incomplete operator."
    if st.session_state.mode == "SymPy" and ('{' in formula or '}' in formula):
        return False, "LaTeX braces {} not allowed in SymPy mode. Use _sub (e.g., x_1)."
    incomplete_functions = ['sqrt(', 'log(', 'sin(', 'cos(', 'tan(', 'exp(']
    for func in incomplete_functions:
        if formula.strip().endswith(func):
            return False, f"Incomplete: {func}"
    if formula.count('(') != formula.count(')'):
        return False, "Unbalanced parentheses."
    return True, ""

# Update LaTeX from SymPy or direct
def update_latex():
    if st.session_state.manual_edit:
        return
    formula = st.session_state.formula
    if st.session_state.mode == "LaTeX":
        st.session_state.latex = formula  # Direct pass
        return
    valid, error = is_valid_formula(formula)
    if not valid:
        st.session_state.latex = f"Invalid: {error}"
        st.error(error)
        return
    try:
        parsed = formula.replace("^", "**")
        locals_dict = {v: sp.Symbol(v) for v in re.findall(r'\b[a-zA-Z]\w*(?:_\w+)?\b', parsed) if v not in ['sqrt', 'log', 'sin', 'cos', 'tan', 'exp']}
        expr = parse_expr(parsed, local_dict=locals_dict, transformations=standard_transformations)
        st.session_state.latex = sp.latex(expr)
    except Exception as e:
        st.session_state.latex = f"Parse error: {str(e)}"
        st.error(str(e))

# Heuristic LaTeX to SymPy (basic)
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
    st.session_state.formula = sympy_approx
    st.session_state.mode = "SymPy"
    st.rerun()

# LaTeX to image (fallback)
@lru_cache(maxsize=100)
def latex_to_image(latex_str):
    try:
        fig = plt.figure(figsize=(6, 1))
        ax = fig.add_axes([0,0,1,1])
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', ha='center', va='center', fontsize=16)
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
    except:
        return None

# Append to input
def append_text(text):
    if st.session_state.mode == "LaTeX":
        st.session_state.formula += text
    else:
        st.session_state.formula += text.replace('_{}', '_')
    update_latex()

# UI
st.title("Enhanced LaTeX Equation Editor")

col1, col2 = st.columns([3,1])
with col2:
    st.session_state.mode = st.selectbox("Mode:", ["SymPy (parseable)", "LaTeX (direct)"], index=0 if st.session_state.mode == "SymPy" else 1)
    if st.button("Sync LaTeX → SymPy"):
        sync_to_sympy()

st.text_input("Input (SymPy or LaTeX):", key="formula", on_change=update_latex)
st.checkbox("Manual edit (lock auto-update)", key="manual_edit")

# Toolbar: Dropdowns
col1, col2, col3 = st.columns(3)
with col1:
    func = st.selectbox("Functions", ["", "\\sin", "\\cos", "\\tan", "\\log", "\\exp", "\\sqrt"])
    if func: append_text(f"{func}{{}}")
with col2:
    color = st.selectbox("Color", ["", "\\color{red}", "\\color{blue}", "\\color{green}"])
    if color: append_text(color)
with col3:
    size = st.selectbox("Size", ["", "\\tiny", "\\small", "\\large", "\\huge"])
    if size: append_text(size)

# Tabs for symbols
tab_names = ["Basic", "Greek", "Trig", "Calculus", "Matrices", "Chemistry", "Physics"]
tabs = st.tabs(tab_names)

# Basic symbols
with tabs[0]:
    symbols = {"+": "+", "-": "-", "*": "\\times", "/": "\\div", "^": "^{}", "_": "_{}"}
    for label, text in symbols.items():
        if st.button(label): append_text(text)

# Greek
with tabs[1]:
    greek = ["\\alpha", "\\beta", "\\gamma", "\\delta", "\\theta", "\\pi", "\\sigma", "\\phi"]
    cols = st.columns(4)
    for i, g in enumerate(greek):
        with cols[i%4]:
            if st.button(g): append_text(g)

# Trig
with tabs[2]:
    if st.button("\\sin{}"): append_text("\\sin{}")
    if st.button("\\cos{}"): append_text("\\cos{}")

# Calculus
with tabs[3]:
    if st.button("\\int_a^b"): append_text("\\int_a^b f(x) \\, dx")
    if st.button("\\frac{}{}"): append_text("\\frac{}{}")

# Matrices
with tabs[4]:
    with st.expander("Insert Matrix"):
        rows = st.number_input("Rows", 1, 5, 2)
        cols = st.number_input("Cols", 1, 5, 2)
        if st.button("Insert pmatrix"):
            matrix = "\\begin{pmatrix} & \\\\ & \\end{pmatrix}"
            append_text(matrix)

# Chemistry
with tabs[5]:
    with st.expander("Chemistry (\\ce{})"):
        if st.button("\\ce{H2O}"): append_text("\\ce{H2O}")
        if st.button("\\ce{A -> B}"): append_text("\\ce{A -> B}")

# Physics
with tabs[6]:
    with st.expander("Physics (\\dv, etc.)"):
        if st.button("\\dv{f}{x}"): append_text("\\dv{f}{x}")
        if st.button("\\grad{\\psi}"): append_text("\\grad{\\psi}")

# Output
st.text_area("LaTeX Output:", st.session_state.latex, key="latex_out", height=50)

st.write("Preview:")
if st.session_state.latex and not st.session_state.latex.startswith("Invalid"):
    st.latex(st.session_state.latex)
    
    # MathJax component
    components.html(f"""
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <div id="mathjax-preview">$${st.session_state.latex}$</div>
    <script>MathJax.typeset();</script>
    """, height=100)
    
    # Copy buttons (corrected)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Copy LaTeX"):
            st.code(st.session_state.latex)
    with col2:
        if st.button("Copy for Word"):
            st.info("Use MathML: " + st.session_state.latex.replace('\\', ''))
    with col3:
        img_b64 = latex_to_image(st.session_state.latex)
        if img_b64:
            st.image(f"data:image/png;base64,{img_b64}")
            if st.button("Copy Image"):
                st.success("Image copied! (simulate)")
else:
    st.info("Enter valid input.")

# Reset
if st.button("Reset"):
    for key in ["formula", "latex"]: setattr(st.session_state, key, "")
    st.rerun()
