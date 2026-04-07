from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models import Tile
from app.utils.barcode import validate_tile_code

CATEGORY_CHOICES = [
    ('starts', 'Starts'),
    ('checkpoints', 'Checkpoints'),
    ('characters', 'Characters'),
    ('enemies', 'Enemies'),
    ('bosses', 'Bosses'),
    ('items', 'Items & Power-ups'),
    ('treasures', 'Treasures'),
    ('interactive', 'Interactive'),
    ('food_gifts', 'Food & Gifts'),
    ('yoshi_eggs', 'Yoshi Eggs'),
    ('mario_kart', 'Mario Kart'),
    ('environment', 'Environment'),
    ('special', 'Special'),
    ('provisional', 'Provisional'),
    ('custom', 'Custom'),
]


class TileForm(FlaskForm):
    code = StringField('Barcode Code', validators=[DataRequired(), Length(min=5, max=5)])
    label = StringField('Label', validators=[DataRequired(), Length(max=120)])
    category = SelectField('Category', choices=CATEGORY_CHOICES, validators=[DataRequired()])
    note = TextAreaField('Notes', validators=[Optional()])
    hit_points = IntegerField('Hit Points', validators=[Optional()])
    submit = SubmitField('Create Tile')

    def validate_code(self, code):
        valid, error = validate_tile_code(code.data)
        if not valid:
            raise ValidationError(error)
        existing = Tile.query.filter_by(code=code.data.upper()).first()
        if existing:
            raise ValidationError('A tile with this code already exists.')
