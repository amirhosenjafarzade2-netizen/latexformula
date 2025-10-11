# utils.py
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import re
from functools import lru_cache
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import streamlit as st
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

plt.switch_backend('Agg')

def is_valid_formula(formula, mode):
    logger.debug(f"Validating formula: {formula}, mode: {mode}")
    if not formula.strip():
        return False, "Formula is empty."
    if formula.strip()[-1] in ['+', '-', '*', '/', '^', '_']:
        return False, "Formula ends with an incomplete operator."
    if mode == "SymPy" and ('{' in formula or '}' in formula):
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

def get_locals(formula):
    logger.debug(f"Getting locals for formula: {formula}")
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
            if '_' in var and st.session_state.get('mode') == "LaTeX":
                base, subscript = var.split('_', 1)
                symbol._latex_repr = f"{base}_{{{subscript}}}"
            local_dict[var] = symbol
    return local_dict

def update_latex():
    try:
        if st.session_state.get('subscript_trigger', False):
            logger.debug("Skipping update due to subscript trigger")
            return
        formula = st.session_state.formula
        mode = st.session_state.mode
        logger.debug(f"Updating LaTeX for formula: {formula}, mode: {mode}")
        if mode == "LaTeX":
            st.session_state.latex = formula
            return
        valid, error_msg = is_valid_formula(formula, mode)
        if not valid:
            st.session_state.latex = f"Invalid formula: {error_msg}"
            st.error(error_msg)
            logger.error(f"Formula validation failed: {error_msg}")
            return
        parsed_formula = formula.replace("^", "**")
        local_dict = get_locals(parsed_formula)
        transformations = standard_transformations + (implicit_multiplication_application,)
        expr = parse_expr(parsed_formula, local_dict=local_dict, transformations=transformations)
        latex_str = sp.latex(expr, order='none')
        latex_str = re.sub(r'\\frac\{d\}\{d x\}\s*([a-zA-Z])', r'\\frac{d\1}{dx}', latex_str)
        latex_str = re.sub(r'\\frac\{d\}\{d x\}\s*\\left\(([^)]+)\\right\)', r'\\frac{d(\\1)}{dx}", latex_str)
        st.session_state.latex = latex_str
        st.session_state.history.append((formula, latex_str))
        if len(st.session_state.history) > 10:
            st.session_state.history.pop(0)
        logger.debug(f"LaTeX updated: {latex_str}")
    except Exception as e:
        error_msg = f"Invalid formula: {str(e)}"
        st.session_state.latex = error_msg
        st.error(error_msg)
        logger.error(f"Error updating LaTeX: {str(e)}")

def sync_to_sympy():
    logger.debug("Syncing LaTeX to SymPy")
    latex = st.session_state.latex
    if not latex or st.session_state.mode != "LaTeX":
        st.warning("Switch to LaTeX mode first.")
        logger.warning("Sync attempted in wrong mode or with empty LaTeX")
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
    logger.debug(f"Synced to SymPy: {sympy_approx}")
    st.rerun()

@lru_cache(maxsize=100)
def latex_to_image(latex_str):
    logger.debug(f"Generating image for LaTeX: {latex_str}")
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
        logger.error(f"Image generation failed: {str(e)}")
        return None

def latex_to_pdf(latex_str):
    logger.debug(f"Generating PDF for LaTeX: {latex_str}")
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
        plt.savefig(buf, format='pdf', dpi=300, bbox_inches='tight', pad_inches=0.05, facecolor='white')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        logger.error(f"PDF generation failed: {str(e)}")
        return None

def append_to_formula(symbol):
    logger.debug(f"Appending symbol: {symbol}")
    temp_formula = st.session_state.formula
    mode = st.session_state.mode
    text = symbol.get("LaTeX", symbol.get("SymPy", "")) if mode == "LaTeX" else symbol.get("SymPy", symbol.get("LaTeX", ""))
    text = text.replace('_{}', '_').replace('^{}', '^') if mode == "SymPy" else text
    temp_formula += text
    st.session_state.temp_formula = temp_formula
    st.session_state.formula = temp_formula
    update_latex()

def add_subscript(subscript, selected_param):
    logger.debug(f"Adding subscript: {subscript} to parameter: {selected_param}")
    if not subscript.strip():
        st.error("Subscript cannot be empty.")
        logger.error("Empty subscript provided")
        return
    if not re.match(r'^[\w\d]+$', subscript):
        st.error("Subscript must be alphanumeric.")
        logger.error("Invalid subscript format")
        return
    formula = st.session_state.formula
    if not formula.strip():
        st.error("Formula is empty. Enter a parameter to subscript.")
        logger.error("Empty formula for subscript")
        return
    if st.session_state.mode == "LaTeX":
        st.warning("Subscript adding is optimized for SymPy mode. In LaTeX, use manual _{sub} syntax.")
        logger.warning("Subscript attempted in LaTeX mode")
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
        logger.debug(f"Subscript applied: {new_formula}")
    else:
        st.error("Selected parameter not found in formula.")
        logger.error(f"Parameter {selected_param} not found in formula")
