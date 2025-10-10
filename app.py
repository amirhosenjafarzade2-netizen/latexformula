# Streamlit app to convert math formulas to LaTeX, with 3 copy options
# Run with: streamlit run app.py
import streamlit as st
import sympy as sp
from functools import partial
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
import streamlit.components.v1 as components

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
        st.session_state.latex = f"Invalid formula: {str(e)}"
        st.error(f"Invalid formula: {str(e)}")

# Function to create image from LaTeX with tightly proportional size
def latex_to_image(latex_str):
    try:
        # Estimate formula width based on character count (more precise scaling)
        formula_length = len(latex_str)
        # Width: 0.15 inches per character, min 0.8 inch, max 3 inches
        width = max(0.8, min(3, formula_length * 0.15))
        # Height: proportional to width, min 0.5 inch
        height = max(0.5, width * 0.25)
        fig = plt.figure(figsize=(width, height))
        fig.patch.set_facecolor('white')
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', fontsize=14, ha='center', va='center')
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.03, facecolor='white')
        plt.close(fig)
        buf.seek(0)
        
        img_b64 = base64.b64encode(buf.read()).decode()
        return img_b64
    except Exception as e:
        st.error(f"Image generation error: {str(e)}")
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

# Render the LaTeX and copy buttons
st.write("Rendered:")
if st.session_state.latex and not st.session_state.latex.startswith("Invalid formula"):
    try:
        st.latex(st.session_state.latex)
        
        # Generate image version
        img_b64 = latex_to_image(st.session_state.latex)
        
        # Streamlit buttons for copy operations
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Copy LaTeX", key="copy_latex"):
                try:
                    # Use JavaScript to copy LaTeX to clipboard
                    js_code = f"""
                    <script>
                    navigator.clipboard.writeText(`{st.session_state.latex}`).then(() => {{
                        alert('LaTeX copied to clipboard!');
                    }}, (err) => {{
                        console.error('Failed to copy:', err);
                        alert('Failed to copy LaTeX');
                    }});
                    </script>
                    """
                    components.html(js_code, height=0)
                except Exception as e:
                    st.error(f"Failed to copy LaTeX: {str(e)}")
        
        with col2:
            if st.button("Copy for Word", key="copy_word"):
                try:
                    # Use MathJax to generate MathML and copy via JavaScript
                    js_code = f"""
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
                    <script>
                    async function copyMathML() {{
                        try {{
                            const mathml = await MathJax.tex2mmlPromise(`{st.session_state.latex}`);
                            const htmlContent = `<!DOCTYPE html><html><body>${{mathml}}</body></html>`;
                            const blob = new Blob([htmlContent], {{ type: 'text/html' }});
                            const clipboardItem = new ClipboardItem({{ 'text/html': blob }});
                            await navigator.clipboard.write([clipboardItem]);
                            alert('MathML copied for Word!');
                        }} catch (err) {{
                            console.error('Failed to copy:', err);
                            alert('Failed to copy MathML');
                        }}
                    }}
                    copyMathML();
                    </script>
                    """
                    components.html(js_code, height=0)
                except Exception as e:
                    st.error(f"Failed to copy for Word: {str(e)}")
        
        with col3:
            if st.button("Copy as Image", key="copy_image"):
                if img_b64:
                    st.image(f"data:image/png;base64,{img_b64}", caption="Right-click to copy or save image")
                    # Attempt JavaScript-based image copy
                    js_code = f"""
                    <script>
                    async function copyImage() {{
                        try {{
                            const img = document.createElement('img');
                            img.src = 'data:image/png;base64,{img_b64}';
                            document.body.appendChild(img);
                            const response = await fetch(img.src);
                            const blob = await response.blob();
                            const clipboardItem = new ClipboardItem({{ 'image/png': blob }});
                            await navigator.clipboard.write([clipboardItem]);
                            alert('Image copied to clipboard!');
                            document.body.removeChild(img);
                        }} catch (err) {{
                            console.error('Failed to copy:', err);
                            alert('Failed to copy image. Right-click the displayed image to copy or save.');
                        }}
                    }}
                    copyImage();
                    </script>
                    """
                    components.html(js_code, height=0)
                else:
                    st.error("No image available to copy.")
        
        # Display image if generated
        if img_b64:
            st.image(f"data:image/png;base64,{img_b64}", caption="Rendered formula (proportional size)")
        
        # Instructions
        st.markdown("""
        - **Copy LaTeX**: Copies the LaTeX code as text
        - **Copy for Word**: Copies MathML for direct pasting into Word
        - **Copy as Image**: Copies as PNG image (or right-click to copy/save)
        """)
        
    except Exception as e:
        st.error(f"Unable to render LaTeX: {str(e)}")
else:
    st.write("Enter a valid formula to see the LaTeX rendering.")
