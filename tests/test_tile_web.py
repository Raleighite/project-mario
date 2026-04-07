from app.models import Tile


def _seed_tile(db):
    tile = Tile(code='GRLBV', label='START', category='starts', note='60s start')
    db.session.add(tile)
    db.session.commit()
    return tile


def test_tiles_index_page(client, db):
    _seed_tile(db)
    response = client.get('/tiles')
    assert response.status_code == 200
    assert b'START' in response.data
    assert b'GRLBV' in response.data


def test_tiles_index_filter_category(client, db):
    _seed_tile(db)
    response = client.get('/tiles?category=starts')
    assert response.status_code == 200
    assert b'START' in response.data


def test_tile_detail_page(client, db):
    tile = _seed_tile(db)
    response = client.get(f'/tiles/{tile.id}')
    assert response.status_code == 200
    assert b'START' in response.data
    assert b'<svg' in response.data


def test_tile_detail_not_found(client):
    response = client.get('/tiles/9999', follow_redirects=True)
    assert response.status_code == 200
    assert b'not found' in response.data.lower()


def test_tile_print_page(client, db):
    tile = _seed_tile(db)
    response = client.get(f'/tiles/{tile.id}/print')
    assert response.status_code == 200
    assert b'<svg' in response.data
    assert b'Print' in response.data


def test_tile_create_requires_login(client):
    response = client.get('/tiles/create')
    assert response.status_code == 302


def test_tile_create_valid(auth_client, db):
    response = auth_client.post('/tiles/create', data={
        'code': 'GRYPB',
        'label': 'MY CUSTOM',
        'category': 'custom',
        'note': 'A custom tile',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert Tile.query.filter_by(code='GRYPB').first() is not None


def test_tile_create_invalid_code(auth_client, db):
    response = auth_client.post('/tiles/create', data={
        'code': 'XXXXX',
        'label': 'BAD',
        'category': 'custom',
    })
    assert response.status_code == 200
    assert b'Invalid color' in response.data
