from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField
from wtforms.validators import DataRequired, Length, EqualTo

class HomePage(FlaskForm):
    g_ios = RadioField('gIOS', validators=[])
    ap_ports = RadioField('AP-Ports', validators=[])
    used_port_inventory = RadioField('Used Port Inventory', validators=[])
    garp = RadioField('PA Gratuitous ARP', validators=[])
    becu = RadioField('PA Intra-zone Security Rule Conversion', validators=[])

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