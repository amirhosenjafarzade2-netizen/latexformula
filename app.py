# Streamlit app to convert math formulas to LaTeX, with 3 copy options
# Run with: streamlit run app.py
import streamlit as st
import sympy as sp
from functools import partial
import pyperclip
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
        st.session_state.latex = f"Invalid formula: {str(e)}"
        st.error(f"Invalid formula: {str(e)}")

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
if st.session_state.latex:
    try:
        st.latex(st.session_state.latex)
        
        # Generate image version
        img_b64 = latex_to_image(st.session_state.latex) if st.session_state.latex else None
        
        # Copy buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Copy LaTeX", key="copy_latex"):
                try:
                    pyperclip.copy(st.session_state.latex)
                    st.success("LaTeX code copied to clipboard!")
                except Exception as e:
                    st.error(f"Failed to copy LaTeX: {str(e)}")
        with col2:
            if st.button("Copy for Word", key="copy_word"):
                try:
                    html_content = f'<span style="font-family: \'Cambria Math\', \'Times New Roman\'; font-size: 14pt;">${st.session_state.latex}$</span>'
                    pyperclip.copy(html_content)
                    st.success("Copied for Word (paste into Word equation editor)!")
                except Exception as e:
                    st.error(f"Failed to copy for Word: {str(e)}")
        with col3:
            if st.button("Copy as Image", key="copy_image"):
                if img_b64:
                    st.image(f"data:image/png;base64,{img_b64}")
                    st.info("Image displayed above. Right-click to copy or save.")
                else:
                    st.error("No image available to copy.")
        
        # Display image if generated
        if img_b64:
            st.image(f"data:image/png;base64,{img_b64}", caption="Rendered formula as image")
        
        # Instructions
        st.markdown("""
        - **Copy LaTeX**: Copies the LaTeX code as text
        - **Copy for Word**: Copies formatted text (paste into Word equation editor)
        - **Copy as Image**: Displays the image (right-click to copy or save)
        """)
        
    except Exception as e:
        st.error(f"Unable to render LaTeX: {str(e)}")
else:
    st.write("Enter a formula to see the LaTeX rendering.")
