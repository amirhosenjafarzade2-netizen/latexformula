# symbols.py
symbols_basic = [
    {"label": "√", "SymPy": "sqrt()", "LaTeX": "\\sqrt{}"},
    {"label": "log", "SymPy": "log()", "LaTeX": "\\log{}"},
    {"label": "exp", "SymPy": "exp()", "LaTeX": "\\exp{}"},
    {"label": "÷", "SymPy": "/", "LaTeX": "\\div"},
    {"label": "×", "SymPy": "*", "LaTeX": "\\times"},
    {"label": "^", "SymPy": "^", "LaTeX": "^{}"},
    {"label": "_", "SymPy": "_", "LaTeX": "_{}"},
    {"label": "+", "SymPy": "+", "LaTeX": "+"},
    {"label": "-", "SymPy": "-", "LaTeX": "-"}
]

symbols_brackets = [
    {"label": "(", "SymPy": "(", "LaTeX": "("},
    {"label": ")", "SymPy": ")", "LaTeX": ")"},
    {"label": "[", "SymPy": "[", "LaTeX": "["},
    {"label": "]", "SymPy": "]", "LaTeX": "]"},
    {"label": "{", "SymPy": "{", "LaTeX": "{"},
    {"label": "}", "SymPy": "}", "LaTeX": "}"}
]

symbols_trig = [
    {"label": "sin", "SymPy": "sin()", "LaTeX": "\\sin{}"},
    {"label": "cos", "SymPy": "cos()", "LaTeX": "\\cos{}"},
    {"label": "tan", "SymPy": "tan()", "LaTeX": "\\tan{}"},
    {"label": "cot", "SymPy": "cot()", "LaTeX": "\\cot{}"},
    {"label": "sec", "SymPy": "sec()", "LaTeX": "\\sec{}"},
    {"label": "csc", "SymPy": "csc()", "LaTeX": "\\csc{}"},
    {"label": "asin", "SymPy": "asin()", "LaTeX": "\\arcsin{}"},
    {"label": "acos", "SymPy": "acos()", "LaTeX": "\\arccos{}"},
    {"label": "atan", "SymPy": "atan()", "LaTeX": "\\arctan{}"}
]

symbols_hyperbolic = [
    {"label": "sinh", "SymPy": "sinh()", "LaTeX": "\\sinh{}"},
    {"label": "cosh", "SymPy": "cosh()", "LaTeX": "\\cosh{}"},
    {"label": "tanh", "SymPy": "tanh()", "LaTeX": "\\tanh{}"}
]

symbols_calculus = [
    {"label": "∫", "SymPy": "Integral(, x)", "LaTeX": "\\int_{}^{} \\, dx"},
    {"label": "∑", "SymPy": "Sum(, (n, 0, oo))", "LaTeX": "\\sum_{}^{}"},
    {"label": "lim", "SymPy": "Limit(, x, 0)", "LaTeX": "\\lim_{x \\to }"},
    {"label": "d/dx", "SymPy": "Derivative(, x)", "LaTeX": "\\frac{d}{dx}"},
    {"label": "∂", "SymPy": "Derivative(, x, evaluate=False)", "LaTeX": "\\partial"}
]

symbols_constants = [
    {"label": "π", "SymPy": "pi", "LaTeX": "\\pi"},
    {"label": "e", "SymPy": "e", "LaTeX": "e"},
    {"label": "∞", "SymPy": "oo", "LaTeX": "\\infty"}
]

symbols_greek = [
    {"label": "α", "SymPy": "alpha", "LaTeX": "\\alpha"},
    {"label": "β", "SymPy": "beta", "LaTeX": "\\beta"},
    {"label": "γ", "SymPy": "gamma", "LaTeX": "\\gamma"},
    {"label": "δ", "SymPy": "delta", "LaTeX": "\\delta"},
    {"label": "Δ", "SymPy": "Delta", "LaTeX": "\\Delta"},
    {"label": "ε", "SymPy": "epsilon", "LaTeX": "\\epsilon"},
    {"label": "ζ", "SymPy": "zeta", "LaTeX": "\\zeta"},
    {"label": "η", "SymPy": "eta", "LaTeX": "\\eta"},
    {"label": "θ", "SymPy": "theta", "LaTeX": "\\theta"},
    {"label": "Θ", "SymPy": "Theta", "LaTeX": "\\Theta"},
    {"label": "ι", "SymPy": "iota", "LaTeX": "\\iota"},
    {"label": "κ", "SymPy": "kappa", "LaTeX": "\\kappa"},
    {"label": "λ", "SymPy": "lambda", "LaTeX": "\\lambda"},
    {"label": "Λ", "SymPy": "Lambda", "LaTeX": "\\Lambda"},
    {"label": "μ", "SymPy": "mu", "LaTeX": "\\mu"},
    {"label": "ν", "SymPy": "nu", "LaTeX": "\\nu"},
    {"label": "ξ", "SymPy": "xi", "LaTeX": "\\xi"},
    {"label": "π", "SymPy": "pi", "LaTeX": "\\pi"},
    {"label": "ρ", "SymPy": "rho", "LaTeX": "\\rho"},
    {"label": "σ", "SymPy": "sigma", "LaTeX": "\\sigma"},
    {"label": "Σ", "SymPy": "Sigma", "LaTeX": "\\Sigma"},
    {"label": "τ", "SymPy": "tau", "LaTeX": "\\tau"},
    {"label": "φ", "SymPy": "phi", "LaTeX": "\\phi"},
    {"label": "Φ", "SymPy": "Phi", "LaTeX": "\\Phi"},
    {"label": "ω", "SymPy": "omega", "LaTeX": "\\omega"},
    {"label": "Ω", "SymPy": "Omega", "LaTeX": "\\Omega"}
]

symbols_engineering = [
    {"label": "Ω (ohm)", "SymPy": "Omega", "LaTeX": "\\Omega"},
    {"label": "µ (micro)", "SymPy": "mu", "LaTeX": "\\mu"},
    {"label": "° (degree)", "SymPy": "degree", "LaTeX": "^{\\circ}"},
    {"label": "≈", "SymPy": "approx", "LaTeX": "\\approx"},
    {"label": "≠", "SymPy": "ne", "LaTeX": "\\neq"},
    {"label": "≥", "SymPy": "ge", "LaTeX": "\\geq"},
    {"label": "≤", "SymPy": "le", "LaTeX": "\\leq"}
]

symbols_petroleum = [
    {"label": "φ (porosity)", "SymPy": "phi", "LaTeX": "\\phi"},
    {"label": "κ (permeability)", "SymPy": "kappa", "LaTeX": "\\kappa"},
    {"label": "μ (viscosity)", "SymPy": "mu", "LaTeX": "\\mu"},
    {"label": "ρ (density)", "SymPy": "rho", "LaTeX": "\\rho"},
    {"label": "P (pressure)", "SymPy": "P", "LaTeX": "P"},
    {"label": "Q (flow rate)", "SymPy": "Q", "LaTeX": "Q"}
]
