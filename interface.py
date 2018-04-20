from core import Core
from mongo_database import DataBase as db
from config import Config

from flask import Flask, render_template, request, redirect, url_for, flash, session
from forms import LoginForm, RegistrationForm, EditProfileForm, ChangePasswordForm, SearchForm, SelectForm, ApproveForm, ApproveDocumentForm
from forms import AddBookForm, AddReferenceBookForm, AddJournalForm, AddAVForm, AddCopies

import json
from functools import wraps


doc_attributes = json.loads(open('documents.json').read())

app = Flask(__name__)
app.config.from_object(Config)
core = None


def login_required(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		user_id = session.get('user_id')
		# print(user_id)
		# assert type(user_id) == int
		if user_id is not None:
			return func(*args, **kwargs)
		else:
			flash("Please log in")
		return redirect(url_for('login'))
	return wrapper


def can_do_a_thing(thing, user_id):
	if user_id is not None:
		# print("thing", thing, core.get_permissions(core.find_by_id(user_id)))
		if thing in core.get_permissions(core.find_by_id(user_id)):
			return True
		else:
			return redirect(url_for("sorry"))
	else:
		flash("Please log in")
		return redirect(url_for("login"))


def can_modify(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		user_id = session.get('user_id')
		# assert type(user_id) == int
		can_do = can_do_a_thing('modify', user_id)
		if can_do is True:
			return func(*args, **kwargs)
		else:
			return can_do
	return wrapper


def can_edit_user_page(func):
	@wraps(func)
	def wrapper(user_id):
		current_user_id = session.get('user_id')
		can_do = can_do_a_thing('modify', current_user_id)
		print(current_user_id, user_id, can_do)
		if can_do is True or current_user_id == user_id:
			return func(user_id)
		else:
			return can_do
	return wrapper


def can_check_out(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		user_id = session.get('user_id')
		can_do = can_do_a_thing('checkout', user_id)
		# print("can_do", can_do)
		if can_do is True:
			return func(*args, **kwargs)
		else:
			return can_do
	return wrapper


@app.route('/')
@app.route('/documents', methods=['POST','GET'])
@login_required
def documents():
	"""rendering documents (main page)"""
	search_form = SearchForm()
	if search_form.validate_on_submit():
		return search_results(search_form)
	return render_template('documents/documents.html', documents=core.find_all_documents(), user=get_current_user())


def get_current_user():
	return core.find_by_id(session.get('user_id'))


def get_current_user_id():
	return session.get('user_id')

@app.route('/check_out/<int:doc_id>')
@can_check_out
def check_out(doc_id):
	"""check our document with id=doc_id"""
	if core.check_out(doc_id, dict()):
		flash("Checked out document with id {}".format(doc_id))
	else:
		flash("Failed to checked out document with id {}".format(doc_id))
	return redirect(url_for('document', doc_id=doc_id))


@app.route("/users")
@can_modify
def users():
	return render_template("users/users.html", users = core.find_all_users(), user=get_current_user())


@app.route("/overdue_users")
@can_modify
def overdue_users():
	"""For librarian to get users with overdue"""
	return render_template("users/users.html", users=core.get_all_users_with_overdue(), user=get_current_user())


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
@can_modify
def return_document(copy_id):
	"""rendering returning copy with id=copy_id"""
	if core.give_back(copy_id) is not None:
		flash("Returned book with id {}".format(copy_id))
	else:
		flash("Failed to return book with id {}".format(copy_id))
	return redirect(url_for('document', doc_id=core.find_by_id(copy_id)['attributes']['origin_id']))


@app.route('/document/<int:doc_id>')
@login_required
def document(doc_id):
	"""rendering document page with id=doc_id"""
	document = core.find_by_id(doc_id)
	if document["type"] != "student" and document["type"] != "faculty" and document["type"] != "librarian":
		copies = core.find("copy",{"origin_id":doc_id})
		available_copies = 0

		held_copies = []
		for copy in copies:
			if copy['attributes']['user_id'] is None:
				available_copies += 1
			else:
				held_copies.append(copy)
		names = users_names(held_copies)
		current_user = get_current_user()
		if current_user and core.find("copy", {"user_id": current_user['id'], "origin_id": doc_id}) != []:
			copy_id = core.find("copy", {"user_id": current_user['id'], "origin_id": doc_id})[0]['id']
		else:
			copy_id = 0
		priority_queue = core.get_queue(doc_id)
		names_and_types = get_names_and_types_from_queue(priority_queue)
		# print(core.placed_outstanding_request(doc_id))
		# print("hey")
		# print(get_overdue(copy))

		# "C:\Users\Asus\Projects\slms2\core.py", line
		# 364, in decline_check_out
		# self.notify_queue(self.find_by_id(request_id)['attributes']['target_id'])
		# requested_to_return = user_requested_to_return(copy_id)
		# print(requested_to_return)
		return render_template('documents/document.html', document=core.find_by_id(doc_id), user=get_current_user(),
								available_copies=available_copies, held_copies=held_copies, checked=user_checked(doc_id),
								names=names, overdue_days=overdue_days(held_copies), requested=user_requested(doc_id),
								requested_to_return=user_requested_to_return(copy_id), copy_id=copy_id,
								overdue=get_overdue(copy_id), can_renew=core.can_renew(doc_id, get_current_user()), priority_queue=priority_queue,
								names_and_types=names_and_types, is_outstanding_request=core.placed_outstanding_request(doc_id))
	else:
		return redirect(url_for('sorry'))


def get_names_and_types_from_queue(priority_queue):
	"""From queue of requests get names and types of users"""
	names_and_types = []
	for request in priority_queue:
		user = core.find_by_id(request['attributes']['user_id'])
		names_and_types.append((user['attributes']['name'], user['type']))
	return names_and_types


@app.route("/renew/<int:doc_id>")
@can_check_out
def renew(doc_id):
	"""Renew a document by current user"""
	if not core.renew(doc_id, get_current_user()):
		flash("Failed to renew book with id= {}".format(doc_id))
	return redirect(url_for("document", doc_id=doc_id))


@can_check_out
def user_requested_to_return(copy_id):
	"""Check if user requested to return a document"""
	# print("request", core.find("request", {"action": "return", "target_id": doc_id, "user_id": get_current_user()['id']}))
	return (core.find("request", {"action": "return", "target_id": copy_id, "user_id": get_current_user()['id']})) != []


@can_check_out
def user_requested(doc_id):
	"""Check if a user requested to check out a document"""
	return (core.find("request", {"action": "check-out", "target_id": doc_id, "user_id": get_current_user()['id']})) != []


@app.route('/delete_copy/<int:origin_id>')
@can_modify
def delete_copy(origin_id):
	"""Delete 1 copy of a document"""
	core.db.delete_one({"type": "copy", "attributes.origin_id": origin_id, "attributes.user_id": None})
	return redirect(url_for("document", doc_id=origin_id))


@app.route('/delete_copies/<int:origin_id>')
@can_modify
def delete_copies(origin_id):
	"""Delete all available copies of a document"""
	if can_modify():
		core.delete_available_copies(origin_id)
		return redirect(url_for("document", doc_id=origin_id))
	else:
		return redirect(url_for("sorry"))


def overdue_days(copies):
	"""Get overdue days from copies itemes in database"""
	overdue_days = []
	for copy in copies:
		overdue_days.append(get_overdue(copy))
	return overdue_days


def get_overdue(copy):
	"""Get an overdue of a copy"""
	try:
		return core.get_overdue(copy)
	except Exception:
		return 0


def overdue_days_and_fines(copies):
	"""Get overdue days and fines (pairs) of copies"""
	overdues_and_fines = []
	sum = 0
	for copy in copies:
		pair = overdue_and_fine(copy)
		overdues_and_fines.append(pair)
		sum += pair[1]
	return overdues_and_fines, sum


def overdue_and_fine(copy):
	"""Get overdue days and fines (pair) of copy"""
	try:
		return core.get_overdue(copy), core.get_fine(copy)
	except Exception:
		return 0


def users_names(copies):
	"""names of users holding given copies"""
	names = []
	for copy in copies:
		names.append(core.find_by_id(copy['attributes']['user_id'])['attributes']['name'])
	return names


@can_check_out
def user_checked(doc_id):
	"""return True if user checked document with id=doc_id"""
	copies = get_copies(get_current_user_id())
	checked = None
	for copy in copies:
		if copy['attributes']['origin_id'] == doc_id:
			checked = copy['id']
	return checked


@app.route('/edit_document/<int:doc_id>', methods=["GET", "POST"])
@can_modify
def edit_document(doc_id):
	"""editing documents page with id=doc_id"""
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
		try:
			core.modify(doc_id, new_attributes, new_type=form.is_best_seller.data)
		except Exception:
			core.modify(doc_id, new_attributes)
		if add_copies:
			add_n_copies(doc_id, add_copies.number.data)
		return redirect(url_for("document", doc_id=doc_id))
	elif request.method == 'GET':
		old_attributes = core.find_by_id(doc_id)['attributes']
		for attribute in attributes:
			form[attribute].data = old_attributes[attribute]

	return render_template("documents/add_document.html", form=form, attributes=attributes, user=get_current_user(), add_copies=add_copies)


@app.route('/delete_document/<int:doc_id>', methods=["GET", "POST"])
@can_modify
def delete_document(doc_id):
	"""rendering removing documents"""
	if core.delete_book(doc_id):
		return redirect(url_for("documents"))
	else:
		flash("Failed to delete document with doc_id={}, document has held copies".format(doc_id))
		return redirect(url_for("document", doc_id=doc_id))


@app.route('/add_documents/')
@can_modify
def add_documents():
	"""rendering add documents page"""
	return render_template('documents/add_documents.html', user=get_current_user())


@app.route('/checked_out')
@can_modify
def checked_out():
	"""Check if a current user can check out"""
	checked_out = core.get_all_checked_out_documents()
	fines = [get_fines(document) for document in checked_out]
	return render_template("documents/checked_out.html", documents=checked_out, user=get_current_user(), fines=fines)


def get_fines(document):
	return sum([core.get_fine(copy) for copy in core.find("copy",{"origin_id": document['id']})] + [0])


@app.route('/add_document/<int:action_id>', methods=["GET", "POST"])
@can_modify
def add_document(action_id):
	"""add document
	action_ids:
	1: book
	2: reference_book
	3: journal article
	4: audio_video """
	if action_id > 0 and action_id < 5:
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
			add_copies = None
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
			if add_copies:
				n = add_copies.number.data if add_copies.number.data is not None else 0
				core.add_document_with_copies(target=target, attributes=new_attributes, n=n)
			else:
				core.add(target=target, attributes=new_attributes)
			return redirect(url_for('add_documents'))
		return render_template("documents/add_document.html", title='Add document', form=form, attributes=attributes, user=get_current_user(), add_copies=add_copies)
	else:
		return redirect(url_for('sorry'))


@app.route('/delete_user/<int:user_id>')
@can_modify
def delete_user(user_id):
	"""Delete a user with given id"""
	copies = get_copies(user_id)
	if len(copies) > 0:
		flash("Failed to delete user with id {}. He has documents to return".format(user_id))
		return redirect(url_for("user", user_id=user_id))
	core.db.delete(user_id)
	return redirect(url_for("users"))


@app.route('/login', methods=['GET', 'POST'])
def login():
	"""rendering login"""
	form = LoginForm()
	if form.validate_on_submit():
		user_id = core.login(form.login.data, form.password.data)
		assert type(user_id) == int
		if user_id is not False:
			session['user_id'] = user_id
			flash('Login requested for user {}, remember_me={}'.format(
				form.login.data, form.remember_me.data))
			return redirect(url_for('documents'))
	return render_template('users/login.html', title='Sign In', form=form)


@app.route('/user/<int:user_id>')
@can_edit_user_page
def user(user_id):
	"""rendering user page with id=user_id"""
	copies = get_copies(user_id)
	documents_names = user_documents_names(copies)
	(overdues_and_fines, total_fine) = overdue_days_and_fines(copies)
	notifications = core.get_notifications(user_id)
	return render_template("users/user.html", user=get_current_user(), a_user=core.find_by_id(user_id), copies=copies,
											documents=documents_names, overdues_and_fines=overdues_and_fines, total_fine=total_fine, notifications=notifications)


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
	return redirect(url_for('user', user=get_current_user()))


@app.route('/edit_profile/<int:user_id>', methods=["POST", "GET"])
@can_edit_user_page
def edit_profile(user_id):
	"""rendering editing profile page"""
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
		core.modify(id=user_id, attributes=attributes, new_type=new_type)
		flash('Your changes have been saved.')
		return redirect(url_for('user', user_id=user_id))
	elif request.method == 'GET':
		form.login.data = user['attributes']['login']
		form['name'].data = user['attributes']['name']
		form.address.data = user['attributes']['address']
		form.phone_number.data = user['attributes']['phone-number']
		form.card_number.data = user['attributes']['card-number']
		if "modify" not in core.get_permissions(get_current_user()):
			approve_form = None
	return render_template('users/edit_profile.html', title='Edit Profile',
						   form=form, user=user, approve_form=approve_form)


@app.route('/change_password/<int:user_id>', methods=["POST", "GET"])
@can_edit_user_page
def change_password(user_id):
	"""rendering change password"""
	form = ChangePasswordForm()
	if form.validate_on_submit():
		attributes = {"password": form.password.data}
		core.modify(user_id, attributes)
		flash('Your changes have been saved.')
		return redirect(url_for('user', user_id = user_id))
	return render_template('users/change_password.html', title='Edit Profile',
						   form=form, user=get_current_user())


@app.route('/sorry')
def sorry():
	"""page for wrong permissions"""
	return render_template('sorry.html', info='No permissions', user=get_current_user())


@app.route('/logout')
def logout():
	"""login without attributes - means logout"""
	core.login()
	session.pop('user_id', None)
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
		if core.register("unconfirmed", new_user):
			flash('Register requested for user {}'.format(
				form.login.data))
			return redirect(url_for('login'))
		else:
			flash('Failed to register')
	return render_template('users/register.html', title='Register', form=form, user=get_current_user())


@app.route('/registration_requests', methods=["GET","POST"])
@can_modify
def registration_requests():
	"""For librarian to assign a user's status"""
	users = core.get_all_unconfirmed_users()
	forms = [ApproveForm(request.form) for i in range(len(users))]
	for i in range(len(forms)):
		if forms[i].validate_on_submit():
			if forms[i].student.data:
				core.modify(id=users[i]['id'], new_type="student")
			elif forms[i].faculty.data:
				core.modify(id=users[i]['id'], new_type="faculty")
			elif forms[i].librarian.data:
				core.modify(id=users[i]['id'], new_type="librarian")
			elif forms[i].visiting_professor.data:
				core.modify(id=users[i]['id'], new_type="visiting-professor")
			elif forms[i].decline.data:
				core.delete(id=users[i]['id'])
			return redirect(url_for("registration_requests"))
	return render_template("users/registration_requests.html", user=get_current_user(), users=users, forms=forms)


def get_users(requests):
	"""Get users from request items in database"""
	users = []
	for request in requests:
		users.append(core.find_by_id(request['attributes']['user_id']))
	return users


def get_documents(requests):
	"""Get documents from request items in database"""
	documents = []
	for request in requests:
		if request['attributes']['action'] == "check-out":
			documents.append(core.find_by_id(request['attributes']['target_id']))
		else:
			documents.append(core.find_by_id(core.find_by_id(request['attributes']['target_id'])['attributes']['origin_id']))
	return documents


@app.route('/documents_requests/', methods=['GET', 'POST'])
@can_modify
def documents_requests():
	"""For librarian to work with documents' requests"""
	requests = core.courteous_find({"type": "request"})
	if requests:
		users = get_users(requests)
		documents = get_documents(requests)
	else:
		users = []
		documents = []
	return render_template("documents/documents_requests.html", user=get_current_user(), requests=requests, users=users, documents=documents)


@app.route('/approve_request/<int:req_id>')
@can_modify
def approve_request(req_id):  # TODO: if didn't find req
	req = core.find_by_id(req_id)
	if req['attributes']['action'] == "check-out":
		if not core.approve_check_out(req['id'], get_current_user()):
			flash("failed to approve check out")
	else:
		if not core.approve_return(req['id'], get_current_user()):
			flash("failed to approve return")
	return redirect(url_for("documents_requests"))


@app.route('/decline_request/<int:req_id>')
@can_modify
def decline_request(req_id):
	req = core.find_by_id(req_id)
	if req['attributes']['action'] == "check-out":
		if not core.decline_check_out(req['id'], get_current_user()):
			flash("failed to decline check out")
	else:
		if not core.decline_return(req['id'], get_current_user()):
			flash("failed to decline return")
	return redirect(url_for("documents_requests"))




@app.route('/request_document/<int:doc_id>', methods=["GET", "POST"])
@can_check_out
def request_document(doc_id):
	"""For user to request a document to check out"""
	if core.request_check_out(doc_id, get_current_user()):
		return redirect(url_for("document", doc_id=doc_id))
	else:
		flash("Failed to request a document with id={}".format(doc_id))
		return redirect(url_for("document", doc_id=doc_id))


@app.route('/request_return/<int:copy_id>', methods=["POST","GET"])
@can_check_out
def request_return(copy_id):
	"""For user to request a document to return"""
	if not core.request_return(copy_id, get_current_user()):
		flash("Failed to return document with id={}".format(copy_id))
	return redirect(url_for("document", doc_id=core.find_by_id(copy_id)['attributes']['origin_id']))


@app.route('/outstanding_request_on/<int:doc_id>')
@can_modify
def outstanding_request_on(doc_id):
	core.outstanding_request(doc_id, get_current_user())
	return redirect(url_for("document", doc_id=doc_id))


@app.route('/outstanding_request_off/<int:doc_id>')
@can_modify
def outstanding_request_off(doc_id):
	core.delete_outstanding_request(doc_id)
	return redirect(url_for("document",doc_id=doc_id))


@app.route('/run_routines')
@can_modify
def run_routines():
	core.run_routines()


@app.route('/all_notifications')
@can_modify
def all_notifications():
		notifications = core.get_all_notifications()
		return render_template("users/all_notifications.html", notifications=notifications, user=get_current_user())


@app.route('/delete_all_notifications')
@can_modify
def delete_all_notifications():
	core.delete_all_notifications()
	return redirect(url_for('all_notifications'))


if __name__ == '__main__':
	core = Core(True)
	app.run(debug=True, threaded=True)


