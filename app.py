# Streamlit app to convert math formulas to LaTeX, with MathML copying for Word
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

# JavaScript for copying MathML to clipboard
copy_js = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
<script>
async function copyRenderedFormula() {
    const button = document.getElementById('copy-button');
    const latexCode = document.getElementById('latex-content').innerText;
    
    try {
        // Convert LaTeX to MathML using MathJax
        const mathml = await MathJax.tex2mmlPromise(latexCode);
        
        // Create HTML with MathML
        const htmlContent = `<!DOCTYPE html><html><body>${mathml}</body></html>`;
        
        // Copy as HTML (Word will understand this)
        const blob = new Blob([htmlContent], { type: 'text/html' });
        const clipboardItem = new ClipboardItem({ 'text/html': blob });
        
        await navigator.clipboard.write([clipboardItem]);
        
        button.style.backgroundColor = '#00ff00';
        button.innerText = 'Copied!';
        setTimeout(() => {
            button.style.backgroundColor = '#0f80c1';
            button.innerText = 'Copy for Word';
        }, 1500);
    } catch (err) {
        console.error('Failed to copy:', err);
        button.style.backgroundColor = '#ff0000';
        button.innerText = 'Failed';
        setTimeout(() => {
            button.style.backgroundColor = '#0f80c1';
            button.innerText = 'Copy for Word';
        }, 1500);
    }
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
    ("√", "sqrt("),
    ("÷", "/"),
    ("∫", "Integral(, x)"),
    ("d/dx", "Derivative(, x)"),
    ("log", "log("),
    ("×", "*"),
    ("^", "^"),
    ("_", "_")
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
    
    # Copy button with MathML support
    components.html(f"""
    {copy_js}
    <div id="latex-content" style="display: none;">{st.session_state.latex}</div>
    <button id="copy-button" onclick="copyRenderedFormula()" 
            style="background-color: #0f80c1; color: white; padding: 10px 20px; 
                   border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
        Copy for Word
    </button>
    <p style="font-size: 12px; color: #666; margin-top: 8px;">
        Click "Copy for Word" then paste (Ctrl+V) directly into Microsoft Word
    </p>
    """, height=100)
except:
    st.write("Unable to render LaTeX.")
