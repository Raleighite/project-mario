from app.models import User, Tile, Course, CourseTile


def _setup(db):
    """Create a user and a tile for testing."""
    user = User(username='apibuilder', email='ab@example.com')
    user.set_password('pass')
    db.session.add(user)

    tile = Tile(code='GRLBV', label='START', category='starts')
    db.session.add(tile)
    db.session.commit()
    return user, tile


def _login(client, username='apibuilder', password='pass'):
    client.post('/api/v1/login', json={'username': username, 'password': password})


def test_create_course(client, db):
    user, _ = _setup(db)
    _login(client)
    resp = client.post('/api/v1/courses', json={
        'name': 'My Course',
        'description': 'A test course',
        'is_public': True,
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['name'] == 'My Course'
    assert data['is_public'] is True


def test_create_course_unauthenticated(client):
    resp = client.post('/api/v1/courses', json={'name': 'Nope'})
    assert resp.status_code == 401


def test_list_courses_public(client, db):
    user, _ = _setup(db)
    c1 = Course(name='Public', is_public=True, created_by_id=user.id)
    c2 = Course(name='Private', is_public=False, created_by_id=user.id)
    db.session.add_all([c1, c2])
    db.session.commit()

    # Unauthenticated: only public
    resp = client.get('/api/v1/courses')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['courses'][0]['name'] == 'Public'


def test_list_courses_own(client, db):
    user, _ = _setup(db)
    c1 = Course(name='Public', is_public=True, created_by_id=user.id)
    c2 = Course(name='Private', is_public=False, created_by_id=user.id)
    db.session.add_all([c1, c2])
    db.session.commit()

    _login(client)
    resp = client.get('/api/v1/courses')
    data = resp.get_json()
    assert data['total'] == 2


def test_get_course(client, db):
    user, tile = _setup(db)
    course = Course(name='Detail', is_public=True, created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    ct = CourseTile(course_id=course.id, tile_id=tile.id, x=10, y=20)
    db.session.add(ct)
    db.session.commit()

    resp = client.get(f'/api/v1/courses/{course.id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['name'] == 'Detail'
    assert len(data['tiles']) == 1
    assert data['tiles'][0]['x'] == 10


def test_get_private_course_forbidden(client, db):
    user, _ = _setup(db)
    course = Course(name='Secret', is_public=False, created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    resp = client.get(f'/api/v1/courses/{course.id}')
    assert resp.status_code == 404


def test_get_course_not_found(client):
    resp = client.get('/api/v1/courses/9999')
    assert resp.status_code == 404


def test_update_course(client, db):
    user, _ = _setup(db)
    course = Course(name='Old Name', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    _login(client)
    resp = client.put(f'/api/v1/courses/{course.id}', json={'name': 'New Name'})
    assert resp.status_code == 200
    assert resp.get_json()['name'] == 'New Name'


def test_update_course_forbidden(client, db):
    user, _ = _setup(db)
    other = User(username='other', email='other@example.com')
    other.set_password('pass')
    db.session.add(other)
    course = Course(name='Not Mine', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    _login(client, 'other')
    resp = client.put(f'/api/v1/courses/{course.id}', json={'name': 'Hacked'})
    assert resp.status_code == 403


def test_save_course_tiles(client, db):
    user, tile = _setup(db)
    course = Course(name='Tile Save', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    _login(client)
    resp = client.put(f'/api/v1/courses/{course.id}/tiles', json={
        'tiles': [
            {'tile_id': tile.id, 'x': 100, 'y': 200},
            {'tile_id': tile.id, 'x': 300, 'y': 400},
        ]
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['tiles']) == 2


def test_save_course_tiles_replaces(client, db):
    user, tile = _setup(db)
    course = Course(name='Replace', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    ct = CourseTile(course_id=course.id, tile_id=tile.id, x=0, y=0)
    db.session.add(ct)
    db.session.commit()

    _login(client)
    resp = client.put(f'/api/v1/courses/{course.id}/tiles', json={
        'tiles': [{'tile_id': tile.id, 'x': 50, 'y': 50}]
    })
    assert resp.status_code == 200
    assert len(resp.get_json()['tiles']) == 1
    assert CourseTile.query.filter_by(course_id=course.id).count() == 1


def test_save_course_tiles_invalid_tile_id(client, db):
    user, _ = _setup(db)
    course = Course(name='Bad Tile', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    _login(client)
    resp = client.put(f'/api/v1/courses/{course.id}/tiles', json={
        'tiles': [{'tile_id': 99999, 'x': 0, 'y': 0}]
    })
    assert resp.status_code == 400


def test_delete_course(client, db):
    user, _ = _setup(db)
    course = Course(name='Delete Me', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()
    course_id = course.id

    _login(client)
    resp = client.delete(f'/api/v1/courses/{course_id}')
    assert resp.status_code == 200
    assert db.session.get(Course, course_id) is None


def test_delete_course_forbidden(client, db):
    user, _ = _setup(db)
    other = User(username='other2', email='other2@example.com')
    other.set_password('pass')
    db.session.add(other)
    course = Course(name='Not Yours', created_by_id=user.id)
    db.session.add(course)
    db.session.commit()

    _login(client, 'other2')
    resp = client.delete(f'/api/v1/courses/{course.id}')
    assert resp.status_code == 403
