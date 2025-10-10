# Streamlit app to convert math formulas to LaTeX, using JavaScript for clipboard copy
# Run with: streamlit run app.py

import streamlit as st
import sympy as sp
from functools import partial
import streamlit.components.v1 as components

# Initialize session state
if "formula" not in st.session_state:
    st.session_state.formula = ""

if "latex" not in st.session_state:
    st.session_state.latex = ""

# Function to update LaTeX from formula
def update_latex():
    try:
        parsed_formula = st.session_state.formula.replace("^", "**")
        expr = sp.sympify(parsed_formula)
        st.session_state.latex = sp.latex(expr)
    except Exception as e:
        st.session_state.latex = "Invalid formula"

# Function to append text to formula and update LaTeX
def append_to_formula(text):
    st.session_state.formula += text
    update_latex()

# JavaScript for copying text to clipboard
copy_js = """
<script>
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        alert('Copied to clipboard!');
    }, function(err) {
        alert('Failed to copy: ' + err);
    });
}
</script>
"""

# UI
st.title("Formula to LaTeX Converter")

# First entry bar: Formula input
st.text_input("Enter formula (e.g., x^2 + sqrt(y))", key="formula", on_change=update_latex)

# Buttons for symbols
st.write("Math tools:")
cols = st.columns(8)

buttons = [
    ("√", "sqrt("),       # radical
    ("÷", "/"),           # division
    ("∫", "Integral(, x)"),  # integral
    ("d/dx", "Derivative(, x)"),  # derivative
    ("log", "log("),      # log
    ("×", "*"),           # multiplication
    ("^", "^"),           # power
    ("_", "_")            # subscript
]

for i, (label, text) in enumerate(buttons):
    with cols[i]:
        st.button(label, on_click=partial(append_to_formula, text))

# Second entry bar: LaTeX version (editable)
st.text_input("LaTeX version", key="latex")

# Copy button using JavaScript
components.html(f"""
{copy_js}
<button onclick="copyToClipboard('{st.session_state.latex}')">Copy LaTeX</button>
""")

# Render the LaTeX
st.write("Rendered:")
try:
    st.latex(st.session_state.latex)
except:
    st.write("Unable to render LaTeX.")
