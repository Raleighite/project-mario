import pytest
from app.models import User
from app.extensions import db as _db


def test_set_and_check_password(app):
    user = User(username='alice', email='alice@example.com')
    user.set_password('correct-horse')
    assert user.check_password('correct-horse') is True
    assert user.check_password('wrong-password') is False


def test_password_hash_is_not_plaintext(app):
    user = User(username='bob', email='bob@example.com')
    user.set_password('mysecret')
    assert user.password_hash != 'mysecret'


def test_to_dict(app, db):
    user = User(username='charlie', email='charlie@example.com')
    user.set_password('pass')
    db.session.add(user)
    db.session.commit()

    d = user.to_dict()
    assert d['username'] == 'charlie'
    assert d['email'] == 'charlie@example.com'
    assert 'id' in d
    assert 'created_at' in d
    assert 'password_hash' not in d


def test_username_unique(app, db):
    u1 = User(username='same', email='a@example.com')
    u1.set_password('pass')
    db.session.add(u1)
    db.session.commit()

    u2 = User(username='same', email='b@example.com')
    u2.set_password('pass')
    db.session.add(u2)
    with pytest.raises(Exception):
        db.session.commit()


def test_repr(app):
    user = User(username='dave', email='dave@example.com')
    assert repr(user) == '<User dave>'
