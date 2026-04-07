from datetime import datetime, timezone
from sqlalchemy import orm
from app.extensions import db
from app.utils.barcode import validate_tile_code


class Tile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(5), unique=True, nullable=False, index=True)
    label = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(64), nullable=False, index=True)
    note = db.Column(db.Text, nullable=True)
    hit_points = db.Column(db.Integer, nullable=True)
    is_custom = db.Column(db.Boolean, default=False, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    created_by = db.relationship('User', backref='tiles')

    @orm.validates('code')
    def validate_code(self, key, value):
        value = value.upper()
        valid, error = validate_tile_code(value)
        if not valid:
            raise ValueError(f'Invalid tile code: {error}')
        return value

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'label': self.label,
            'category': self.category,
            'note': self.note,
            'hit_points': self.hit_points,
            'is_custom': self.is_custom,
            'created_by_id': self.created_by_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Tile {self.code}: {self.label}>'
