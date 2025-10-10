# Streamlit app to convert math formulas to LaTeX, with 3 copy options
# Run with: streamlit run app.py
import streamlit as st
import sympy as sp
from functools import partial
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg')

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

# Function to create image from LaTeX
def latex_to_image(latex_str):
    try:
        fig = plt.figure(figsize=(10, 2))
        fig.patch.set_facecolor('white')
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', fontsize=24, ha='center', va='center')
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.3, facecolor='white')
        plt.close(fig)
        buf.seek(0)
        
        img_b64 = base64.b64encode(buf.read()).decode()
        return img_b64
    except:
        return None

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
    
    # Generate image version
    img_b64 = latex_to_image(st.session_state.latex) if st.session_state.latex else None
    
    # HTML with inline onclick handlers
    html_content = f"""
    <div id="latex-content" style="display: none;">{st.session_state.latex}</div>
    {'<img id="latex-image" src="data:image/png;base64,' + img_b64 + '" style="display: none;" />' if img_b64 else ''}
    <div style="display: flex; gap: 10px; margin-top: 10px;">
        <button onclick="navigator.clipboard.writeText(document.getElementById('latex-content').innerText); alert('Copied LaTeX!')" 
                style="background-color: #0f80c1; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
            Copy LaTeX
        </button>
        
        <button onclick="
            const htmlContent = '<span style=\\'font-family: Cambria Math;\\'>${st.session_state.latex}</span>';
            navigator.clipboard.write([
                new ClipboardItem({{'text/html': new Blob([htmlContent], {{type: 'text/html'}})}})
            ]).then(() => alert('Copied for Word!'));
        " 
        style="background-color: #0f80c1; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
            Copy for Word
        </button>
        
        <button onclick="
            fetch(document.getElementById('latex-image').src)
            .then(res => res.blob())
            .then(blob => navigator.clipboard.write([new ClipboardItem({{'image/png': blob}})]))
            .then(() => alert('Copied Image!'))
            .catch(err => alert('Failed to copy image'));
        " 
        style="background-color: #0f80c1; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
            Copy as Image
        </button>
    </div>
    <p style="font-size: 12px; color: #666; margin-top: 10px;">
        • <strong>Copy LaTeX</strong>: Copies LaTeX as text<br>
        • <strong>Copy for Word</strong>: Copies formatted LaTeX for Word<br>
        • <strong>Copy as Image</strong>: Copies PNG image
    </p>
    """
    
    st.markdown(html_content, unsafe_allow_html=True)
    
except Exception as e:
    st.write(f"Unable to render LaTeX: {e}")
