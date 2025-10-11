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
if "subscript_trigger" not in st.session_state:
    st.session_state.subscript_trigger = False
if "last_valid_formula" not in st.session_state:
    st.session_state.last_valid_formula = ""

# Function to validate formula
def is_valid_formula(formula):
    if not formula.strip():
        return False, "Formula is empty."
    if formula.strip()[-1] in ['+', '-', '*', '/', '^', '_']:
        return False, "Formula ends with an incomplete operator."
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
        "sp": sp, "sqrt": sp.sqrt, "log": sp.log, "sin": sp.sin, "cos": sp.cos,
        "tan": sp.tan, "cot": sp.cot, "sec": sp.sec, "csc": sp.csc, "asin": sp.asin,
        "acos": sp.acos, "atan": sp.atan, "sinh": sp.sinh, "cosh": sp.cosh,
        "tanh": sp.tanh, "exp": sp.exp, "Sum": sp.Sum, "Limit": sp.Limit,
        "Integral": sp.Integral, "Derivative": sp.Derivative, "oo": sp.oo,
        "pi": sp.pi, "e": sp.E
    }
    
    # Add Greek letters and common symbols
    greek_symbols = {
        'phi': 'phi', 'kappa': 'kappa', 'mu': 'mu', 'alpha': 'alpha', 'beta': 'beta',
        'gamma': 'gamma', 'delta': 'delta', 'Delta': 'Delta', 'epsilon': 'epsilon',
        'zeta': 'zeta', 'eta': 'eta', 'theta': 'theta', 'Theta': 'Theta',
        'iota': 'iota', 'lambda': 'lambda', 'Lambda': 'Lambda', 'nu': 'nu',
        'xi': 'xi', 'rho': 'rho', 'sigma': 'sigma', 'Sigma': 'Sigma', 'tau': 'tau',
        'Phi': 'Phi', 'omega': 'omega', 'Omega': 'Omega', 'degree': 'degree',
        'approx': 'approx', 'ne': 'ne', 'ge': 'ge', 'le': 'le'
    }
    
    for name, sym_name in greek_symbols.items():
        local_dict[name] = sp.Symbol(sym_name)
    
    # Automatically add undefined variables as symbols, including subscripted ones
    variables = re.findall(r'\b[a-zA-Z]\w*(?:_\w+)?\b', formula)
    reserved = ['sqrt', 'log', 'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'asin', 'acos', 'atan',
                'sinh', 'cosh', 'tanh', 'exp', 'Sum', 'Limit', 'Integral', 'Derivative', 'oo', 'pi', 'e']
    
    for var in variables:
        if var not in local_dict and var not in reserved:
            local_dict[var] = sp.Symbol(var)
    
    return local_dict

# Function to update LaTeX from formula
def update_latex():
    if st.session_state.subscript_trigger:
        return
    formula = st.session_state.formula
    valid, error_msg = is_valid_formula(formula)
    if not valid:
        st.session_state.latex = f"Invalid formula: {error_msg}"
        return
    try:
        parsed_formula = formula.replace("^", "**")
        local_dict = get_locals(parsed_formula)
        expr = parse_expr(parsed_formula, local_dict=local_dict, transformations=standard_transformations)
        latex_str = sp.latex(expr, order='none')
        # Clean up LaTeX for derivatives
        latex_str = re.sub(r'\\frac\{d\}\{d x\}\s*([a-zA-Z])', r'\\frac{d\1}{dx}', latex_str)
        latex_str = re.sub(r'\\frac\{d\}\{d x\}\s*\\left\(([^)]+)\\right\)', r'\\frac{d(\\1)}{dx}', latex_str)
        st.session_state.latex = latex_str
        st.session_state.last_valid_formula = formula  # Store last valid formula
    except Exception as e:
        error_msg = f"Parsing error: {str(e)}"
        st.session_state.latex = error_msg

# Callback for formula input change
def on_formula_change():
    st.session_state.formula = st.session_state.formula_input
    update_latex()

# Callback for subscript application
def on_apply_subscript():
    parameters = get_parameters(st.session_state.formula)
    if not parameters:
        st.error("No parameters found in formula.")
        return
    
    selected_param = st.session_state.selected_param
    subscript_input = st.session_state.subscript_input
    
    if selected_param not in parameters:
        st.error("Selected parameter not found in formula.")
        return
    
    if not subscript_input.strip():
        st.error("Subscript cannot be empty.")
        return
    if not re.match(r'^[\w\d]+$', subscript_input):
        st.error("Subscript must be alphanumeric.")
        return
    
    # Find and replace the last occurrence of the parameter
    formula = st.session_state.formula
    param_positions = [m.start() for m in re.finditer(r'\b' + re.escape(selected_param) + r'\b', formula)]
    if param_positions:
        last_pos = param_positions[-1]
        new_formula = formula[:last_pos] + f"{selected_param}_{subscript_input}" + formula[last_pos + len(selected_param):]
        st.session_state.formula = new_formula
        st.session_state.formula_input = new_formula  # Update the input widget value
        update_latex()
        st.success(f"Applied subscript '{subscript_input}' to '{selected_param}'")
    else:
        st.error("Parameter replacement failed.")

# Function to get parameters from formula
def get_parameters(formula):
    params = re.findall(r'\b[a-zA-Z]\w*(?:_\w+)?\b', formula)
    # Filter out reserved words
    reserved = ['sqrt', 'log', 'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'asin', 'acos', 'atan',
                'sinh', 'cosh', 'tanh', 'exp', 'Sum', 'Limit', 'Integral', 'Derivative', 'oo', 'pi', 'e']
    return [p for p in params if p not in reserved]

# Cached function to create image from LaTeX (unchanged)
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
        img_b64 = base64.b64encode(buf.read()).decode()
        return img_b64
    except:
        return None

