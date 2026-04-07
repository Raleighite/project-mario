from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.web import web_bp
from app.extensions import db
from app.models import Tile
from app.forms.tile import TileForm, CATEGORY_CHOICES
from app.utils.barcode_image import generate_barcode_svg


@web_bp.route('/tiles')
def tiles_index():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    search = request.args.get('search')

    query = Tile.query
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Tile.label.ilike(f'%{search}%'))

    pagination = query.order_by(Tile.category, Tile.label).paginate(
        page=page, per_page=24, error_out=False
    )

    categories = [
        r[0] for r in db.session.query(Tile.category).distinct().order_by(Tile.category).all()
    ]
    category_labels = dict(CATEGORY_CHOICES)

    return render_template(
        'tiles/index.html',
        pagination=pagination,
        tiles=pagination.items,
        categories=categories,
        category_labels=category_labels,
        current_category=category,
        search=search,
        generate_barcode_svg=generate_barcode_svg,
    )


@web_bp.route('/tiles/<int:tile_id>')
def tile_detail(tile_id):
    tile = db.session.get(Tile, tile_id)
    if tile is None:
        flash('Tile not found.', 'error')
        return redirect(url_for('web.tiles_index'))
    category_labels = dict(CATEGORY_CHOICES)
    svg = generate_barcode_svg(tile.code, bar_width=60, bar_height=300)
    return render_template('tiles/detail.html', tile=tile, svg=svg, category_labels=category_labels)


@web_bp.route('/tiles/<int:tile_id>/print')
def tile_print(tile_id):
    tile = db.session.get(Tile, tile_id)
    if tile is None:
        flash('Tile not found.', 'error')
        return redirect(url_for('web.tiles_index'))
    svg = generate_barcode_svg(tile.code, bar_width=80, bar_height=400)
    return render_template('tiles/print.html', tile=tile, svg=svg)


@web_bp.route('/tiles/create', methods=['GET', 'POST'])
@login_required
def tile_create():
    form = TileForm()
    if form.validate_on_submit():
        tile = Tile(
            code=form.code.data.upper(),
            label=form.label.data,
            category=form.category.data,
            note=form.note.data or None,
            hit_points=form.hit_points.data,
            is_custom=True,
            created_by_id=current_user.id,
        )
        db.session.add(tile)
        db.session.commit()
        flash(f'Tile {tile.code} created!', 'success')
        return redirect(url_for('web.tile_detail', tile_id=tile.id))
    return render_template('tiles/create.html', form=form)
