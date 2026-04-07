from app.models import Tile, User


def _seed_tiles(db):
    tiles = [
        Tile(code='GRLBV', label='START', category='starts', note='60s start'),
        Tile(code='GRBPY', label='GOOMBA', category='enemies', hit_points=1),
        Tile(code='GRBLV', label='BOWSER', category='bosses', hit_points=10),
    ]
    db.session.add_all(tiles)
    db.session.commit()
    return tiles


def test_api_list_tiles(client, db):
    _seed_tiles(db)
    response = client.get('/api/v1/tiles')
    assert response.status_code == 200
    data = response.get_json()
    assert data['total'] == 3
    assert len(data['tiles']) == 3
    assert 'categories' in data


def test_api_list_tiles_filter_category(client, db):
    _seed_tiles(db)
    response = client.get('/api/v1/tiles?category=enemies')
    data = response.get_json()
    assert data['total'] == 1
    assert data['tiles'][0]['label'] == 'GOOMBA'


def test_api_get_tile(client, db):
    tiles = _seed_tiles(db)
    response = client.get(f'/api/v1/tiles/{tiles[0].id}')
    assert response.status_code == 200
    assert response.get_json()['code'] == 'GRLBV'


def test_api_get_tile_not_found(client):
    response = client.get('/api/v1/tiles/9999')
    assert response.status_code == 404


def test_api_create_tile_authenticated(client, db):
    user = User(username='creator', email='c@example.com')
    user.set_password('pass')
    db.session.add(user)
    db.session.commit()

    client.post('/api/v1/login', json={'username': 'creator', 'password': 'pass'})
    response = client.post('/api/v1/tiles', json={
        'code': 'GRLBV',
        'label': 'MY TILE',
        'category': 'custom',
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['code'] == 'GRLBV'
    assert data['is_custom'] is True


def test_api_create_tile_unauthenticated(client):
    response = client.post('/api/v1/tiles', json={
        'code': 'GRLBV',
        'label': 'MY TILE',
        'category': 'custom',
    })
    assert response.status_code == 401


def test_api_create_tile_invalid_code(client, db):
    user = User(username='creator2', email='c2@example.com')
    user.set_password('pass')
    db.session.add(user)
    db.session.commit()

    client.post('/api/v1/login', json={'username': 'creator2', 'password': 'pass'})
    response = client.post('/api/v1/tiles', json={
        'code': 'XXXXX',
        'label': 'BAD',
        'category': 'custom',
    })
    assert response.status_code == 400


def test_api_tile_barcode_svg(client, db):
    tiles = _seed_tiles(db)
    response = client.get(f'/api/v1/tiles/{tiles[0].id}/barcode.svg')
    assert response.status_code == 200
    assert 'image/svg+xml' in response.content_type


def test_api_tile_barcode_png(client, db):
    tiles = _seed_tiles(db)
    response = client.get(f'/api/v1/tiles/{tiles[0].id}/barcode.png')
    assert response.status_code == 200
    assert response.content_type == 'image/png'


def test_api_barcode_preview(client):
    response = client.get('/api/v1/tiles/barcode/preview?code=GRLBV')
    assert response.status_code == 200
    assert 'image/svg+xml' in response.content_type


def test_api_barcode_preview_invalid_code(client):
    response = client.get('/api/v1/tiles/barcode/preview?code=XXXXX')
    assert response.status_code == 400