# Function to append text to formula using callback
def append_to_formula(text):
    new_formula = st.session_state.formula + text
    st.session_state.formula = new_formula
    st.session_state.formula_input = new_formula
    update_latex()

# UI
st.title("Formula to LaTeX Converter")

# Store current formula in session state for widget
if "formula_input" not in st.session_state:
    st.session_state.formula_input = st.session_state.formula

# Formula input - must be before any modifications
formula_input = st.text_input(
    "Enter formula (e.g., x^2 + sqrt(y))", 
    value=st.session_state.formula_input,
    key="formula_input",
    on_change=on_formula_change,
    help="Type your formula here. Use ^ for exponents, _ for subscripts (after applying via button)"
)

# Update formula from input
st.session_state.formula = formula_input

# Update LaTeX when formula changes
if st.session_state.formula != st.session_state.last_valid_formula:
    update_latex()

# Reset button - place before subscript section
if st.button("Reset Formula", key="reset"):
    st.session_state.formula = ""
    st.session_state.formula_input = ""
    st.session_state.latex = ""
    st.session_state.last_valid_formula = ""
    st.session_state.subscript_trigger = False
    st.rerun()

# Subscript input section
st.write("**Add subscript to a parameter:**")
parameters = get_parameters(st.session_state.formula)
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if parameters:
        st.session_state.selected_param = st.selectbox(
            "Select parameter:", 
            parameters, 
            key="param_select",
            index=0 if parameters else None
        )
    else:
        st.write("No parameters")

with col2:
    st.session_state.subscript_input = st.text_input(
        "Enter subscript (e.g., 1, oil, gas)", 
        key="subscript_input",
        placeholder="Type subscript here"
    )

with col3:
    if st.button("Apply Subscript", key="apply_subscript_btn", on_click=on_apply_subscript):
        pass  # Callback handles the logic

if not parameters:
    st.info("Enter a formula with parameters (like x, y, etc.) to enable subscripting.")

# Symbol selection tabs
st.write("**Math tools:**")
tab_names = ["Basic", "Brackets", "Trigonometry", "Hyperbolic", "Calculus", "Constants", "Greek"]
tabs = st.tabs(tab_names)

symbol_lists = {
    "Basic": [
        ("√", "sqrt()"), ("log", "log()"), ("exp", "exp()"),
        ("÷", "/"), ("×", "*"), ("^", "^"), ("+", "+"), ("-", "-")
    ],
    "Brackets": [
        ("(", "("), (")", ")"), ("[", "["), ("]", "]"), ("{", "{"), ("}", "}")
    ],
    "Trigonometry": [
        ("sin", "sin()"), ("cos", "cos()"), ("tan", "tan()"), 
        ("cot", "cot()"), ("sec", "sec()"), ("csc", "csc()")
    ],
    "Hyperbolic": [
        ("sinh", "sinh()"), ("cosh", "cosh()"), ("tanh", "tanh()")
    ],
    "Calculus": [
        ("∫", "Integral(x, (t, 0, x))"), ("d/dx", "Derivative(x, x)"),
        ("∑", "Sum(n, (n, 0, oo))"), ("lim", "Limit(x, x, 0)")
    ],
    "Constants": [
        ("π", "pi"), ("e", "e"), ("∞", "oo")
    ],
    "Greek": [
        ("α", "alpha"), ("β", "beta"), ("γ", "gamma"), ("δ", "delta"),
        ("φ", "phi"), ("κ", "kappa"), ("μ", "mu"), ("θ", "theta"), ("λ", "lambda"), ("ω", "omega")
    ]
}

for idx, tab in enumerate(tabs):
    tab_name = tab_names[idx]
    with tab:
        if symbol_lists[tab_name]:
            symbols = symbol_lists[tab_name]
            selected = st.radio(
                f"Select {tab_name.lower()} symbol:",
                options=[label for label, _ in symbols],
                key=f"radio_{tab_name.lower()}_{idx}",
                horizontal=True if len(symbols) <= 6 else False
            )
            if selected:
                for label, text in symbols:
                    if label == selected:
                        st.button(
                            f"Insert {label}", 
                            key=f"btn_{tab_name.lower()}_{text.replace('(', '').replace(')', '')}_{idx}",
                            on_click=partial(append_to_formula, text)
                        )
                        break

# LaTeX output display
st.subheader("LaTeX Output")
st.text_area("LaTeX code:", value=st.session_state.latex, key="latex_display", height=50)

# Render LaTeX and copy buttons
st.write("**Rendered Formula:**")
if st.session_state.latex and not st.session_state.latex.startswith("Invalid") and not st.session_state.latex.startswith("Parsing"):
    try:
        st.latex(st.session_state.latex)
        
        # Generate and display image
        img_b64 = latex_to_image(st.session_state.latex)
        if img_b64:
            st.image(f"data:image/png;base64,{img_b64}", use_column_width=True)
            
            # Copy buttons using components
            components.html(f"""
            <div style="display: flex; gap: 10px; margin-top: 10px;">
                <button onclick="navigator.clipboard.writeText('{st.session_state.latex}').then(() => alert('LaTeX copied!'))" 
                        style="background: #0f80c1; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">
                    Copy LaTeX
                </button>
                <button onclick="alert('Copy image manually or use screenshot')" 
                        style="background: #28a745; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">
                    Save Image
                </button>
            </div>
            """, height=100)
        else:
            st.warning("Could not generate image preview.")
            
    except Exception as e:
        st.error(f"Rendering error: {str(e)}")
else:
    if st.session_state.formula:
        st.info("Enter a valid formula to see LaTeX rendering.")
    else:
        st.info("Enter a formula above to get started.")
