from datetime import datetime, timezone
from app.extensions import db


class Course(db.Model):
    PLATE_TYPES = ('mils', 'standard')
    PLATE_STUDS = 32  # studs per side on a standard LEGO base plate

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    plate_type = db.Column(db.String(20), default='mils', nullable=False)
    canvas_width = db.Column(db.Integer, default=1200, nullable=False)
    canvas_height = db.Column(db.Integer, default=800, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    created_by = db.relationship('User', backref='courses')
    tile_placements = db.relationship(
        'CourseTile', backref='course', cascade='all, delete-orphan', lazy='dynamic',
    )

    def to_dict(self, include_tiles=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_public': self.is_public,
            'plate_type': self.plate_type,
            'plate_studs': self.PLATE_STUDS,
            'canvas_width': self.canvas_width,
            'canvas_height': self.canvas_height,
            'created_by_id': self.created_by_id,
            'created_by_username': self.created_by.username if self.created_by else None,
            'tile_count': self.tile_placements.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_tiles:
            data['tiles'] = [tp.to_dict() for tp in self.tile_placements.all()]
        return data

    def __repr__(self):
        return f'<Course {self.id}: {self.name}>'


class CourseTile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, index=True)
    tile_id = db.Column(db.Integer, db.ForeignKey('tile.id'), nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    plate_index = db.Column(db.Integer, default=0, nullable=False)

    tile = db.relationship('Tile')

    def to_dict(self):
        return {
            'id': self.id,
            'tile_id': self.tile_id,
            'x': self.x,
            'y': self.y,
            'plate_index': self.plate_index,
            'tile': self.tile.to_dict() if self.tile else None,
        }

    def __repr__(self):
        return f'<CourseTile course={self.course_id} tile={self.tile_id} ({self.x},{self.y})>'
