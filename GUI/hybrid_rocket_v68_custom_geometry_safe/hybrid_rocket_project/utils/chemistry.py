"""
Chemistry Utilities

Functions for chemical formula manipulation.
"""


def explode_formula(formula: str) -> str:
    """
    Convert chemical formula to expanded format
    
    Example: H2O -> H 2 O 1
    
    Args:
        formula: Chemical formula (e.g., "H2O", "C3H8")
        
    Returns:
        Expanded formula string
    """
    formula = formula.replace(" ", "")
    exploded_formula = ""
    prec = "1"

    for i, char in enumerate(formula):
        if char.isupper() and char.isalpha():
            if prec.isdigit():
                exploded_formula = exploded_formula + " " + char
            else:
                exploded_formula = exploded_formula + " " + "1" + " " + char
            prec = char
        elif char.islower() and char.isalpha():
            if prec.isupper() and prec.isalpha():
                exploded_formula = exploded_formula + char
            prec = char
        elif char.isdigit():
            if prec.isalpha():
                exploded_formula = exploded_formula + " " + char
            elif prec.isdigit():
                exploded_formula = exploded_formula + char
            prec = char
        if i == (len(formula) - 1) and char.isalpha():
            exploded_formula = exploded_formula + " " + "1"

    exploded_formula = exploded_formula.strip()
    return exploded_formula
