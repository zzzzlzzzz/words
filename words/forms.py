from string import ascii_lowercase, ascii_uppercase, digits, punctuation
import re

from flask_bootstrap import bootstrap_find_resource
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileField
from flask_wtf.recaptcha.validators import Recaptcha
from wtforms import StringField, PasswordField, SubmitField
from wtforms.widgets import TextArea, HTMLString
from wtforms.validators import DataRequired, Length, EqualTo, Regexp, Optional, ValidationError


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
    username = StringField('Username', [DataRequired(), Length(5, 16), Regexp('^[a-z0-9_]*$', message='Field must be contains lower case letters, digits and _.')])
    password = PasswordField('Password', [DataRequired(), Length(8, 32), PasswordStrong()])
    password_repeat = PasswordField('Password repeat', [DataRequired(), EqualTo('password')])
    recaptcha = RecaptchaField(validators=[Recaptcha('ReCaptcha invalid')])
    submit = SubmitField('Sign Up')


class SignInForm(FlaskForm):
    username = StringField('Username', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    recaptcha = RecaptchaField(validators=[Recaptcha('ReCaptcha invalid')])
    submit = SubmitField('Sign In')


class PasswordChangeForm(FlaskForm):
    old_password = PasswordField('Old password', [DataRequired()])
    password = PasswordField('New password', [DataRequired(), Length(8, 32), PasswordStrong()])
    password_repeat = PasswordField('New password repeat', [DataRequired(), EqualTo('password')])
    submit = SubmitField('Change')


class MarkdownEditor(TextArea):
    MARKDOWN_TEMPLATE = '''{}
<script src="{}"></script>
<script>
var simplemde = new SimpleMDE({{element: document.getElementById("{}"), spellChecker: false, promptURLs: true}});
</script>
'''

    def __call__(self, field, **kwargs):
        return HTMLString(self.MARKDOWN_TEMPLATE.format(super().__call__(field, **kwargs),
                                                        bootstrap_find_resource('simplemde.js', cdn='simplemde-js'),
                                                        field.id))


class ProfileForm(FlaskForm):
    logotype = FileField('Logotype', [Optional()])
    first_name = StringField('First name', [Optional(), Length(max=32)])
    last_name = StringField('Last name', [Optional(), Length(max=32)])
    about = StringField('About', [Optional()], widget=MarkdownEditor())
    submit = SubmitField('Save')


class PostForm(FlaskForm):
    content = StringField('Post', [Regexp(r'''^# [\w\d\s]{1,256}$''', re.MULTILINE, message='Start your message with Heading (Ctrl-H)')], widget=MarkdownEditor())
    submit = SubmitField('Post It')
