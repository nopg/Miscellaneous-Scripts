from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField
from wtforms.validators import DataRequired, Length, EqualTo

class HomePage(FlaskForm):
    choices = [
        ("g_ios", "gIOS"),
        ("ap_ports", "AP-Ports"),
        ("used_port_inventory", "Used Port Inventory"),
        ("garp", "PA Gratuitous ARP"),
        ("becu", "PA Intra-Zone Security Rule Conversion")
    ]
    main_menu = RadioField("Choose your Tool.", choices=choices)
    submit = SubmitField('Login')
    remember = BooleanField('Remember Me')

class LoginForm(FlaskForm):
    pa_ip = StringField('IP Address', validators=[DataRequired(), Length(min=2,max=32)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2,max=32)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=2,max=32)])

    submit = SubmitField('Login')
    remember = BooleanField('Remember Me')

class PaPAN(FlaskForm):
    pa = BooleanField('PA or PAN?')