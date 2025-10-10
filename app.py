import streamlit as st
import sympy as sp
from functools import partial
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

# Function to validate formula
def is_valid_formula(formula):
    if not formula.strip():
        return False, "Formula is empty."
    # Check for trailing operators
    if formula.strip()[-1] in ['+', '-', '*', '/', '^', '_']:
        return False, "Formula ends with an incomplete operator."
    # Check for incomplete function calls (e.g., 'sqrt(', 'Integral(')
    incomplete_functions = ['sqrt(', 'log(', 'Integral(', 'Derivative(']
    for func in incomplete_functions:
        if formula.strip().endswith(func):
            return False, f"Incomplete function call: '{func}' is missing arguments."
    # Check for unbalanced parentheses
    if formula.count('(') != formula.count(')'):
        return False, "Unbalanced parentheses in formula."
    # Check for consecutive commas in function arguments
    if re.search(r',\s*,', formula):
        return False, "Invalid function arguments: consecutive commas detected."
    # Check for empty function arguments (e.g., 'Integral(, x)')
    if re.search(r'\(\s*,', formula):
        return False, "Invalid function arguments: empty argument detected."
    # Check for incomplete Integral or Derivative (missing integrand/function)
    if re.search(r'(Integral|Derivative)\(\s*,', formula):
        return False, "Integral/Derivative is missing the function to integrate/differentiate."
    return True, ""

# Function to update LaTeX from formula
def update_latex():
    formula = st.session_state.formula
    valid, error_msg = is_valid_formula(formula)
    if not valid:
        st.session_state.latex = f"Invalid formula: {error_msg}"
        st.error(error_msg)
        return
    try:
        # Replace ^ with ** for exponentiation
        parsed_formula = formula.replace("^", "**")
        
        # Replace log with sp.log
        parsed_formula = re.sub(r'\blog\(', 'sp.log(', parsed_formula)
        
        # Replace Integral with valid SymPy syntax, auto-insert '1' if integrand is empty or whitespace
        parsed_formula = re.sub(r'Integral\(\s*([^,)]*?)\s*,\s*x\s*\)', 
                                lambda m: 'sp.Integral(' + (m.group(1).strip() if m.group(1).strip() else '1') + ', x)', 
                                parsed_formula)
        # Same for Derivative
        parsed_formula = re.sub(r'Derivative\(\s*([^,)]*?)\s*,\s*x\s*\)', 
                                lambda m: 'sp.Derivative(' + (m.group(1).strip() if m.group(1).strip() else '1') + ', x)', 
                                parsed_formula)
        
        # Define local namespace with SymPy functions
        local_dict = {
            "sp": sp,
            "sqrt": sp.sqrt,
            "log": sp.log,
            "sin": sp.sin,
            "cos": sp.cos,
            "tan": sp.tan,
            "exp": sp.exp
        }
        expr = sp.sympify(parsed_formula, locals=local_dict)
        st.session_state.latex = sp.latex(expr)
    except Exception as e:
        error_msg = f"Invalid formula: {str(e)}"
        st.session_state.latex = error_msg
        st.error(error_msg)

# Function to create image from LaTeX with proportional width
def latex_to_image(latex_str):
    try:
        # Create temporary figure to measure text width
        temp_fig = plt.figure(figsize=(10, 2))
        temp_ax = temp_fig.add_subplot(111)
        temp_ax.axis('off')
        t = temp_ax.text(0.5, 0.5, f'${latex_str}$', fontsize=20, ha='center', va='center')
        
        # Render to get bounding box
        temp_fig.canvas.draw()
        bbox = t.get_window_extent(temp_fig.canvas.get_renderer())
        bbox_inches = bbox.transformed(temp_fig.dpi_scale_trans.inverted())
        plt.close(temp_fig)
        
        # Calculate proportional figure size with slight padding
        width = bbox_inches.width + 0.3
        height = bbox_inches.height + 0.2
        
        # Create final figure with calculated size
        fig = plt.figure(figsize=(width, height))
        fig.patch.set_facecolor('white')
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.text(0.5, 0.5, f'${latex_str}$', fontsize=20, ha='center', va='center')
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.05, facecolor='white')
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
    ("√", "sqrt()"),
    ("÷", "/"),
    ("∫", "Integral(1, x)"),
    ("d/dx", "Derivative(1, x)"),
    ("log", "log()"),
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
        
        # JavaScript for clipboard operations
        copy_js = """
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
        <script>
        function copyLatexText() {
            const button = document.getElementById('copy-latex-btn');
            const latexCode = document.getElementById('latex-content').innerText;
            navigator.clipboard.writeText(latexCode).then(() => {
                button.style.backgroundColor = '#00ff00';
                button.innerText = '✓ Copied!';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy LaTeX';
                }, 1500);
            }, (err) => {
                console.error('Failed to copy:', err);
                button.style.backgroundColor = '#ff0000';
                button.innerText = 'Failed';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy LaTeX';
                }, 1500);
            });
        }

        async function copyForWord() {
            const button = document.getElementById('copy-word-btn');
            const latexCode = document.getElementById('latex-content').innerText;
            try {
                const mathml = await MathJax.tex2mmlPromise(latexCode);
                const htmlContent = `<!DOCTYPE html><html><body>${mathml}</body></html>`;
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

        async function copyAsImage() {
            const button = document.getElementById('copy-image-btn');
            const imgElement = document.getElementById('latex-image');
            if (!imgElement) {
                button.style.backgroundColor = '#ff0000';
                button.innerText = 'No Image';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy as Image';
                }, 1500);
                return;
            }
            try {
                button.innerText = 'Copying...';
                const response = await fetch(imgElement.src);
                const blob = await response.blob();
                const clipboardItem = new ClipboardItem({ 'image/png': blob });
                await navigator.clipboard.write([clipboardItem]);
                button.style.backgroundColor = '#00ff00';
                button.innerText = '✓ Copied!';
                setTimeout(() => {
                    button.style.backgroundColor = '#0f80c1';
                    button.innerText = 'Copy as Image';
                }, 1500);
            } catch (err) {
                console.error('Failed to copy:', err);
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
        
        # HTML content for buttons
        html_content = f"""
        {copy_js}
        <div id="latex-content" style="display: none;">{st.session_state.latex}</div>
        """
        if img_b64:
            html_content += f"""
            <img id="latex-image" src="data:image/png;base64,{img_b64}" style="max-width: 100%; margin-top: 10px;" />
            """
        else:
            html_content += """
            <p style="color: #ff0000;">No image available.</p>
            """
        
        html_content += """
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
            • <strong>Copy for Word</strong>: Copies MathML for direct pasting into Word<br>
            • <strong>Copy as Image</strong>: Copies as PNG image (works in most applications)
        </p>
        """
        
        components.html(html_content, height=320)
        
    except Exception as e:
        st.error(f"Unable to render LaTeX: {str(e)}")
else:
    st.write("Enter a valid formula to see the LaTeX rendering.")
