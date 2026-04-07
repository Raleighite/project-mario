import io
from flask import request, jsonify, Response, send_file
from flask_login import login_required, current_user
from app.api import api_bp
from app.extensions import db
from app.models import Tile
from app.utils.barcode import validate_tile_code
from app.utils.barcode_image import generate_barcode_svg, generate_barcode_png


@api_bp.route('/tiles', methods=['GET'])
def list_tiles():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 100)

    query = Tile.query
    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)

    search = request.args.get('search')
    if search:
        query = query.filter(Tile.label.ilike(f'%{search}%'))

    pagination = query.order_by(Tile.category, Tile.label).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'tiles': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'categories': [
            r[0] for r in db.session.query(Tile.category).distinct().order_by(Tile.category).all()
        ],
    }), 200


@api_bp.route('/tiles/<int:tile_id>', methods=['GET'])
def get_tile(tile_id):
    tile = db.session.get(Tile, tile_id)
    if tile is None:
        return jsonify({'error': 'Tile not found'}), 404
    return jsonify(tile.to_dict()), 200


@api_bp.route('/tiles', methods=['POST'])
@login_required
def create_tile():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request must be JSON'}), 400

    code = data.get('code', '').upper()
    label = data.get('label')
    category = data.get('category')

    if not all([code, label, category]):
        return jsonify({'error': 'Missing required fields: code, label, category'}), 400

    valid, error = validate_tile_code(code)
    if not valid:
        return jsonify({'error': f'Invalid tile code: {error}'}), 400

    if Tile.query.filter_by(code=code).first():
        return jsonify({'error': 'A tile with this code already exists'}), 409

    tile = Tile(
        code=code,
        label=label,
        category=category,
        note=data.get('note'),
        hit_points=data.get('hit_points'),
        is_custom=True,
        created_by_id=current_user.id,
    )
    db.session.add(tile)
    db.session.commit()

    return jsonify(tile.to_dict()), 201


@api_bp.route('/tiles/<int:tile_id>/barcode.svg', methods=['GET'])
def tile_barcode_svg(tile_id):
    tile = db.session.get(Tile, tile_id)
    if tile is None:
        return jsonify({'error': 'Tile not found'}), 404
    svg = generate_barcode_svg(tile.code)
    return Response(svg, mimetype='image/svg+xml')


@api_bp.route('/tiles/<int:tile_id>/barcode.png', methods=['GET'])
def tile_barcode_png(tile_id):
    tile = db.session.get(Tile, tile_id)
    if tile is None:
        return jsonify({'error': 'Tile not found'}), 404
    png_bytes = generate_barcode_png(tile.code)
    return send_file(io.BytesIO(png_bytes), mimetype='image/png', download_name=f'{tile.code}.png')


@api_bp.route('/tiles/barcode/preview', methods=['GET'])
def barcode_preview():
    code = request.args.get('code', '').upper()
    if not code:
        return jsonify({'error': 'Missing code parameter'}), 400

    valid, error = validate_tile_code(code)
    if not valid:
        return jsonify({'error': f'Invalid tile code: {error}'}), 400

    fmt = request.args.get('format', 'svg')
    if fmt == 'png':
        png_bytes = generate_barcode_png(code)
        return send_file(io.BytesIO(png_bytes), mimetype='image/png', download_name=f'{code}.png')

    svg = generate_barcode_svg(code)
    return Response(svg, mimetype='image/svg+xml')
