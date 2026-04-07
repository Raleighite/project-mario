from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    is_public = BooleanField('Make this course public')
    submit = SubmitField('Create Course')
