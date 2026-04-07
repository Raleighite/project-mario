import pytest
from app.models import User, Tile, Course, CourseTile


def _make_user(db):
    user = User(username='builder', email='builder@example.com')
    user.set_password('pass')
    db.session.add(user)
    db.session.commit()
    return user


def _make_tile(db):
    tile = Tile(code='GRLBV', label='START', category='starts')
    db.session.add(tile)
    db.session.commit()
    return tile


def test_course_to_dict(app, db):
    user = _make_user(db)
    course = Course(name='Test Course', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    d = course.to_dict()
    assert d['name'] == 'Test Course'
    assert d['created_by_username'] == 'builder'
    assert d['tile_count'] == 0
    assert 'id' in d


def test_course_to_dict_with_tiles(app, db):
    user = _make_user(db)
    tile = _make_tile(db)
    course = Course(name='With Tiles', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    ct = CourseTile(course_id=course.id, tile_id=tile.id, x=100.0, y=200.0)
    db.session.add(ct)
    db.session.commit()

    d = course.to_dict(include_tiles=True)
    assert d['tile_count'] == 1
    assert len(d['tiles']) == 1
    assert d['tiles'][0]['x'] == 100.0
    assert d['tiles'][0]['tile']['code'] == 'GRLBV'


def test_course_repr(app, db):
    user = _make_user(db)
    course = Course(name='My Level', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()
    assert 'My Level' in repr(course)


def test_course_tile_cascade_delete(app, db):
    user = _make_user(db)
    tile = _make_tile(db)
    course = Course(name='Cascade', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    ct = CourseTile(course_id=course.id, tile_id=tile.id, x=0, y=0)
    db.session.add(ct)
    db.session.commit()

    assert CourseTile.query.count() == 1
    db.session.delete(course)
    db.session.commit()
    assert CourseTile.query.count() == 0


def test_course_user_relationship(app, db):
    user = _make_user(db)
    course = Course(name='Related', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    assert course.created_by.username == 'builder'
    assert course in user.courses


def test_course_tile_to_dict(app, db):
    user = _make_user(db)
    tile = _make_tile(db)
    course = Course(name='CT Dict', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    ct = CourseTile(course_id=course.id, tile_id=tile.id, x=50.5, y=75.3)
    db.session.add(ct)
    db.session.commit()

    d = ct.to_dict()
    assert d['x'] == 50.5
    assert d['y'] == 75.3
    assert d['tile']['label'] == 'START'
