import io
from app.utils.barcode import validate_tile_code, code_to_colors, COLOR_NAMES


def generate_barcode_svg(code, bar_width=40, bar_height=200, gap=2):
    """Generate an SVG barcode image for a tile code.

    Returns an SVG string.
    """
    code = code.upper()
    valid, error = validate_tile_code(code)
    if not valid:
        raise ValueError(error)

    colors = code_to_colors(code)
    total_width = (bar_width * 5) + (gap * 4)
    label_height = 24
    total_height = bar_height + label_height + 8

    bars = []
    for i, (color, letter) in enumerate(zip(colors, code)):
        x = i * (bar_width + gap)
        bars.append(
            f'<rect x="{x}" y="0" width="{bar_width}" height="{bar_height}" '
            f'fill="{color}" stroke="#333" stroke-width="1"/>'
        )
        label_x = x + bar_width // 2
        label_y = bar_height + label_height
        bars.append(
            f'<text x="{label_x}" y="{label_y}" text-anchor="middle" '
            f'font-family="monospace" font-size="14" fill="#333">'
            f'{COLOR_NAMES[letter]}</text>'
        )

    bars_str = '\n    '.join(bars)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_width}" height="{total_height}" '
        f'viewBox="0 0 {total_width} {total_height}">\n'
        f'    {bars_str}\n'
        f'</svg>'
    )


def generate_barcode_png(code, bar_width=80, bar_height=400, gap=4, dpi=300):
    """Generate a PNG barcode image for a tile code.

    Returns PNG bytes suitable for printing.
    """
    from PIL import Image, ImageDraw, ImageFont

    code = code.upper()
    valid, error = validate_tile_code(code)
    if not valid:
        raise ValueError(error)

    colors = code_to_colors(code)
    total_width = (bar_width * 5) + (gap * 4) + 20  # 10px padding each side
    label_height = 40
    total_height = bar_height + label_height + 30  # padding top/bottom

    img = Image.new('RGB', (total_width, total_height), 'white')
    draw = ImageDraw.Draw(img)

    for i, (color, letter) in enumerate(zip(colors, code)):
        x = 10 + i * (bar_width + gap)
        draw.rectangle([x, 10, x + bar_width, 10 + bar_height], fill=color, outline='#333333')

        label_x = x + bar_width // 2
        label_y = 10 + bar_height + 8
        name = COLOR_NAMES[letter]
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
        except (OSError, IOError):
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((label_x - text_width // 2, label_y), name, fill='#333333', font=font)

    buf = io.BytesIO()
    img.save(buf, format='PNG', dpi=(dpi, dpi))
    buf.seek(0)
    return buf.getvalue()
