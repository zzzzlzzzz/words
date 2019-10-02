from string import ascii_lowercase, ascii_uppercase, digits, punctuation

from flask_bootstrap import bootstrap_find_resource
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileField
from flask_wtf.recaptcha.validators import Recaptcha
from wtforms import StringField, PasswordField, SubmitField
from wtforms.widgets import TextArea, HTMLString, Input
from wtforms.validators import DataRequired, Length, EqualTo, Regexp, Optional, ValidationError

from words.models import Service


class PasswordStrong:
    LOWERCASE = frozenset(ascii_lowercase)
    UPPERCASE = frozenset(ascii_uppercase)
    DIGITS = frozenset(digits)
    PUNCTUATION = frozenset(punctuation)

    def __init__(self, lowercase_n=1, uppercase_n=1, digits_n=1, punctuations_n=1):
        self.lowercase_n = lowercase_n
        self.uppercase_n = uppercase_n
        self.digits_n = digits_n
        self.punctuations_n = punctuations_n

    def __call__(self, form, field):
        password = frozenset(field.data)
        if not all((len(password & self.LOWERCASE) >= self.lowercase_n,
                    len(password & self.UPPERCASE) >= self.uppercase_n,
                    len(password & self.DIGITS) >= self.digits_n,
                    len(password & self.PUNCTUATION) >= self.punctuations_n)):
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
    title = StringField('Title', [DataRequired(), Length(max=200)])
    content = StringField('Post', [Length(min=1)], widget=MarkdownEditor())
    submit = SubmitField('Post It')


class BackWidget(Input):
    def __call__(self, field, **kwargs):
        return HTMLString('<a href="{}" {}>{}</a>'.format(field.href, self.html_params(**kwargs), field.label.text))


class TelegramServiceForm(FlaskForm):
    channel_name = StringField('Channel name', [DataRequired(), Regexp(r'''@[a-z0-9]{5,}''', message='Channel name is invalid')])
    submit = SubmitField('Save')
    back = SubmitField('Back', widget=BackWidget())

    def dump(self):
        """Dump form data for store to database"""
        return dict(channel_name=self.channel_name.data, )


class TwitterServiceForm(FlaskForm):
    consumer_key = StringField('Consumer key', [DataRequired()])
    consumer_secret = StringField('Consumer secret', [DataRequired()])
    access_token_key = StringField('Access token key', [DataRequired()])
    access_token_secret = StringField('Access token secret', [DataRequired()])
    submit = SubmitField('Save')
    back = SubmitField('Back', widget=BackWidget())

    def dump(self):
        """Dump form data for store to database"""
        return dict(consumer_key=self.consumer_key.data,
                    consumer_secret=self.consumer_secret,
                    access_token_key=self.access_token_key,
                    access_token_secret=self.access_token_secret, )


service_forms = {
    Service.TELEGRAM.name: TelegramServiceForm,
    Service.TWITTER.name: TwitterServiceForm,
}
