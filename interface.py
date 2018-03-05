from core import Core

from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from forms import LoginForm, RegistrationForm, EditProfileForm, ChangePasswordForm, SearchForm
from forms import AddBookForm, AddReferenceBookForm, AddJournalForm, AddAVForm, AddCopies

import json
doc_attributes = json.loads(open('documents.json').read())

app = Flask(__name__)
app.config.from_object(Config)
core = None


@app.route('/')
@app.route('/documents', methods=['POST','GET'])
def documents():
	"""rendering documents (main page)"""
	search_form = SearchForm()
	if search_form.validate_on_submit():
		return search_results(search_form)
	return render_template('documents/documents.html', documents=core.find_all_documets(), user=core.current_user, search_form=search_form)


@app.route('/check_out/<int:doc_id>')
def check_out(doc_id):
	"""check our document with id=doc_id"""
	if can_check_out():
		if core.check_out(doc_id, dict()):
			flash("Checked out document with id {}".format(doc_id))
		else:
			flash("Failed to checked out document with id {}".format(doc_id))
		return redirect(url_for('document', doc_id=doc_id))
	else:
		return redirect(url_for('sorry'))


def can_check_out():
	"""return True if current user can check our documents"""
	try:
		return "checkout" in core.get_permissions(core.current_user)
	except Exception:
		return False


@app.route('/results')
def search_results(search):
	"""search for given string "search" """
	search_string = search.data['search']
	results = core.search(search_string)
	if not results:
		flash('No results found!')
		return redirect('/')
	else:
		return render_template('results.html', results=results)


def add_n_copies(origin_id, n):
	"""add n copies of book origin_id"""
	if n is not None:
		for i in range(n):
			core.add_copy(origin_id, dict())


@app.route('/return/<int:copy_id>')
def return_document(copy_id):
	"""rendering returning copy with id=copy_id"""
	if can_modify():
		if core.give_back(copy_id, dict()):
			flash("Returned book with id {}".format(copy_id))
		else:
			flash("Failed to return book with id {}".format(copy_id))
		return redirect(url_for('document', doc_id=core.find_by_id(copy_id)['attributes']['origin_id']))
	return redirect(url_for('sorry'))


@app.route('/document/<int:doc_id>')
def document(doc_id):
	"""rendering document page with id=doc_id"""
	document = core.find_by_id(doc_id)
	if document["type"] != "student" and document["type"] != "faculty" and document["type"] != "librarian":
		copies = core.courteous_find({"attributes.origin_id":doc_id})
		available_copies = []

		held_copies = []
		for copy in copies:
			if copy['attributes']['user_id'] is None:
				available_copies.append(copy)
			else:
				held_copies.append(copy)
		names = users_names(held_copies)
		return render_template('documents/document.html', document=core.find_by_id(doc_id), user=core.current_user,
							   available_copies=available_copies, held_copies=held_copies, checked=user_checked(doc_id),
							   names=names)
	else:
		return redirect(url_for('sorry'))


def users_names(copies):
	"""names of users holding given copies"""
	names = []
	for copy in copies:
		names.append(core.find_by_id(copy['attributes']['user_id'])['attributes']['name'])
	return names


def user_checked(doc_id):
	"""return True if user checked document with id=doc_id"""
	if can_check_out():
		copies = get_copies(core.current_user['id'])
		checked = None
		for copy in copies:
			if copy['attributes']['origin_id'] == doc_id:
				checked = copy['id']
		return checked
	return False


@app.route('/edit_document/<int:doc_id>', methods=["GET", "POST"])
def edit_document(doc_id):
	"""editing documents page with id=doc_id"""
	if can_modify():
		document = core.find_by_id(doc_id)
		add_copies = AddCopies()
		if document['type'] == "book" or document['type'] == "best_seller":
			form = AddBookForm()
			attributes = doc_attributes[0]["attributes"]
		elif document['type'] == "reference_book":
			form = AddReferenceBookForm()
			attributes = doc_attributes[1]["attributes"]
			add_copies = None
		elif document['type'] == "journal_article":
			form = AddJournalForm()
			attributes = doc_attributes[3]["attributes"]
		else:
			form = AddAVForm()
			attributes = doc_attributes[4]["attributes"]
		if form.validate_on_submit():
			flash('Adding document {}'.format(form.title))
			new_attributes = {}
			for attribute in attributes:
				new_attributes[attribute] = form[attribute].data
			core.modify(doc_id, new_attributes)
			add_n_copies(doc_id, add_copies.number.data)
			return redirect(url_for("document", doc_id=doc_id))
		elif request.method == 'GET':
			old_attributes = core.find_by_id(doc_id)['attributes']
			for attribute in attributes:
				form[attribute].data = old_attributes[attribute]

		return render_template("documents/add_document.html", form=form, attributes=attributes, user=core.current_user, add_copies=add_copies)
	else:
		return redirect(url_for('sorry'))


@app.route('/delete_document/<int:doc_id>', methods=["GET", "POST"])
def delete_document(doc_id):
	"""rendering removing documents"""
	if can_modify():
		core.delete(doc_id, dict())
		return redirect(url_for("documents"))
	else:
		return redirect(url_for('sorry'))


