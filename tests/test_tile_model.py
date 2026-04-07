import pytest
from app.models import Tile, User


def test_tile_to_dict(app, db):
    tile = Tile(code='GRLBV', label='TEST', category='items', note='A test tile')
    db.session.add(tile)
    db.session.commit()

    d = tile.to_dict()
    assert d['code'] == 'GRLBV'
    assert d['label'] == 'TEST'
    assert d['category'] == 'items'
    assert d['note'] == 'A test tile'
    assert 'id' in d
    assert 'created_at' in d


def test_tile_repr(app):
    tile = Tile(code='GRLBV', label='TEST', category='items')
    assert repr(tile) == '<Tile GRLBV: TEST>'


def test_tile_code_unique(app, db):
    t1 = Tile(code='GRLBV', label='FIRST', category='items')
    db.session.add(t1)
    db.session.commit()

    t2 = Tile(code='GRLBV', label='SECOND', category='items')
    db.session.add(t2)
    with pytest.raises(Exception):
        db.session.commit()


def test_tile_code_validation_invalid(app):
    with pytest.raises(ValueError):
        Tile(code='XXX', label='BAD', category='items')


def test_tile_code_normalized_uppercase(app, db):
    tile = Tile(code='grlbv', label='LOWER', category='items')
    assert tile.code == 'GRLBV'


def test_tile_user_relationship(app, db):
    user = User(username='tilemaker', email='tm@example.com')
    user.set_password('pass')
    db.session.add(user)
    db.session.commit()

    tile = Tile(
        code='GRLBV', label='CUSTOM', category='custom',
        is_custom=True, created_by_id=user.id,
    )
    db.session.add(tile)
    db.session.commit()

    assert tile.created_by.username == 'tilemaker'
    assert tile in user.tiles
