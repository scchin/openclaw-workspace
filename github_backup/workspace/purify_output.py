import argparse
import re
import sys
import json
import os

# Core fallback replacement map for 100% reliability even if external rules are missing.
CORE_REPLACEMENTS = {
    r"\\rightarrow": "→",
    r"\\leftarrow": "←",
    r"\\Rightarrow": "⇒",
    r"\\Leftarrow": "⇐",
    r"\\leftrightarrow": "↔",
    r"\\approx": "≈",
    r"\\sim": "∼",
    r"\\cong": "≅",
    r"\\equiv": "≡",
    r"\\neq": "≠",
    r"\\le": "≤",
    r"\\ge": "≥",
    r"\\leq": "≤",
    r"\\geq": "≥",
    r"\\pm": "±",
    r"\\mp": "∓",
    r"\\infty": "∞",
    r"\\partial": "∂",
    r"\\nabla": "∇",
    r"\\forall": "∀",
    r"\\exists": "∃",
    r"\\in": "∈",
    r"\\notin": "∉",
    r"\\subset": "⊂",
    r"\\supset": "⊃",
    r"\\subseteq": "⊆",
    r"\\supseteq": "⊇",
    r"\\cap": "∩",
    r"\\cup": "∪",
    r"\\wedge": "∧",
    r"\\vee": "∨",
    r"\\oplus": "⊕",
    r"\\otimes": "⊗",
    r"\\perp": "⊥",
    r"\\angle": "∠",
    r"\\parallel": "∥",
    r"\\alpha": "α",
    r"\\beta": "β",
    r"\\gamma": "γ",
    r"\\delta": "δ",
    r"\\epsilon": "ε",
    r"\\zeta": "ζ",
    r"\\eta": "η",
    r"\\theta": "θ",
    r"\\iota": "ι",
    r"\\kappa": "κ",
    r"\\lambda": "λ",
    r"\\mu": "μ",
    r"\\nu": "ν",
    r"\\xi": "ξ",
    r"\\omicron": "ο",
    r"\\pi": "π",
    r"\\rho": "ρ",
    r"\\sigma": "σ",
    r"\\tau": "τ",
    r"\\upsilon": "υ",
    r"\\phi": "φ",
    r"\\chi": "χ",
    r"\\psi": "ψ",
    r"\\omega": "ω",
    r"\\Delta": "Δ",
    r"\\Gamma": "Γ",
    r"\\Theta": "Θ",
    r"\\Lambda": "Λ",
    r"\\Xi": "Ξ",
    r"\\Pi": "Π",
    r"\\Sigma": "Σ",
    r"\\Phi": "Φ",
    r"\\Psi": "Ψ",
    r"\\Omega": "Ω",
}

RULES_PATH = "/Users/KS/.openclaw/workspace/Sutra_Library/S-Swarm_Hybrid_System/intercept_rules.json"

def load_rules():
    """Loads extended rules from JSON, merges with CORE_REPLACEMENTS."""
    rules = CORE_REPLACEMENTS.copy()
    try:
        if os.path.exists(RULES_PATH):
            with open(RULES_PATH, 'r', encoding='utf-8') as f:
                external_rules = json.load(f).get("latex_to_unicode", {})
                # Convert keys to regex patterns if they aren't already
                for k, v in external_rules.items():
                    rules[re.escape(k)] = v
    except Exception as e:
        # Log error to stderr to avoid polluting stdout
        print(f"Warning: Failed to load external rules: {e}", file=sys.stderr)
    return rules

def resolve_nested_commands(text):
    """
    Recursively resolves \command{content} patterns.
    Handles \text{}, \mathbf{}, \textit{}, etc.
    """
    # 1. Handle \frac{num}{den} -> (num/den)
    # This regex finds \frac followed by two { ... } blocks
    while True:
        new_text = re.sub(r'\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}', r'(\1/\2)', text)
        if new_text == text:
            break
        text = new_text

    # 2. Handle general \command{content} -> content
    # Matches common wrapper commands: \text, \mathbf, \textit, \mathrm, \mathit, \mathcal, \mathsf
    # Also handles nested ones by looping
    while True:
        # Pattern: \ followed by letters, then { content }
        # Using a non-greedy match for the inner content [^{}]*
        new_text = re.sub(r'\\(text|mathbf|textit|mathrm|mathit|mathcal|mathsf)\s*\{([^{}]*)\}', r'\2', text)
        if new_text == text:
            break
        text = new_text
    
    return text

def sanitize_latex_content(content, rules):
    """Applies symbol replacement to a string (used for $ blocks)."""
    # Sort rules by length descending to ensure longest matches (e.g., \rightarrow) happen before shorter ones (\to)
    sorted_keys = sorted(rules.keys(), key=len, reverse=True)
    for key in sorted_keys:
        content = re.sub(key, rules[key], content)
    
    # Final cleanup of any remaining \command sequences inside the block
    content = re.sub(r'\\([a-zA-Z]+)', ' ', content)
    content = content.replace('{', '').replace('}', '')
    return content

def purify_text(text):
    """
    Deterministic Physical Interception Pipeline.
    1. Unwrap nested commands.
    2. Process LaTeX blocks ($...$, $$...$$).
    3. Global symbol replacement.
    4. Final physical scrubbing.
    """
    if not text:
        return ""

    rules = load_rules()

    # Phase 1: Unwrap nested commands (\text{}, \frac{}, etc.)
    text = resolve_nested_commands(text)

    # Phase 2: Handle LaTeX blocks
    # Double dollar signs first
    text = re.sub(r'\$\$(.*?)\$\$', lambda m: sanitize_latex_content(m.group(1), rules), text, flags=re.DOTALL)
    # Single dollar signs
    text = re.sub(r'\$(.*?)\$', lambda m: sanitize_latex_content(m.group(1), rules), text)

    # Phase 3: Global symbol replacement (catch naked LaTeX)
    # Use the same logic as sanitize_latex_content but on the whole text
    sorted_keys = sorted(rules.keys(), key=len, reverse=True)
    for key in sorted_keys:
        text = re.sub(key, rules[key], text)

    # Phase 4: Physical Scrubbing (The Hard-Lock)
    # Remove any remaining \command sequences
    text = re.sub(r'\\([a-zA-Z]+)', ' ', text)
    # Remove leftover $
    text = text.replace('$', '')
    # Remove leftover curly braces that weren't part of a command
    text = text.replace('{', '').replace('}', '')
    # Fix escaped percent signs
    text = text.replace('\\%', '%')
    # Collapse multiple spaces
    text = re.sub(r' +', ' ', text)

    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Physical Interception Layer (PIL) - Output Purifier")
    parser.add_argument("--text", type=str, help="The text to purify")
    parser.add_argument("--file", type=str, help="Path to the file to purify")
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                input_text = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        input_text = args.text
    else:
        parser.print_help()
        sys.exit(1)

    print(purify_text(input_text))

if __name__ == "__main__":
    main()
