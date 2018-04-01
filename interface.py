from core import Core

from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from forms import LoginForm, RegistrationForm, EditProfileForm, ChangePasswordForm, SearchForm, SelectForm, ApproveForm, ApproveDocumentForm
from forms import AddBookForm, AddReferenceBookForm, AddJournalForm, AddAVForm, AddCopies

import sys
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
	return render_template('documents/documents.html', documents=core.find_all_documents(), user=core.current_user)  # search_form=search_form


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


@app.route("/users")
def users():
	"""rendering page of all users"""
	return render_template("users/users.html", users = core.find_all_users(), user = core.current_user)


@app.route("/overdue_users")
def overdue_users():
	return render_template("users/users.html", users=core.get_all_users_with_overdue(), user=core.current_user)


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
		if core.give_back(copy_id) is not None:
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
		available_copies = 0

		held_copies = []
		for copy in copies:
			if copy['attributes']['user_id'] is None:
				available_copies += 1
			else:
				held_copies.append(copy)
		names = users_names(held_copies)
		if core.current_user and core.find("copy", {"user_id": core.current_user['id'], "origin_id": doc_id}) != []:
			copy_id = core.find("copy", {"user_id": core.current_user['id'], "origin_id": doc_id})[0]['id']
		else:
			copy_id = 0
		return render_template('documents/document.html', document=core.find_by_id(doc_id), user=core.current_user,
							   available_copies=available_copies, held_copies=held_copies, checked=user_checked(doc_id),
							   names=names, overdue_days=overdue_days(held_copies), requested=user_requested(doc_id),
								requested_to_return=user_requested_to_return(copy_id), copy_id=copy_id, overdue=get_overdue(copy_id))

	else:
		return redirect(url_for('sorry'))


def user_requested_to_return(copy_id):
	if can_check_out():
		return (core.find("request", {"action": "return", "target_id": copy_id, "user_id": core.current_user['id']})) != []
	else:
		return False


def user_requested(doc_id):
	if can_check_out():
		return (core.find("request", {"action": "check-out", "target_id": doc_id, "user_id": core.current_user['id']})) != []
	else:
		return False


@app.route('/delete_copy/<int:origin_id>')
def delete_copy(origin_id):
	if can_modify():
		core.db.delete_one({"type": "copy", "attributes.origin_id": origin_id, "attributes.user_id": None})
		return redirect(url_for("document", doc_id=origin_id))
	else:
		return redirect(url_for("sorry"))


@app.route('/delete_copies/<int:origin_id>')
def delete_copies(origin_id):
	if can_modify():
		core.delete_available_copies(origin_id)
	else:
		return redirect(url_for("sorry"))


def overdue_days(copies):
	overdue_days = []
	for copy in copies:
		overdue_days.append(get_overdue(copy))


def get_overdue(copy):
	try:
		return core.get_overdue(copy)
	except Exception:
		return 0


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
			flash('Edited document {}'.format(form.title))
			new_attributes = {}
			for attribute in attributes:
				new_attributes[attribute] = form[attribute].data
			core.modify(doc_id, new_attributes, new_type=form.is_best_seller.data)
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
		if core.delete_book(doc_id):
			return redirect(url_for("documents"))
		else:
			flash("Failed to delete document with doc_id={}, document has held copies".format(doc_id))
			return redirect(url_for("document", doc_id=doc_id))
	else:
		return redirect(url_for('sorry'))


@app.route('/add_documents/')
def add_documents():
	"""rendering add documents page"""
	if can_modify():
		return render_template('documents/add_documents.html', user=core.current_user)
	else:
		return redirect(url_for('sorry'))


@app.route('/checked_out')
def checked_out():
	if can_modify():
		checked_out = core.get_all_checked_out_documents()
		return render_template("documents/checked_out.html", documents = checked_out, user = core.current_user)
	else:
		return redirect(url_for("sorry"))


@app.route('/add_document/<int:action_id>', methods=["GET", "POST"])
def add_document(action_id):
	"""add document
	action_ids:
	1: book
	2: reference_book
	3: journal article
	4: audio_video """
	if can_modify() and action_id > 0 and action_id < 5:
		add_copies = AddCopies()
		if action_id == 1:
			form = AddBookForm()
			if form['is_best_seller'].data == 'best_seller':
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
			n = add_copies.number.data if add_copies.number.data is not None else 0
			core.add_document_with_copies(target=target, attributes=new_attributes, n=n)
			return redirect(url_for('add_documents'))
		return render_template("documents/add_document.html", title='Add document', form=form, attributes=attributes, user=core.current_user, add_copies=add_copies)
	else:
		return redirect(url_for('sorry'))


@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
	if can_modify(user_id):
		copies = get_copies(user_id)
		print(copies)
		if len(copies) > 0:
			flash("Failed to delete user with id {}. He has documents to return".format(user_id))
			return redirect(url_for("user", user_id=user_id))
		core.db.delete(user_id)
		return redirect(url_for("users"))
	else:
		return redirect(url_for("sorry"))


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
		overdue = [get_overdue(copy) for copy in copies]
		return render_template("users/user.html", user=core.current_user, a_user=core.find_by_id(user_id), copies=copies, documents=documents_names, overdue=overdue)
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
	"""checking permissions"""
	try:
		return "modify" in core.get_permissions(core.current_user) or core.current_user['id'] == user_id
	except TypeError:
		return False


