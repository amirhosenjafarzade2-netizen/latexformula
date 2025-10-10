# Streamlit app to convert math formulas to LaTeX, with 3 copy options
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

# JavaScript with all three copy functions
copy_js = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

<script>
MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']]
  }
};

// Function 1: Copy LaTeX code as text
function copyLatexText() {
    const button = document.getElementById('copy-latex-btn');
    const latexCode = document.getElementById('latex-content').innerText;
    
    navigator.clipboard.writeText(latexCode).then(function() {
        button.style.backgroundColor = '#00ff00';
        button.innerText = '✓ Copied!';
        setTimeout(() => {
            button.style.backgroundColor = '#0f80c1';
            button.innerText = 'Copy LaTeX';
        }, 1500);
    }, function(err) {
        console.error('Failed to copy:', err);
        button.style.backgroundColor = '#ff0000';
        button.innerText = 'Failed';
        setTimeout(() => {
            button.style.backgroundColor = '#0f80c1';
            button.innerText = 'Copy LaTeX';
        }, 1500);
    });
}

// Function 2: Copy as MathML for Word
async function copyForWord() {
    const button = document.getElementById('copy-word-btn');
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
        button.innerText = '✓ Copied!';
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

// Function 3: Copy as Image
async function copyAsImage() {
    const button = document.getElementById('copy-image-btn');
    const latexCode = document.getElementById('latex-content').innerText;
    
    try {
        // Create temporary div with rendered math
        const tempDiv = document.createElement('div');
        tempDiv.style.position = 'absolute';
        tempDiv.style.left = '-9999px';
        tempDiv.style.fontSize = '24px';
        tempDiv.style.padding = '20px';
        tempDiv.style.backgroundColor = 'white';
        tempDiv.innerHTML = `$$${latexCode}$$`;
        document.body.appendChild(tempDiv);
        
        // Wait for MathJax to render
        await MathJax.typesetPromise([tempDiv]);
        
        // Convert to canvas
        const canvas = await html2canvas(tempDiv, {
            backgroundColor: 'white',
            scale: 3
        });
        
        // Convert canvas to blob
        canvas.toBlob(async (blob) => {
            const item = new ClipboardItem({ 'image/png': blob });
            await navigator.clipboard.write([item]);
            
            document.body.removeChild(tempDiv);
            
            button.style.backgroundColor = '#00ff00';
            button.innerText = '✓ Copied!';
            setTimeout(() => {
                button.style.backgroundColor = '#0f80c1';
                button.innerText = 'Copy as Image';
            }, 1500);
        });
    } catch (err) {
        console.error('Failed to copy:', err);
        if (tempDiv.parentNode) document.body.removeChild(tempDiv);
        button.style.backgroundColor = '#ff0000';
        button.innerText = 'Failed';
        setTimeout(() => {
            button.style.backgroundColor = '#0f80c1';
            button.innerText = 'Copy as Image';
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
    
    # Three copy buttons
    components.html(f"""
    {copy_js}
    <div id="latex-content" style="display: none;">{st.session_state.latex}</div>
    <div style="display: flex; gap: 10px; margin-top: 10px;">
        <button id="copy-latex-btn" onclick="copyLatexText()" 
                style="background-color: #0f80c1; color: white; padding: 10px 20px; 
                       border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
            Copy LaTeX
        </button>
        <button id="copy-word-btn" onclick="copyForWord()" 
                style="background-color: #0f80c1; color: white; padding: 10px 20px; 
                       border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
            Copy for Word
        </button>
        <button id="copy-image-btn" onclick="copyAsImage()" 
                style="background-color: #0f80c1; color: white; padding: 10px 20px; 
                       border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
            Copy as Image
        </button>
    </div>
    <p style="font-size: 12px; color: #666; margin-top: 10px;">
        • <strong>Copy LaTeX</strong>: Copies the LaTeX code as text<br>
        • <strong>Copy for Word</strong>: Copies as editable equation for Microsoft Word<br>
        • <strong>Copy as Image</strong>: Copies as PNG image (works anywhere)
    </p>
    """, height=150)
except:
    st.write("Unable to render LaTeX.")
