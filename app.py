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
if "history" not in st.session_state:
    st.session_state.history = []

# Function to validate SymPy formula
def is_valid_formula(formula):
    if not formula.strip():
        return False, "Formula is empty."
    if formula.strip()[-1] in ['+', '-', '*', '/', '^', '_']:
        return False, "Formula ends with an incomplete operator."
    if st.session_state.mode == "SymPy" and ('{' in formula or '}' in formula):
        return False, "LaTeX braces {} not allowed in SymPy mode. Use _sub (e.g., x_1)."
    incomplete_functions = ['sqrt(', 'log(', 'sin(', 'cos(', 'tan(', 'exp(', 'sum(', 'prod(']
    for func in incomplete_functions:
        if formula.strip().endswith(func):
            return False, f"Incomplete: {func}"
    if formula.count('(') != formula.count(')'):
        return False, "Unbalanced parentheses."
    if formula.count('{') != formula.count('}'):
        return False, "Unbalanced LaTeX braces."
    return True, ""

# Update LaTeX from SymPy or direct
def update_latex():
    if st.session_state.manual_edit:
        return
    formula = st.session_state.formula
    if st.session_state.mode == "LaTeX":
        st.session_state.latex = formula
        return
    valid, error = is_valid_formula(formula)
    if not valid:
        st.session_state.latex = f"Invalid: {error}"
        st.error(error)
        return
    try:
        parsed = formula.replace("^", "**").replace("sum", "Sum").replace("prod", "Product")
        locals_dict = {v: sp.Symbol(v) for v in re.findall(r'\b[a-zA-Z]\w*(?:_\w+)?\b', parsed) if v not in ['sqrt', 'log', 'sin', 'cos', 'tan', 'exp', 'Sum', 'Product']}
        expr = parse_expr(parsed, local_dict=locals_dict, transformations=standard_transformations)
        latex_out = sp.latex(expr)
        st.session_state.latex = latex_out
        st.session_state.history.append((formula, latex_out))
        if len(st.session_state.history) > 10:
            st.session_state.history.pop(0)
    except Exception as e:
        st.session_state.latex = f"Parse error: {str(e)}"
        st.error(str(e))

# Heuristic LaTeX to SymPy
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
    sympy_approx = re.sub(r'\\prod_\{([^}]+)\}\^\{([^}]+)\}', r'prod(\1,\2)', sympy_approx)
    sympy_approx = re.sub(r'\\int_\{([^}]+)\}\^\{([^}]+)\}', r'integral(\1,\2)', sympy_approx)
    st.session_state.formula = sympy_approx
    st.session_state.mode = "SymPy"
    st.rerun()

# LaTeX to image
@lru_cache(maxsize=100)
def latex_to_image(latex_str):
    try:
        fig = plt.figure(figsize=(8, 2))
        ax = fig.add_axes([0,0,1,1])
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', ha='center', va='center', fontsize=18)
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=200, transparent=True)
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
    except:
        return None

# LaTeX to PDF (simplified)
def latex_to_pdf(latex_str):
    try:
        fig = plt.figure(figsize=(8, 2))
        ax = fig.add_axes([0,0,1,1])
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', ha='center', va='center', fontsize=18)
        buf = BytesIO()
        plt.savefig(buf, format='pdf', bbox_inches='tight')
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
        text = text.replace('_{}', '_').replace('^{}', '^')
        st.session_state.formula += text
    update_latex()

# UI
st.title("Enhanced LaTeX Equation Editor")

# Mode and sync
col1, col2 = st.columns([3,1])
with col2:
    st.session_state.mode = st.selectbox("Mode:", ["SymPy (parseable)", "LaTeX (direct)"], index=0 if st.session_state.mode == "SymPy" else 1)
    if st.button("Sync LaTeX → SymPy"):
        sync_to_sympy()
    if st.button("View History"):
        st.write("Recent Formulas:", st.session_state.history)

# Input
st.text_input("Input (SymPy or LaTeX):", key="formula", on_change=update_latex)
st.checkbox("Manual edit (lock auto-update)", key="manual_edit")

# Toolbar: Dropdowns
col1, col2, col3, col4 = st.columns(4)
with col1:
    func = st.selectbox("Functions", ["", "\\sin", "\\cos", "\\tan", "\\log", "\\exp", "\\sqrt", "\\arcsin", "\\arccos", "\\arctan"])
    if func: append_text(f"{func}{{}}")
with col2:
    color = st.selectbox("Color", ["", "\\color{red}", "\\color{blue}", "\\color{green}", "\\color{black}", "\\color{purple}"])
    if color: append_text(f"{color}{{}}")
with col3:
    size = st.selectbox("Size", ["", "\\tiny", "\\small", "\\normalsize", "\\large", "\\huge"])
    if size: append_text(f"{size}")
with col4:
    accents = st.selectbox("Accents", ["", "\\hat", "\\bar", "\\tilde", "\\dot", "\\ddot"])
    if accents: append_text(f"{accents}{{}}")

# Tabs
tab_names = ["Basic", "Greek", "Relations", "Arrows", "Calculus", "Matrices", "Chemistry", "Physics"]
tabs = st.tabs(tab_names)

# Basic
with tabs[0]:
    cols = st.columns(5)
    symbols = {"+": "+", "-": "-", "×": "\\times", "÷": "\\div", "^": "^{}", "_": "_{}", "=": "=", "(": "(", ")": ")", ",": ","}
    for i, (label, text) in enumerate(symbols.items()):
        with cols[i%5]:
            if st.button(label): append_text(text)

