import pytest
from app import create_app
from app.extensions import db as _db
from app.models import User


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def auth_client(app, db):
    """A test client that is already logged in."""
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()

    client = app.test_client()
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password123',
    })
    return client
