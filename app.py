# Streamlit app to convert math formulas to LaTeX, with 3 copy options
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
        ax.text(0.5, 0.5, f'${latex_str}$', fontsize=28, ha='center', va='center')
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.3, facecolor='white')
        plt.close(fig)
        buf.seek(0)
        
        img_b64 = base64.b64encode(buf.read()).decode()
        return img_b64
    except Exception as e:
        st.error(f"Image generation error: {e}")
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
if st.session_state.latex:
    try:
        st.latex(st.session_state.latex)
        
        # Generate image version
        img_b64 = latex_to_image(st.session_state.latex)
        
        # Escape LaTeX for JavaScript
        latex_escaped = st.session_state.latex.replace("\\", "\\\\").replace("'", "\\'")
        
        # HTML with inline onclick handlers
        html_content = f"""
        <div id="latex-content" style="display: none;">{st.session_state.latex}</div>
        {f'<img id="latex-image" src="data:image/png;base64,{img_b64}" style="display: none;" />' if img_b64 else ''}
        <div style="display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap;">
            <button onclick="navigator.clipboard.writeText(document.getElementById('latex-content').innerText).then(() => alert('✓ Copied LaTeX!')).catch(() => alert('Failed to copy'))" 
                    style="background-color: #0f80c1; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                Copy LaTeX
            </button>
            
            <button onclick="
                const latexCode = document.getElementById('latex-content').innerText;
                const htmlContent = '<math><mi>' + latexCode + '</mi></math>';
                const blob = new Blob([htmlContent], {{type: 'text/html'}});
                navigator.clipboard.write([new ClipboardItem({{'text/html': blob}})]).then(() => alert('✓ Copied for Word!')).catch(() => alert('Failed'));
            " 
            style="background-color: #0f80c1; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                Copy for Word
            </button>
            
            <button onclick="
                const img = document.getElementById('latex-image');
                if (!img) {{ alert('No image available'); return; }}
                fetch(img.src)
                .then(res => res.blob())
                .then(blob => navigator.clipboard.write([new ClipboardItem({{'image/png': blob}})]))
                .then(() => alert('✓ Copied Image!'))
                .catch(err => alert('Failed: ' + err.message));
            " 
            style="background-color: #0f80c1; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                Copy as Image
            </button>
        </div>
        <p style="font-size: 12px; color: #666; margin-top: 10px;">
            • <strong>Copy LaTeX</strong>: Copies the LaTeX code as text<br>
            • <strong>Copy for Word</strong>: Copies formatted text for Word<br>
            • <strong>Copy as Image</strong>: Copies as PNG image (works anywhere)
        </p>
        """
        
        st.markdown(html_content, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error rendering LaTeX: {e}")
else:
    st.info("Enter a formula to see it rendered")