@app.route('/add_documents/')
def add_documents():
	"""rendering add documents page"""
	if can_modify():
		return render_template('documents/add_documents.html', user=core.current_user)
	else:
		return redirect(url_for('sorry'))


@app.route('/add_document/<int:action_id>', methods=["GET", "POST"])
def add_document(action_id):
	"""add document
	action_ids:
	1: book
	2: reference_book
	3: journal article
	4: audio_video """
	if can_modify() and action_id > 0 and action_id < 5:
		if action_id == 1:
			form = AddBookForm()
			if form['is_best_seller'].data == 'best-seller':
				target = 'best_seller'
			else:
				target = 'book'
			attributes = doc_attributes[0]["attributes"]
		elif action_id == 2:
			form = AddReferenceBookForm()
			attributes = doc_attributes[1]["attributes"]
			target = 'reference_book'
		elif action_id == 3:
			form = AddJournalForm()
			attributes = doc_attributes[3]["attributes"]
			target = 'journal_article'
		else:
			form = AddAVForm()
			attributes = doc_attributes[4]["attributes"]
			target = 'audio_video'
		if form.validate_on_submit():
			flash('Adding document {}'.format(form.title))
			new_attributes = {}
			for attribute in attributes:
				new_attributes[attribute] = form[attribute].data
			core.add(target=target, attributes=new_attributes)
			return redirect(url_for('add_documents'))
		return render_template("documents/add_document.html", title='Add document', form=form, attributes=attributes, user=core.current_user)
	else:
		return redirect(url_for('sorry'))






@app.route('/login', methods=['GET', 'POST'])
def login():
	"""rendering login"""
	form = LoginForm()
	if form.validate_on_submit():
		if core.login(form.login.data, form.password.data):  # now I can use core.current_user
			flash('Login requested for user {}, remember_me={}'.format(
				form.login.data, form.remember_me.data))
			return redirect(url_for('documents'))
	return render_template('users/login.html', title='Sign In', form=form)


@app.route('/user/<int:user_id>')
def user(user_id):
	"""rendering user page with id=user_id"""
	if can_modify(user_id):
		copies = get_copies(user_id)
		documents_names = user_documents_names(copies)
		return render_template("users/user.html", user=core.find_by_id(user_id), copies=copies, documents=documents_names)
	else:
		return redirect(url_for('sorry'))


def get_copies(user_id):
	"""get copies of user with id = user_id"""
	return core.find(type="copy", attributes={"user_id": user_id})


def user_documents_names(copies):
	"""method for getting names of origin books of given copies"""
	documents_names = []
	for copy in copies:
		documents_names.append(core.find_by_id(copy['attributes']['origin_id'])['attributes']['title'])
	return documents_names


@app.route('/user/')
def user_free():
	"""redirecting for page with current user page"""
	return redirect(url_for('user', user=core.current_user))


def can_modify(user_id=-1):
	"""checking admissions"""
	try:
		return "modify" in core.get_permissions(core.current_user) or core.current_user['id'] == user_id
	except TypeError:
		return False


@app.route('/edit_profile/<int:user_id>', methods=["POST", "GET"])
def edit_profile(user_id):
	"""rendering editing profile page"""
	if can_modify(user_id):
		form = EditProfileForm()
		if form.validate_on_submit():
			attributes = {"login":form.login.data, "name": form.name.data,
													"address": form.address.data, "phone-number": form.phone_number.data}
			core.modify_current_user(user_id, attributes)
			flash('Your changes have been saved.')
			return redirect(url_for('user', user_id=user_id))
		elif request.method == 'GET':
			form.login.data = core.current_user['attributes']['login']
			form['name'].data = core.current_user['attributes']['name']
			form.address.data = core.current_user['attributes']['address']
			form.phone_number.data = core.current_user['attributes']['phone-number']
		return render_template('users/edit_profile.html', title='Edit Profile',
							   form=form, user=core.current_user)
	else:
		return redirect(url_for('sorry'))


@app.route('/change_password/<int:user_id>', methods=["POST", "GET"])
def change_password(user_id):
	"""rendering change password"""
	if can_modify(user_id):
		form = ChangePasswordForm()
		if form.validate_on_submit():
			attributes = {"password": form.password.data}
			core.modify(user_id, attributes)
			flash('Your changes have been saved.')
			return redirect(url_for('user', user_id = user_id))
		return render_template('users/change_password.html', title='Edit Profile',
							   form=form, user=core.current_user)
	else:
		return redirect(url_for('sorry'))


@app.route('/sorry')
def sorry():
	"""page for wrong admissions"""
	return render_template('sorry.html', info='No permissions', user=core.current_user)


@app.route('/logout')
def logout():
	"""login without attributes - means logout"""
	core.login()
	return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
	"""rendering registration"""
	form = RegistrationForm(request.form)
	if form.validate_on_submit():
		new_user = {"login": form.login.data, "password": form.password.data, "name" : form.name.data,
													"address": form.address.name, "phone-number": form.phone_number.data,
													"card-number": form.card_number.data}
		if core.register(form.type.data, new_user):
			flash('Register requested for user {}'.format(
				form.login.data))
			return redirect(url_for('login'))
	return render_template('users/register.html', title='Register', form=form, user=core.current_user)


if __name__ == '__main__':
	core = Core()
	app.run(debug=True)