@app.route('/edit_profile/<int:user_id>', methods=["POST", "GET"])
def edit_profile(user_id):
	"""rendering editing profile page"""
	if can_modify(user_id):
		form = EditProfileForm()
		approve_form = SelectForm(request.form)
		user = core.find_by_id(user_id)
		if form.validate_on_submit():
			if approve_form.type.data == "None":
				new_type = user['type']
			else:
				new_type = approve_form.type.data
			attributes = {"login":form.login.data, "name": form.name.data,
													"address": form.address.data, "phone-number": form.phone_number.data, "card-number": form.card_number.data}
			core.modify(some_id=user_id, attributes=attributes, new_type=new_type)
			flash('Your changes have been saved.')
			return redirect(url_for('user', user_id=user_id))
		elif request.method == 'GET':
			form.login.data = user['attributes']['login']
			form['name'].data = user['attributes']['name']
			form.address.data = user['attributes']['address']
			form.phone_number.data = user['attributes']['phone-number']
			form.card_number.data = user['attributes']['card-number']
			if "modify" not in core.get_permissions(core.current_user):
				approve_form = None
		return render_template('users/edit_profile.html', title='Edit Profile',
							   form=form, user=user, approve_form=approve_form)
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
	"""page for wrong permissions"""
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
		# if core.register(form.type.data, new_user):
		if core.register(new_user):
			flash('Register requested for user {}'.format(
				form.login.data))
			return redirect(url_for('login'))
	return render_template('users/register.html', title='Register', form=form, user=core.current_user)


@app.route('/registration_requests', methods=["GET","POST"])
def registration_requests():
	if can_modify():
		users = core.get_all_unconfirmed_users()
		forms = [ApproveForm(request.form) for i in range(len(users))]
		for i in range(len(forms)):
			if forms[i].validate_on_submit():
				if forms[i].student.data:
					core.modify(some_id=users[i]['id'], new_type="student")
				elif forms[i].faculty.data:
					core.modify(some_id=users[i]['id'], new_type="faculty")
				elif forms[i].librarian.data:
					core.modify(some_id=users[i]['id'], new_type="librarian")
				elif forms[i].decline.data:
					core.delete(some_id=users[i]['id'])
				return redirect(url_for("registration_requests"))
		return render_template("users/registration_requests.html", user=core.current_user, users=users, forms=forms)
	else:
		return redirect(url_for("sorry"))


def get_users(requests):
	users = []
	for request in requests:
		users.append(core.find_by_id(request['attributes']['user_id']))
	return users


def get_documents(requests):
	documents = []
	for request in requests:
		if request['attributes']['action'] == "check-out":
			documents.append(core.find_by_id(request['attributes']['target_id']))
		else:
			documents.append(core.find_by_id(core.find_by_id(request['attributes']['target_id'])['attributes']['origin_id']))
	return documents


@app.route('/documents_requests/', methods=['GET', 'POST'])
def documents_requests():
	if can_modify():
		requests = core.courteous_find({"type": "request"})
		if requests:
			users = get_users(requests)
			documents = get_documents(requests)
		else:
			users = []
			documents = []
		print(users, documents)
		forms = [ApproveDocumentForm(request.form) for i in range(len(requests))]
		for i in range(len(forms)):
			if forms[i].validate_on_submit():
				if forms[i].approve.data:
					if requests[i]['attributes']['action'] == "check-out":
						if not core.approve_check_out(requests[i]['id']):
							flash("failed")
					else:
						if not core.approve_return(requests[i]['id']):
							flash("failed")
				elif forms[i].decline.data:
					if requests[i]['attributes']['action'] == "check-out":
						if not core.decline_check_out(requests[i]['id']):
							flash("failed")
					else:
						if not core.decline_return(requests[i]['id']):
							flash("failed")
				return redirect(url_for("documents_requests"))
		return render_template("documents/documents_requests.html", user=core.current_user, requests=requests, users=users, documents=documents, forms=forms)
	else:
		return redirect(url_for("sorry"))


@app.route('/request_document/<int:doc_id>', methods=["GET", "POST"])
def request_document(doc_id):
	if can_check_out():
		if core.request_check_out(doc_id):
			return redirect(url_for("document", doc_id=doc_id))
		else:
			flash("Failed to check out document with id={}".format(doc_id))
			return redirect(url_for("document", doc_id=doc_id))
	else:
		return redirect(url_for("sorry"))


@app.route('/request_return/<int:copy_id>', methods=["POST","GET"])
def request_return(copy_id):
	if can_check_out():
		if not core.request_return(copy_id):
			flash("Failed to return document with id={}".format(copy_id))
		doc_id = core.find_by_id(copy_id)['attributes']['origin_id']
		return redirect(url_for("document", doc_id=doc_id))
	else:
		return redirect(url_for("sorry"))


if __name__ == '__main__':
	core = Core()
	app.run(debug=True)


