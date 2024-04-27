from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired


class NoticeForm(FlaskForm):
    title = StringField('Имя', validators=[DataRequired()])
    content = TextAreaField("Описание")
    image = FileField('Фотография')  # IMAGE
    points = TextAreaField('Возможное место нахождения (обязательно указывать адрес)')
    submit = SubmitField('Отправить')