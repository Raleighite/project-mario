from flask import request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.api import api_bp
from app.extensions import db
from app.models import Course, CourseTile, Tile


@api_bp.route('/courses', methods=['GET'])
def list_courses():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 50)

    query = Course.query
    if current_user.is_authenticated:
        query = query.filter(
            or_(Course.is_public == True, Course.created_by_id == current_user.id)  # noqa: E712
        )
    else:
        query = query.filter_by(is_public=True)

    search = request.args.get('search')
    if search:
        query = query.filter(Course.name.ilike(f'%{search}%'))

    pagination = query.order_by(Course.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'courses': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    }), 200


@api_bp.route('/courses', methods=['POST'])
@login_required
def create_course():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request must be JSON'}), 400

    name = data.get('name')
    if not name:
        return jsonify({'error': 'Missing required field: name'}), 400

    course = Course(
        name=name,
        description=data.get('description'),
        is_public=data.get('is_public', False),
        canvas_width=data.get('canvas_width', 1200),
        canvas_height=data.get('canvas_height', 800),
        created_by_id=current_user.id,
    )
    db.session.add(course)
    db.session.commit()

    return jsonify(course.to_dict()), 201


@api_bp.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        return jsonify({'error': 'Course not found'}), 404

    if not course.is_public:
        if not current_user.is_authenticated or current_user.id != course.created_by_id:
            return jsonify({'error': 'Course not found'}), 404

    return jsonify(course.to_dict(include_tiles=True)), 200


@api_bp.route('/courses/<int:course_id>', methods=['PUT'])
@login_required
def update_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        return jsonify({'error': 'Course not found'}), 404
    if course.created_by_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request must be JSON'}), 400

    if 'name' in data:
        course.name = data['name']
    if 'description' in data:
        course.description = data['description']
    if 'is_public' in data:
        course.is_public = data['is_public']
    if 'canvas_width' in data:
        course.canvas_width = data['canvas_width']
    if 'canvas_height' in data:
        course.canvas_height = data['canvas_height']

    db.session.commit()
    return jsonify(course.to_dict()), 200


@api_bp.route('/courses/<int:course_id>/tiles', methods=['PUT'])
@login_required
def save_course_tiles(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        return jsonify({'error': 'Course not found'}), 404
    if course.created_by_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json()
    if not data or 'tiles' not in data:
        return jsonify({'error': 'Missing tiles array'}), 400

    # Validate all tile_ids exist
    tile_ids = {t['tile_id'] for t in data['tiles'] if 'tile_id' in t}
    existing_tiles = {t.id for t in Tile.query.filter(Tile.id.in_(tile_ids)).all()}
    invalid_ids = tile_ids - existing_tiles
    if invalid_ids:
        return jsonify({'error': f'Invalid tile IDs: {sorted(invalid_ids)}'}), 400

    # Full replacement: delete existing, insert new
    for ct in CourseTile.query.filter_by(course_id=course.id).all():
        db.session.delete(ct)
    db.session.flush()

    for entry in data['tiles']:
        ct = CourseTile(
            course_id=course.id,
            tile_id=entry['tile_id'],
            x=float(entry['x']),
            y=float(entry['y']),
        )
        db.session.add(ct)

    db.session.commit()
    return jsonify(course.to_dict(include_tiles=True)), 200


@api_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@login_required
def delete_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        return jsonify({'error': 'Course not found'}), 404
    if course.created_by_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403

    db.session.delete(course)
    db.session.commit()
    return jsonify({'message': 'Course deleted'}), 200
