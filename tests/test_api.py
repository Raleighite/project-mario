from app.models import User


def test_api_register(client):
    response = client.post('/api/v1/register', json={
        'username': 'apiuser',
        'email': 'api@example.com',
        'password': 'secret123',
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['username'] == 'apiuser'
    assert data['email'] == 'api@example.com'
    assert 'id' in data


def test_api_register_duplicate_username(client, db):
    user = User(username='taken', email='orig@example.com')
    user.set_password('pass')
    db.session.add(user)
    db.session.commit()

    response = client.post('/api/v1/register', json={
        'username': 'taken',
        'email': 'new@example.com',
        'password': 'secret123',
    })
    assert response.status_code == 409


def test_api_register_missing_fields(client):
    response = client.post('/api/v1/register', json={'username': 'only'})
    assert response.status_code == 400


def test_api_login_success(client, db):
    user = User(username='loginapi', email='loginapi@example.com')
    user.set_password('password')
    db.session.add(user)
    db.session.commit()

    response = client.post('/api/v1/login', json={
        'username': 'loginapi',
        'password': 'password',
    })
    assert response.status_code == 200
    assert response.get_json()['username'] == 'loginapi'


def test_api_login_bad_credentials(client, db):
    user = User(username='badcred', email='badcred@example.com')
    user.set_password('right')
    db.session.add(user)
    db.session.commit()

    response = client.post('/api/v1/login', json={
        'username': 'badcred',
        'password': 'wrong',
    })
    assert response.status_code == 401


def test_api_users_me_unauthenticated(client):
    response = client.get('/api/v1/users/me')
    assert response.status_code == 401
    assert response.get_json()['error'] == 'Authentication required'


def test_api_users_me_authenticated(client, db):
    user = User(username='meuser', email='me@example.com')
    user.set_password('pass')
    db.session.add(user)
    db.session.commit()

    client.post('/api/v1/login', json={
        'username': 'meuser',
        'password': 'pass',
    })
    response = client.get('/api/v1/users/me')
    assert response.status_code == 200
    assert response.get_json()['username'] == 'meuser'


def test_api_get_user_by_id(client, db):
    user = User(username='byid', email='byid@example.com')
    user.set_password('pass')
    db.session.add(user)
    db.session.commit()

    client.post('/api/v1/login', json={
        'username': 'byid',
        'password': 'pass',
    })
    response = client.get(f'/api/v1/users/{user.id}')
    assert response.status_code == 200
    assert response.get_json()['username'] == 'byid'


def test_api_get_user_not_found(client, db):
    user = User(username='finder', email='finder@example.com')
    user.set_password('pass')
    db.session.add(user)
    db.session.commit()

    client.post('/api/v1/login', json={
        'username': 'finder',
        'password': 'pass',
    })
    response = client.get('/api/v1/users/9999')
    assert response.status_code == 404
