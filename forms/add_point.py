from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class AddPointForm(FlaskForm):
    points = TextAreaField('Возможное место нахождения (обязательно указывать адрес)')
    submit = SubmitField('Отправить')