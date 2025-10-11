# symbols.py
symbols_basic = [
    ("√", "sqrt()"), ("log", "log()"), ("exp", "exp()"), ("÷", "/"), ("×", "*"),
    ("^", "^{}" ), ("_", "_{}" ), # These will be adjusted in append based on mode
    ("+", "+"), ("-", "-")
]

symbols_brackets = [
    ("(", "("), (")", ")"), ("[", "["), ("]", "]"), ("{", "{"), ("}", "}")
]

symbols_trig = [
    ("sin", "sin()"), ("cos", "cos()"), ("tan", "tan()"), ("cot", "cot()"),
    ("sec", "sec()"), ("csc", "csc()"), ("asin", "asin()"), ("acos", "acos()"), ("atan", "atan()")
]

symbols_hyperbolic = [
    ("sinh", "sinh()"), ("cosh", "cosh()"), ("tanh", "tanh()")
]

symbols_calculus = {
    "∫": {"SymPy": "Integral(, x)", "LaTeX": "\\int_{}^{} \\, dx"},
    "∑": {"SymPy": "Sum(, (n, 0, oo))", "LaTeX": "\\sum_{}^{}"},
    "lim": {"SymPy": "Limit(, x, 0)", "LaTeX": "\\lim_{x \\to }"},
    "d/dx": {"SymPy": "Derivative(, x)", "LaTeX": "\\frac{d}{dx}"},
    "∂": {"SymPy": "Derivative(, x, evaluate=False)", "LaTeX": "\\partial"}  # Adjusted for SymPy
}

symbols_constants = [
    ("π", "pi"), ("e", "e"), ("∞", "oo")
]

symbols_greek = [
    ("α", "alpha"), ("β", "beta"), ("γ", "gamma"), ("δ", "delta"), ("Δ", "Delta"),
    ("ε", "epsilon"), ("ζ", "zeta"), ("η", "eta"), ("θ", "theta"), ("Θ", "Theta"),
    ("ι", "iota"), ("κ", "kappa"), ("λ", "lambda"), ("Λ", "Lambda"), ("μ", "mu"),
    ("ν", "nu"), ("ξ", "xi"), ("π", "pi"), ("ρ", "rho"), ("σ", "sigma"),
    ("Σ", "Sigma"), ("τ", "tau"), ("φ", "phi"), ("Φ", "Phi"), ("ω", "omega"), ("Ω", "Omega")
]

symbols_engineering = [
    ("Ω (ohm)", "Omega"), ("µ (micro)", "mu"), ("° (degree)", "degree"),
    ("≈", "approx"), ("≠", "ne"), ("≥", "ge"), ("≤", "le")
]

symbols_petroleum = [
    ("φ (porosity)", "phi"), ("κ (permeability)", "kappa"), ("μ (viscosity)", "mu"),
    ("ρ (density)", "rho"), ("P (pressure)", "P"), ("Q (flow rate)", "Q")
]
