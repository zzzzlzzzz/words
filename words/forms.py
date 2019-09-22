from string import ascii_lowercase, ascii_uppercase, digits, punctuation

from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.recaptcha.validators import Recaptcha
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Regexp, ValidationError


class PasswordStrong:
    def __init__(self, lowercase_n=1, uppercase_n=1, digits_n=1, punctuations_n=1):
        self.lowercase_n = lowercase_n
        self.uppercase_n = uppercase_n
        self.digits_n = digits_n
        self.punctuations_n = punctuations_n

    def __call__(self, form, field):
        password = frozenset(field.data)
        if not all((len(password & frozenset(ascii_lowercase)) >= self.lowercase_n,
                    len(password & frozenset(ascii_uppercase)) >= self.uppercase_n,
                    len(password & frozenset(digits)) >= self.digits_n,
                    len(password & frozenset(punctuation)) >= self.punctuations_n)):
            raise ValidationError('Field must be contains unique '
                                  '{} lower case letter, {} upper case letter, '
                                  '{} digit, {} punctuation.'.format(self.lowercase_n, self.uppercase_n,
                                                                     self.digits_n, self.punctuations_n))


class SignUpForm(FlaskForm):
    username = StringField('Username', [DataRequired(), Length(5, 32), Regexp('^[a-z0-9_]*$', message='Field must be contains lower case letters, digits and _.')])
    password = PasswordField('Password', [DataRequired(), Length(8, 32), PasswordStrong()])
    password_repeat = PasswordField('Password repeat', [DataRequired(), EqualTo('password')])
    recaptcha = RecaptchaField(validators=[Recaptcha('ReCaptcha invalid')])
    submit = SubmitField('Sign Up')


class SignInForm(FlaskForm):
    username = StringField('Username', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    recaptcha = RecaptchaField(validators=[Recaptcha('ReCaptcha invalid')])
    submit = SubmitField('Sign In')
