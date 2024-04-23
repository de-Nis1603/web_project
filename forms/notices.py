from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class NoticeForm(FlaskForm):
    title = StringField('Имя', validators=[DataRequired()])
    content = TextAreaField("Описание")
    points = TextAreaField('Возможное место нахождения')
    submit = SubmitField('Отправить')