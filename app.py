# This Streamlit app converts a simple math formula to LaTeX.
# Requires: pip install streamlit sympy pyperclip
# Run with: streamlit run this_file.py

import streamlit as st
import sympy as sp
from functools import partial
import pyperclip

# Initialize session state
if "formula" not in st.session_state:
    st.session_state.formula = ""

if "latex" not in st.session_state:
    st.session_state.latex = ""

# Function to update LaTeX from formula
def update_latex():
    try:
        # Replace ^ with ** for sympy parsing
        parsed_formula = st.session_state.formula.replace("^", "**")
        expr = sp.sympify(parsed_formula)
        st.session_state.latex = sp.latex(expr)
    except Exception as e:
        st.session_state.latex = "Invalid formula"

# Function to append text to formula and update LaTeX
def append_to_formula(text):
    st.session_state.formula += text
    update_latex()

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

# Copy button
if st.button("Copy LaTeX"):
    pyperclip.copy(st.session_state.latex)
    st.success("LaTeX copied to clipboard!")

# Render the LaTeX
st.write("Rendered:")
try:
    st.latex(st.session_state.latex)
except:
    st.write("Unable to render LaTeX.")
