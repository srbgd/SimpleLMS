from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange
from jinja2 import Markup


class LoginForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class EditProfileForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    phone_number = StringField('Phone number', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddCopies(FlaskForm):
    number = IntegerField('Add number of copies')


class SearchForm(FlaskForm):
    select = SelectField('By', choices=[('-','-'),('title', 'title'), ('author', 'author')])
    search = StringField('Search')
    # go = SubmitField('search')


class AddBookForm(FlaskForm):  # ["title", "authors", "publisher", "edition", "date", "price"]
    title = StringField('Title', validators=[DataRequired()])
    authors = StringField('Authors', validators=[DataRequired()])
    publisher = StringField('Publisher', validators=[DataRequired()])
    edition = StringField('Edition', validators=[DataRequired()])
    date = StringField('Date', validators=[DataRequired()])
    is_best_seller = SelectField('Is bestseller', choices=[('best-seller', 'Yes'), ('book','No')], validators=[DataRequired()])
    #copies = IntegerField('Price', validators=[NumberRange(min=1)])
    price = IntegerField('Price', validators=[NumberRange(min=1)])
    submit = SubmitField('Submit')


class AddReferenceBookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    authors = StringField('Authors', validators=[DataRequired()])
    publisher = StringField('Publisher', validators=[DataRequired()])
    edition = StringField('Edition', validators=[DataRequired()])
    date = StringField('Date', validators=[DataRequired()])
    submit = SubmitField('Submit')


# ["title", "authors", "journal", "editors", "date", "price"]
class AddJournalForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    authors = StringField('Authors', validators=[DataRequired()])
    journal = StringField('Journal', validators=[DataRequired()])
    editors = StringField('Edition', validators=[DataRequired()])
    date = StringField('Date', validators=[DataRequired()])
    #copies = IntegerField('Price', validators=[NumberRange(min=1)])
    price = IntegerField('Price', validators=[NumberRange(min=1)])
    submit = SubmitField('Submit')


class AddAVForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    authors = StringField('Authors', validators=[DataRequired()])
    #copies = IntegerField('Price', validators=[NumberRange(min=1)])
    price = IntegerField('Price', validators=[NumberRange(min=1)])
    submit = SubmitField('Submit')


class ChangePasswordForm(FlaskForm):
    password = PasswordField('New Password', [
        DataRequired(),
        EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password', validators=[DataRequired()])
    submit = SubmitField('Submit')


# "[login", "password", "name", "address", "phone-number", "card-number"]
class RegistrationForm(FlaskForm):
    type = SelectField('Status', choices=[('faculty', 'Faculty'), ('student','Student'), ('librarian','Librarian')], validators=[DataRequired()])
    login = StringField('Login', [Length(min=4, max=25)])
    password = PasswordField('New Password', [
        DataRequired(),
        EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    phone_number = StringField('Phone number', validators=[DataRequired()])
    card_number = StringField('Card Number', validators=[DataRequired()])
    submit = SubmitField('Register', validators=[DataRequired()])