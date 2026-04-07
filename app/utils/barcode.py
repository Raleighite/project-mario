VALID_COLORS = {'G', 'R', 'B', 'L', 'P', 'V', 'Y', 'T'}
VALID_PREFIXES = ('GR', 'BR', 'TR')

COLOR_HEX = {
    'G': '#229551',
    'R': '#cb2129',
    'B': '#0000ff',
    'L': '#aed252',
    'P': '#d166a7',
    'V': '#9b78b5',
    'Y': '#f9dc2a',
    'T': '#1baaa3',
}

COLOR_NAMES = {
    'G': 'Green',
    'R': 'Red',
    'B': 'Blue',
    'L': 'Lime',
    'P': 'Pink',
    'V': 'Violet',
    'Y': 'Yellow',
    'T': 'Teal',
}


def validate_tile_code(code):
    """Validate a 5-character tile barcode code.

    Returns (True, None) if valid, or (False, error_message) if invalid.
    """
    if not isinstance(code, str):
        return False, 'Code must be a string'

    code = code.upper()

    if len(code) != 5:
        return False, 'Code must be exactly 5 characters'

    invalid_chars = set(code) - VALID_COLORS
    if invalid_chars:
        return False, f'Invalid color characters: {", ".join(sorted(invalid_chars))}'

    if len(set(code)) != 5:
        return False, 'Code must not contain repeated colors'

    if not code.startswith(VALID_PREFIXES):
        return False, 'Code must start with GR, BR, or TR'

    return True, None


def code_to_colors(code):
    """Convert a tile code to a list of hex color values."""
    code = code.upper()
    return [COLOR_HEX[c] for c in code]
