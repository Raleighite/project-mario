from app.models import User


def test_login_page_renders(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_register_page_renders(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data


def test_register_creates_user(client, db):
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'secret123',
        'password2': 'secret123',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert User.query.filter_by(username='newuser').first() is not None


def test_login_success(client, db):
    user = User(username='logintest', email='login@example.com')
    user.set_password('mypassword')
    db.session.add(user)
    db.session.commit()

    response = client.post('/login', data={
        'username': 'logintest',
        'password': 'mypassword',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data


def test_login_bad_password(client, db):
    user = User(username='badpass', email='bad@example.com')
    user.set_password('correct')
    db.session.add(user)
    db.session.commit()

    response = client.post('/login', data={
        'username': 'badpass',
        'password': 'wrong',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_logout(auth_client):
    response = auth_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'logged out' in response.data.lower()


def test_dashboard_requires_login(client):
    response = client.get('/dashboard')
    assert response.status_code == 302


def test_dashboard_accessible_when_logged_in(auth_client):
    response = auth_client.get('/dashboard')
    assert response.status_code == 200
    assert b'testuser' in response.data
