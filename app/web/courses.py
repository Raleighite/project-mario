from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.web import web_bp
from app.extensions import db
from app.models import Course, Tile
from app.forms.course import CourseForm


@web_bp.route('/courses')
def courses_index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search')

    query = Course.query
    if current_user.is_authenticated:
        query = query.filter(
            or_(Course.is_public == True, Course.created_by_id == current_user.id)  # noqa: E712
        )
    else:
        query = query.filter_by(is_public=True)

    if search:
        query = query.filter(Course.name.ilike(f'%{search}%'))

    pagination = query.order_by(Course.updated_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )

    return render_template(
        'courses/index.html',
        pagination=pagination,
        courses=pagination.items,
        search=search,
    )


@web_bp.route('/courses/new', methods=['GET', 'POST'])
@login_required
def course_create():
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            name=form.name.data,
            description=form.description.data or None,
            is_public=form.is_public.data,
            created_by_id=current_user.id,
        )
        db.session.add(course)
        db.session.commit()
        return redirect(url_for('web.course_build', course_id=course.id))
    return render_template('courses/create.html', form=form)


@web_bp.route('/courses/<int:course_id>')
def course_detail(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        flash('Course not found.', 'error')
        return redirect(url_for('web.courses_index'))

    if not course.is_public:
        if not current_user.is_authenticated or current_user.id != course.created_by_id:
            flash('Course not found.', 'error')
            return redirect(url_for('web.courses_index'))

    placements = course.tile_placements.all()
    is_owner = current_user.is_authenticated and current_user.id == course.created_by_id

    return render_template(
        'courses/detail.html',
        course=course,
        placements=placements,
        is_owner=is_owner,
    )


@web_bp.route('/courses/<int:course_id>/build')
@login_required
def course_build(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        flash('Course not found.', 'error')
        return redirect(url_for('web.courses_index'))
    if course.created_by_id != current_user.id:
        abort(403)

    return render_template('courses/build.html', course=course)
