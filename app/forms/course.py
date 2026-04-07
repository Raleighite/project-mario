from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    plate_type = SelectField(
        'Base Plate Type',
        choices=[('mils', 'MILS Plate (recommended)'), ('standard', 'Standard Base Plate')],
        default='mils',
    )
    is_public = BooleanField('Make this course public')
    submit = SubmitField('Create Course')
