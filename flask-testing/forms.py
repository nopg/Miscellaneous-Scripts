from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo

class LoginForm(FlaskForm):
    pa_ip = StringField('IP Address', validators=[DataRequired(), Length(min=2,max=32)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2,max=32)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=2,max=32)])

    submit = SubmitField('Login')
    remember = BooleanField('Remember Me')

class PaPAN(FlaskForm):
    pa = BooleanField('PA or PAN?')