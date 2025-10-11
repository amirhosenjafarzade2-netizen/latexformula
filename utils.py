import streamlit as st
import streamlit.components.v1 as components
import re
from utils import (is_valid_formula, get_locals, update_latex, sync_to_sympy,
                  latex_to_image, latex_to_pdf, append_to_formula, add_subscript)
from symbols import (symbols_basic, symbols_brackets, symbols_trig, symbols_hyperbolic,
                    symbols_calculus, symbols_constants, symbols_greek, symbols_engineering,
                    symbols_petroleum)
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    # Initialize session state
    if "formula" not in st.session_state:
        st.session_state.formula = ""
    if "latex" not in st.session_state:
        st.session_state.latex = ""
    if "temp_formula" not in st.session_state:
        st.session_state.temp_formula = ""
    if "pending_formula" not in st.session_state:
        st.session_state.pending_formula = ""
    if "subscript_trigger" not in st.session_state:
        st.session_state.subscript_trigger = False
    if "mode" not in st.session_state:
        st.session_state.mode = "SymPy"
    if "history" not in st.session_state:
        st.session_state.history = []

    st.title("Formula to LaTeX Converter")

    # Mode and sync
    col1, col2 = st.columns([3, 1])
    with col2:
        st.session_state.mode = st.selectbox("Mode:", ["SymPy (parseable)", "LaTeX (direct)"], index=0 if st.session_state.mode == "SymPy" else 1)
        if st.button("Sync LaTeX → SymPy", key="sync_btn"):
            sync_to_sympy()
        if st.button("View History", key="history_btn"):
            st.write("Recent Formulas:", st.session_state.history)

    # Formula input
    st.text_input("Enter formula (e.g., x^2 + sqrt(y) for SymPy, or x^{2} + \\sqrt{y} for LaTeX)", key="formula", on_change=update_latex)

    # Apply pending changes
    if st.session_state.pending_formula and st.session_state.pending_formula != st.session_state.formula:
        if st.button("Apply Changes", key="apply_changes"):
            st.session_state.formula = st.session_state.pending_formula
            update_latex()
            st.rerun()

    # Symbol buttons
    st.write("Math tools:")
    tab_names = ["Basic", "Brackets", "Trigonometry", "Hyperbolic", "Calculus", "Constants", "Greek", "Engineering", "Petroleum", "Matrices", "Chemistry", "Physics"]
    tabs = st.tabs(tab_names)

    symbol_lists = [
        symbols_basic, symbols_brackets, symbols_trig, symbols_hyperbolic, symbols_calculus,
        symbols_constants, symbols_greek, symbols_engineering, symbols_petroleum
    ]

    for idx, tab in enumerate(tabs[:9]):  # Basic to Petroleum
        with tab:
            with st.form(key=f"symbol_form_{tab_names[idx]}"):
                symbols = symbol_lists[idx]
                num_cols = min(5, len(symbols))
                cols = st.columns(num_cols) if num_cols > 0 else [st]
                for i, symbol in enumerate(symbols):
                    col_idx = i % num_cols
                    with cols[col_idx]:
                        if st.form_submit_button(symbol["label"], key=f"btn_{tab_names[idx]}_{i}"):
                            logger.debug(f"Button clicked: {symbol['label']}")
                            append_to_formula(symbol)

    # Subscript
    parameters = re.findall(r'\b[a-zA-Z]\w*(?:_\w+)?\b', st.session_state.formula)
    if parameters:
        st.write("Add subscript to a parameter:")
        with st.form(key="subscript_form"):
            selected_param = st.selectbox("Select parameter:", parameters, key="param_select")
            subscript_input = st.text_input("Enter subscript (e.g., 1, oil)", key="subscript_input")
            if st.form_submit_button("Apply Subscript", key="apply_subscript"):
                add_subscript(subscript_input, selected_param)

    # Matrices
    with tabs[9]:
        if st.session_state.mode == "SymPy":
            st.warning("Matrices are only supported in LaTeX mode.")
        else:
            with st.expander("Insert Matrix"):
                with st.form(key="matrix_form"):
                    matrix_type = st.selectbox("Matrix Type", ["pmatrix", "bmatrix", "vmatrix", "Bmatrix"], key="matrix_type")
                    rows = st.number_input("Rows", 1, 5, 2, key="matrix_rows")
                    cols = st.number_input("Cols", 1, 5, 2, key="matrix_cols")
                    elements = []
                    for i in range(rows):
                        row = []
                        for j in range(cols):
                            row.append(st.text_input(f"Element [{i+1},{j+1}]", key=f"matrix_{i}_{j}"))
                        elements.append(row)
                    if st.form_submit_button("Insert Matrix", key="insert_matrix"):
                        matrix_content = " \\\\ ".join(" & ".join(row) for row in elements if any(row))
                        matrix = f"\\begin{{{matrix_type}}} {matrix_content} \\end{{{matrix_type}}}"
                        st.session_state.pending_formula = st.session_state.formula + matrix
                        update_latex()
                        logger.debug(f"Matrix inserted: {matrix}")

    # Chemistry
    with tabs[10]:
        if st.session_state.mode == "SymPy":
            st.warning("Chemistry notation is only supported in LaTeX mode.")
        else:
            with st.expander("Chemistry (\\ce{})"):
                with st.form(key="chemistry_form"):
                    cols = st.columns(3)
                    chem = ["\\ce{H2O}", "\\ce{CO2}", "\\ce{A -> B}", "\\ce{A + B <=> C}", "\\ce{H2SO4}"]
                    selected_chem = None
                    for i, c in enumerate(chem):
                        with cols[i % 3]:
                            if st.form_submit_button(c, key=f"chem_btn_{i}"):
                                selected_chem = c
                    custom_chem = st.text_input("Custom \\ce{}", key="custom_chem")
                    if st.form_submit_button("Insert Custom Chemistry", key="insert_chem"):
                        selected_chem = f"\\ce{{{custom_chem}}}"
                    if selected_chem:
                        st.session_state.pending_formula = st.session_state.formula + selected_chem
                        update_latex()
                        logger.debug(f"Chemistry notation inserted: {selected_chem}")

    # Physics
    with tabs[11]:
        if st.session_state.mode == "SymPy":
            st.warning("Physics notation is only supported in LaTeX mode.")
        else:
            with st.expander("Physics (\\dv, \\grad, etc.)"):
                with st.form(key="physics_form"):
                    cols = st.columns(3)
                    physics = ["\\dv{f}{x}", "\\grad{\\psi}", "\\curl{\\mathbf{A}}", "\\div{\\mathbf{F}}", "\\pdv{f}{x,y}"]
                    selected_physics = None
                    for i, p in enumerate(physics):
                        with cols[i % 3]:
                            if st.form_submit_button(p, key=f"physics_btn_{i}"):
                                selected_physics = p
                    custom_deriv = st.text_input("Custom Derivative (e.g., f,x)", placeholder="function,variable", key="custom_deriv")
                    if st.form_submit_button("Insert Custom Derivative", key="insert_deriv"):
                        if "," in custom_deriv:
                            f, x = custom_deriv.split(",", 1)
                            selected_physics = f"\\dv{{{f}}}{{{x}}}"
                    if selected_physics:
                        st.session_state.pending_formula = st.session_state.formula + selected_physics
                        update_latex()
                        logger.debug(f"Physics notation inserted: {selected_physics}")

    # Output
    st.text_area("LaTeX Output:", st.session_state.latex, key="latex_out", height=100)

    # Preview
    st.write("Preview:")
    img_b64 = None
    if st.session_state.latex and not st.session_state.latex.startswith("Invalid") and not st.session_state.latex.startswith("Parse error"):
        st.latex(st.session_state.latex)
        copy_js = """
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
                if (!window.MathJax || !window.MathJax.tex2mmlPromise) {
                    throw new Error('MathJax not loaded');
                }
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
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js" onerror="console.error('MathJax failed to load')"></script>
        """
        html_content = f"""
        {copy_js}
        <div id="latex-content" style="display: none;">{st.session_state.latex}</div>
        <div id="mathjax-preview">$${st.session_state.latex}$</div>
        <script>MathJax.typeset();</script>
        """
        img_b64 = latex_to_image(st.session_state.latex)
        if img_b64:
            html_content += f"""
            <img id="latex-image" src="data:image/png;base64,{img_b64}" style="max-width: 100%; margin-top: 10px;" />
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
        components.html(html_content, height=400)
    else:
        st.info("Enter a valid formula to see the LaTeX rendering.")

    # Export
    col1, col2 = st.columns(2)
    with col1:
        if img_b64:
            st.download_button("Download PNG", data=base64.b64decode(img_b64), file_name="equation.png", mime="image/png", key="download_png")
    with col2:
        pdf_b64 = latex_to_pdf(st.session_state.latex)
        if pdf_b64:
            st.download_button("Download PDF", data=base64.b64decode(pdf_b64), file_name="equation.pdf", mime="application/pdf", key="download_pdf_btn")

    # Reset and undo
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reset", key="reset_btn"):
            for key in ["formula", "latex", "temp_formula", "pending_formula"]:
                setattr(st.session_state, key, "")
            st.session_state.subscript_trigger = False
            st.rerun()
    with col2:
        if st.button("Undo", key="undo_btn") and st.session_state.history:
            st.session_state.formula, st.session_state.latex = st.session_state.history[-1]
            st.session_state.history.pop(-1)
            st.rerun()

except Exception as e:
    st.error(f"Unexpected error: {str(e)}")
    logger.error(f"Unexpected error: {str(e)}")