# Greek
with tabs[1]:
    cols = st.columns(4)
    greek = ["\\alpha", "\\beta", "\\gamma", "\\delta", "\\epsilon", "\\theta", "\\pi", "\\sigma", "\\phi", "\\omega", "\\Gamma", "\\Delta"]
    for i, g in enumerate(greek):
        with cols[i%4]:
            if st.button(g): append_text(g)

# Relations
with tabs[2]:
    cols = st.columns(4)
    relations = ["\\leq", "\\geq", "\\neq", "\\approx", "\\sim", "\\equiv", "\\subset", "\\subseteq"]
    for i, r in enumerate(relations):
        with cols[i%4]:
            if st.button(r): append_text(r)

# Arrows
with tabs[3]:
    cols = st.columns(4)
    arrows = ["\\rightarrow", "\\leftarrow", "\\leftrightarrow", "\\uparrow", "\\downarrow", "\\Rightarrow", "\\Leftarrow"]
    for i, a in enumerate(arrows):
        with cols[i%4]:
            if st.button(a): append_text(a)

# Calculus
with tabs[4]:
    cols = st.columns(4)
    calculus = ["\\int_a^b": "\\int_{a}^{b} f(x) \\, dx", "\\sum_a^b": "\\sum_{a}^{b}", "\\prod_a^b": "\\prod_{a}^{b}", "\\frac": "\\frac{}{}", "\\lim": "\\lim_{x \\to a}", "\\partial": "\\partial"]
    for i, (label, text) in enumerate(calculus.items()):
        with cols[i%4]:
            if st.button(label): append_text(text)

# Matrices
with tabs[5]:
    with st.expander("Insert Matrix"):
        matrix_type = st.selectbox("Matrix Type", ["pmatrix", "bmatrix", "vmatrix", "Bmatrix"])
        rows = st.number_input("Rows", 1, 5, 2)
        cols = st.number_input("Cols", 1, 5, 2)
        elements = []
        for i in range(rows):
            row = []
            for j in range(cols):
                row.append(st.text_input(f"Element [{i+1},{j+1}]", key=f"matrix_{i}_{j}"))
            elements.append(row)
        if st.button("Insert Matrix"):
            matrix_content = " \\\\ ".join(" & ".join(row) for row in elements if any(row))
            matrix = f"\\begin{{{matrix_type}}} {matrix_content} \\end{{{matrix_type}}}"
            append_text(matrix)

# Chemistry
with tabs[6]:
    with st.expander("Chemistry (\\ce{})"):
        cols = st.columns(3)
        chem = ["\\ce{H2O}", "\\ce{CO2}", "\\ce{A -> B}", "\\ce{A + B <=> C}", "\\ce{H2SO4}"]
        for i, c in enumerate(chem):
            with cols[i%3]:
                if st.button(c): append_text(c)
        custom_chem = st.text_input("Custom \\ce{}")
        if st.button("Insert Custom Chemistry"): append_text(f"\\ce{{{custom_chem}}}")

# Physics
with tabs[7]:
    with st.expander("Physics (\\dv, \\grad, etc.)"):
        cols = st.columns(3)
        physics = ["\\dv{f}{x}", "\\grad{\\psi}", "\\curl{\\mathbf{A}}", "\\div{\\mathbf{F}}", "\\pdv{f}{x,y}"]
        for i, p in enumerate(physics):
            with cols[i%3]:
                if st.button(p): append_text(p)
        custom_deriv = st.text_input("Custom Derivative (e.g., f,x)", placeholder="function,variable")
        if st.button("Insert Custom Derivative"):
            if "," in custom_deriv:
                f, x = custom_deriv.split(",", 1)
                append_text(f"\\dv{{{f}}}{{{x}}}")

# Output
st.text_area("LaTeX Output:", st.session_state.latex, key="latex_out", height=100)

# Preview
st.write("Preview:")
if st.session_state.latex and not st.session_state.latex.startswith("Invalid") and not st.session_state.latex.startswith("Parse error"):
    st.latex(st.session_state.latex)
    components.html(f"""
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <div id="mathjax-preview">$${st.session_state.latex}$</div>
    <script>MathJax.typeset();</script>
    """, height=150)
else:
    st.info("Enter valid input or fix errors.")

# Copy and export
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Copy LaTeX"):
        st.code(st.session_state.latex)
with col2:
    if st.button("Copy for Word"):
        st.info("MathML approximation: " + st.session_state.latex.replace('\\', ''))
with col3:
    img_b64 = latex_to_image(st.session_state.latex)
    if img_b64:
        st.image(f"data:image/png;base64,{img_b64}")
        if st.button("Download Image"):
            st.download_button("Download PNG", data=base64.b64decode(img_b64), file_name="equation.png", mime="image/png")
with col4:
    pdf_b64 = latex_to_pdf(st.session_state.latex)
    if pdf_b64:
        if st.button("Download PDF"):
            st.download_button("Download PDF", data=base64.b64decode(pdf_b64), file_name="equation.pdf", mime="application/pdf")

# Reset and undo
col1, col2 = st.columns(2)
with col1:
    if st.button("Reset"):
        for key in ["formula", "latex"]: setattr(st.session_state, key, "")
        st.rerun()
with col2:
    if st.button("Undo") and st.session_state.history:
        st.session_state.formula, st.session_state.latex = st.session_state.history[-1]
        st.session_state.history.pop(-1)
        st.rerun()
