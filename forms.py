from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange


"""This is file for rendering forms"""


class LoginForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class EditProfileForm(FlaskForm):
    # type = SelectField('Status', choices=[('unconfirmed', 'Unconfirmed'), ('faculty', 'Faculty'), ('student', 'Student'), ('librarian', 'Librarian')])
    login = StringField('Login', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    phone_number = StringField('Phone number', validators=[DataRequired()])
    card_number = StringField('Card number', validators=[DataRequired()])

    submit = SubmitField('Submit')


class AddCopies(FlaskForm):
    number = IntegerField('Add number of copies', validators=[NumberRange(min=0)])


class SearchForm(FlaskForm):
    search = StringField('Search')


class AddBookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    authors = StringField('Authors', validators=[DataRequired()])
    publisher = StringField('Publisher', validators=[DataRequired()])
    edition = StringField('Edition', validators=[DataRequired()])
    date = StringField('Date', validators=[DataRequired()])
    is_best_seller = SelectField('Is bestseller', choices=[('best_seller', 'Yes'), ('book','No')], validators=[DataRequired()])
    price = IntegerField('Price', validators=[NumberRange(min=1)])
    keywords = StringField('Keywords')
    submit = SubmitField('Submit')


class AddReferenceBookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    authors = StringField('Authors', validators=[DataRequired()])
    publisher = StringField('Publisher', validators=[DataRequired()])
    edition = StringField('Edition', validators=[DataRequired()])
    date = StringField('Date', validators=[DataRequired()])
    keywords = StringField('Keywords')
    submit = SubmitField('Submit')


class AddJournalForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    authors = StringField('Authors', validators=[DataRequired()])
    journal = StringField('Journal', validators=[DataRequired()])
    editors = StringField('Edition', validators=[DataRequired()])
    date = StringField('Date', validators=[DataRequired()])
    price = IntegerField('Price', validators=[NumberRange(min=1)])
    keywords = StringField('Keywords')
    submit = SubmitField('Submit')


class AddAVForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    authors = StringField('Authors', validators=[DataRequired()])
    price = IntegerField('Price', validators=[NumberRange(min=1)])
    keywords = StringField('Keywords')
    submit = SubmitField('Submit')


class ChangePasswordForm(FlaskForm):
    password = PasswordField('New Password', [
        DataRequired(),
        EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password', validators=[DataRequired()])
    submit = SubmitField('Submit')


class RegistrationForm(FlaskForm):
    login = StringField('Login', [DataRequired()])
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


class SelectForm(FlaskForm):
    type = SelectField('Status',
                       choices=[('unconfirmed', 'Unconfirmed'), ('faculty', 'Faculty'), ('student', 'Student'),('visiting-professor',"Visiting Professor"),
                                ('librarian-privilege-1', 'Librarian with privilege 1'), ('librarian-privilege-2', 'Librarian with privilege 2'),
                                ('librarian-privilege-3', 'Librarian with privilege 3')])
    submit = SubmitField('Save', validators=[DataRequired()])


class ApproveForm(FlaskForm):
    student = SubmitField(label="Student")
    faculty = SubmitField(label="Faculty")
    visiting_professor = SubmitField(label="Visiting Professor")
    libr1 = SubmitField(label="Libr-1")
    libr2 = SubmitField(label="Libr-2")
    libr3 = SubmitField(label="Libr-3")
    decline = SubmitField(label="Decline")