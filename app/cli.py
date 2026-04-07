import json
import os
import click
from flask import current_app
from app.extensions import db
from app.models.tile import Tile


def register_commands(app):
    @app.cli.group()
    def tiles():
        """Manage tile data."""
        pass

    @tiles.command()
    def seed():
        """Seed the database with known tiles from tiles.json."""
        data_path = os.path.join(
            os.path.dirname(__file__), 'data', 'tiles.json'
        )
        with open(data_path) as f:
            tile_data = json.load(f)

        added = 0
        skipped = 0
        for entry in tile_data:
            existing = Tile.query.filter_by(code=entry['code']).first()
            if existing:
                skipped += 1
                continue
            tile = Tile(
                code=entry['code'],
                label=entry['label'],
                category=entry['category'],
                note=entry.get('note'),
                hit_points=entry.get('hit_points'),
                is_custom=False,
            )
            db.session.add(tile)
            added += 1

        db.session.commit()
        click.echo(f'Seeded {added} tiles, skipped {skipped} existing.')

    @tiles.command()
    @click.option('--yes', is_flag=True, help='Skip confirmation prompt.')
    def clear(yes):
        """Remove all non-custom (seeded) tiles."""
        count = Tile.query.filter_by(is_custom=False).count()
        if count == 0:
            click.echo('No seeded tiles to remove.')
            return
        if not yes:
            click.confirm(f'Delete {count} seeded tiles?', abort=True)
        Tile.query.filter_by(is_custom=False).delete()
        db.session.commit()
        click.echo(f'Removed {count} seeded tiles.')
