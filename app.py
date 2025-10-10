# Streamlit app to convert math formulas to LaTeX, with JavaScript for copying rendered LaTeX
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

# JavaScript for copying text to clipboard with button color change
copy_js = """
<script>
function copyToClipboard() {
    const text = document.getElementById('latex-content').innerText;
    navigator.clipboard.writeText(text).then(function() {
        const button = document.getElementById('copy-button');
        button.style.backgroundColor = '#00ff00'; // Green on success
        setTimeout(() => {
            button.style.backgroundColor = '#0f80c1'; // Revert to Streamlit blue
        }, 1000);
    }, function(err) {
        console.error('Failed to copy: ', err);
    });
}
</script>
"""

# Function to handle copy button click
def handle_copy():
    # Ensure the latest LaTeX is available for copying
    st.session_state.copy_triggered = True

# Initialize copy trigger
if "copy_triggered" not in st.session_state:
    st.session_state.copy_triggered = False

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

# Render the LaTeX
st.write("Rendered:")
try:
    st.latex(st.session_state.latex)
    # Hidden div to store LaTeX code for copying
    components.html(f"""
    {copy_js}
    <div id="latex-content" style="display: none;">{st.session_state.latex}</div>
    <button id="copy-button" onclick="copyToClipboard()" style="background-color: #0f80c1; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">Copy LaTeX</button>
    """, height=50)
except:
    st.write("Unable to render LaTeX.")
