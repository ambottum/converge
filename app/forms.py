from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User
from flask_wtf import Form


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class HiddenPaths(FlaskForm):
    path1 = HiddenField("Field 1")
    path2 = HiddenField("Field 2")

class HiddenFields(FlaskForm):
    path1 = HiddenField("Field 3")
    path2 = HiddenField("Field 4")    
    hmerge_headers1 = HiddenField("Field 5")
    hmerge_headers2 = HiddenField("Field 6")
    hforeign_key1 = HiddenField("Field 7")
    hforeign_key2 = HiddenField("Field 8")

    #TO DO: create two separate classes for paths & then headers & fkeys
