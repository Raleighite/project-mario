from app import create_app


def test_development_config():
    app = create_app('development')
    assert app.config['DEBUG'] is True
    assert app.config['TESTING'] is False


def test_testing_config():
    app = create_app('testing')
    assert app.config['TESTING'] is True
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite://'
    assert app.config['WTF_CSRF_ENABLED'] is False


def test_production_config():
    app = create_app('production')
    assert app.config['DEBUG'] is False
    assert app.config['TESTING'] is False
