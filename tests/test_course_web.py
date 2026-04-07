from app.models import User, Tile, Course, CourseTile


def _setup(db):
    user = User(username='webbuilder', email='wb@example.com')
    user.set_password('pass')
    db.session.add(user)
    tile = Tile(code='GRLBV', label='START', category='starts')
    db.session.add(tile)
    db.session.commit()
    return user, tile


def _login(client, username='webbuilder', password='pass'):
    client.post('/login', data={'username': username, 'password': password})


def test_courses_index(client, db):
    user, _ = _setup(db)
    course = Course(name='Public Course', is_public=True, created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    resp = client.get('/courses')
    assert resp.status_code == 200
    assert b'Public Course' in resp.data


def test_courses_index_hides_private(client, db):
    user, _ = _setup(db)
    course = Course(name='Secret Course', is_public=False, created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    resp = client.get('/courses')
    assert b'Secret Course' not in resp.data


def test_course_create_requires_login(client):
    resp = client.get('/courses/new')
    assert resp.status_code == 302


def test_course_create_and_redirect(client, db):
    user, _ = _setup(db)
    _login(client)

    resp = client.post('/courses/new', data={
        'name': 'My New Course',
        'description': 'A test',
        'is_public': True,
    })
    assert resp.status_code == 302
    course = Course.query.filter_by(name='My New Course').first()
    assert course is not None
    assert f'/courses/{course.id}/build' in resp.headers['Location']


def test_course_detail(client, db):
    user, tile = _setup(db)
    course = Course(name='Detail View', is_public=True, created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    ct = CourseTile(course_id=course.id, tile_id=tile.id, x=50, y=75)
    db.session.add(ct)
    db.session.commit()

    resp = client.get(f'/courses/{course.id}')
    assert resp.status_code == 200
    assert b'Detail View' in resp.data


def test_course_detail_private_forbidden(client, db):
    user, _ = _setup(db)
    course = Course(name='Hidden', is_public=False, created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    resp = client.get(f'/courses/{course.id}', follow_redirects=True)
    assert b'not found' in resp.data.lower()


def test_course_build_page(client, db):
    user, _ = _setup(db)
    _login(client)

    course = Course(name='Build Me', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    resp = client.get(f'/courses/{course.id}/build')
    assert resp.status_code == 200
    assert b'builder.js' in resp.data
    assert b'Build Me' in resp.data


def test_course_build_forbidden(client, db):
    user, _ = _setup(db)
    other = User(username='other3', email='other3@example.com')
    other.set_password('pass')
    db.session.add(other)
    db.session.commit()

    course = Course(name='Not Yours', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    _login(client, 'other3')
    resp = client.get(f'/courses/{course.id}/build')
    assert resp.status_code == 403
