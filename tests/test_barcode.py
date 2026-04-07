from app.utils.barcode import validate_tile_code, code_to_colors, COLOR_HEX
from app.utils.barcode_image import generate_barcode_svg, generate_barcode_png
import pytest


class TestValidateTileCode:
    def test_valid_gr_code(self):
        valid, error = validate_tile_code('GRLBV')
        assert valid is True
        assert error is None

    def test_valid_br_code(self):
        valid, error = validate_tile_code('BRVYG')
        assert valid is True

    def test_valid_tr_code(self):
        valid, error = validate_tile_code('TRPVB')
        assert valid is True

    def test_case_insensitive(self):
        valid, _ = validate_tile_code('grlbv')
        assert valid is True

    def test_invalid_length_short(self):
        valid, error = validate_tile_code('GRL')
        assert valid is False
        assert 'exactly 5' in error

    def test_invalid_length_long(self):
        valid, error = validate_tile_code('GRLBVT')
        assert valid is False

    def test_invalid_characters(self):
        valid, error = validate_tile_code('GRXYZ')
        assert valid is False
        assert 'Invalid color' in error

    def test_repeated_colors(self):
        valid, error = validate_tile_code('GRRBV')
        assert valid is False
        assert 'repeated' in error

    def test_invalid_prefix(self):
        valid, error = validate_tile_code('LGBPV')
        assert valid is False
        assert 'must start with' in error

    def test_not_a_string(self):
        valid, error = validate_tile_code(12345)
        assert valid is False


class TestCodeToColors:
    def test_returns_hex_list(self):
        colors = code_to_colors('GRLBV')
        assert colors == [
            COLOR_HEX['G'], COLOR_HEX['R'], COLOR_HEX['L'],
            COLOR_HEX['B'], COLOR_HEX['V'],
        ]

    def test_case_insensitive(self):
        assert code_to_colors('grlbv') == code_to_colors('GRLBV')


class TestGenerateBarcodeSvg:
    def test_returns_svg_string(self):
        svg = generate_barcode_svg('GRLBV')
        assert '<svg' in svg
        assert '</svg>' in svg

    def test_contains_five_rects(self):
        svg = generate_barcode_svg('GRLBV')
        assert svg.count('<rect') == 5

    def test_contains_color_labels(self):
        svg = generate_barcode_svg('GRLBV')
        assert 'Green' in svg
        assert 'Red' in svg

    def test_invalid_code_raises(self):
        with pytest.raises(ValueError):
            generate_barcode_svg('XXXXX')


class TestGenerateBarcodePng:
    def test_returns_png_bytes(self):
        data = generate_barcode_png('GRLBV')
        assert isinstance(data, bytes)
        assert data[:8] == b'\x89PNG\r\n\x1a\n'

    def test_invalid_code_raises(self):
        with pytest.raises(ValueError):
            generate_barcode_png('XXXXX')
