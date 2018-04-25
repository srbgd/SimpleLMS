from core import Core
from config import Config

from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from forms import LoginForm, RegistrationForm, EditProfileForm, ChangePasswordForm, SearchForm, SelectForm, ApproveForm
from forms import AddBookForm, AddReferenceBookForm, AddJournalForm, AddAVForm, AddCopies

import json
from functools import wraps

doc_attributes = json.loads(open('documents.json').read())

app = Flask(__name__)
app.config.from_object(Config)
core = None


def login_required(func):
	"""Decorator to require to be logged"""
	@wraps(func)
	def wrapper(*args, **kwargs):
		user_id = session.get('user_id')
		if user_id is not None:
			return func(*args, **kwargs)
		else:
			flash("Please log in")
		return redirect(url_for('login'))
	return wrapper


def can_do_a_thing_wrapper(thing):
	"""Helping function to check whether a user can perform a certain action"""
	user_id = session.get('user_id')
	if user_id is not None:
		if can_do("can_" + thing) or core.check_permissions(get_current_user()['type'], thing):  # cookies are on
			return True
		else:
			return redirect(url_for("sorry"))
	else:
		flash("Please log in")
		return redirect(url_for("login"))


def can_do_a_thing_to_cookie(user_id, thing):
	"""Helping function to check whether a user can perform a certain action.
	Returns 1 if a user can, 0 otherwise"""
	if core.check_permissions(core.find_by_id(user_id)['type'], thing):
		return "1"
	else:
		return "0"


def can_modify_wrapper(func):
	"""decorator to check whether a user has permission 'modify' """
	@wraps(func)
	def wrapper(*args, **kwargs):
		can_do = can_do_a_thing_wrapper('modify')
		return func(*args, **kwargs) if can_do is True else can_do
	return wrapper


def can_add_wrapper(func):
	"""decorator to check whether a user has permission 'insert' (add documents) """
	@wraps(func)
	def wrapper(*args, **kwargs):
		can_do = can_do_a_thing_wrapper('insert')
		return func(*args, **kwargs) if can_do is True else can_do
	return wrapper


def can_delete_wrapper(func):
	"""decorator to check whether a user has permission 'delete' (documents)"""
	@wraps(func)
	def wrapper(*args, **kwargs):
		can_do = can_do_a_thing_wrapper('delete')
		return func(*args, **kwargs) if can_do is True else can_do
	return wrapper


def can_place_outstanding_request_wrapper(func):
	"""decorator to check whether a user has permission 'place outstanding request' """
	@wraps(func)
	def wrapper(*args, **kwargs):
		can_do = can_do_a_thing_wrapper('outstanding-request')
		return func(*args, **kwargs) if can_do is True else can_do
	return wrapper


def can_edit_user_page_wrapper(func):
	"""decorator to check whether a user can modify user page of a given user"""
	@wraps(func)
	def wrapper(user_id):
		current_user_id = session.get('user_id')
		can_do = can_do_a_thing_wrapper('modify')
		if can_do is True or current_user_id == user_id:
			return func(user_id)
		else:
			return can_do
	return wrapper


def can_check_out_wrapper(func):
	"""decorator to check whether a user has permission 'check out' """
	@wraps(func)
	def wrapper(*args, **kwargs):
		can_do = can_do_a_thing_wrapper('check_out')
		if can_do is True:
			return func(*args, **kwargs)
		else:
			return can_do
	return wrapper


def admin_required(func):
	"""decorator to check whether a user is admin"""
	@wraps(func)
	def wrapper(*args, **kwargs):
		user = get_current_user()
		if user['type'] == 'admin':
			return func(*args, **kwargs)
		else:
			return redirect(url_for("sorry"))
	return wrapper


def can_do(action):
	"""translate cookies to True and False for a given action"""
	return True if request.cookies.get(action) == "1" else False


def can_add():
	return can_do("can_insert")


def can_modify():
	return can_do("can_modify")


def can_delete():
	return can_do("can_delete")


def can_check_out():
	return can_do("can_check_out")


def checked_box(box, box_cookies=None):
	"""return 'checked' if a check box is chosen"""
	if box_cookies is None:
		box_cookies = request.cookies.get(box)
	if box == 'where':
		inquiry = 'keywords'
	else:
		inquiry = 'AND'
	return 'checked' if box_cookies == inquiry else ''


def get_current_user():
	"""return current user (from encrypted cookies)"""
	return core.find_by_id(session.get('user_id'))


def get_current_user_id():
	"""return current user id (from encrypted cookies)"""
	return session.get('user_id')


def get_names_and_types_from_queue(priority_queue):
	"""From queue of requests get names and types of users"""
	names_and_types = []
	for request in priority_queue:
		user = core.find_by_id(request['attributes']['user_id'])
		names_and_types.append((user['attributes']['name'], user['type']))
	return names_and_types


def add_n_copies(origin_id, n):
	"""add n copies of book origin_id"""
	if n is not None:
		for i in range(n):
			core.add_copy(origin_id, dict())


def user_requested_to_return(copy_id):
	"""Check if user requested to return a document"""
	return (core.find("request", {"action": "return", "target_id": copy_id, "user_id": get_current_user()['id']})) != []


def user_requested_to_check_out(doc_id):
	"""Check if a user requested to check out a document"""
	return (core.find("request", {"action": "check_out", "target_id": doc_id, "user_id": get_current_user()['id']})) != []


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


def user_checked(doc_id):
	"""return True if user checked document with id=doc_id"""
	copies = get_copies(get_current_user_id())
	checked = None
	for copy in copies:
		if copy['attributes']['origin_id'] == doc_id:
			checked = copy['id']
	return checked


def get_fines(document):
	return sum([core.get_fine(copy) for copy in core.find("copy", {"origin_id": document['id']})] + [0])


def get_set_of_permissions_in_cookie():
	return ["modify", "insert", "delete", "check_out"]


def get_copies(user_id):
	"""get copies of user with id = user_id"""
	return core.find(type="copy", attributes={"user_id": user_id})


def user_documents_names(copies):
	"""method for getting names of origin books of given copies"""
	documents_names = []
	for copy in copies:
		documents_names.append(core.find_by_id(copy['attributes']['origin_id'])['attributes']['title'])
	return documents_names


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
		if request['attributes']['action'] == "check_out":
			documents.append(core.find_by_id(request['attributes']['target_id']))
		else:
			documents.append(
				core.find_by_id(core.find_by_id(request['attributes']['target_id'])['attributes']['origin_id']))
	return documents


@app.route('/', methods=['POST', 'GET'])
@app.route('/documents', methods=['POST', 'GET'])
@login_required
def documents():
	"""rendering documents (main page)"""
	search_form = SearchForm(request.form)
	if request.method == "POST":
		return search_results(search_form.search.data)
	return render_template('documents/documents.html', documents=core.find_all_documents(), user=get_current_user(),
						   can_modify=can_modify(), search_form=search_form)


@app.route('/results', methods=['POST', 'GET'])
def search_results(search_string):
	"""search for given string "search" """
	search_form = SearchForm(request.form)
	if request.form.get('keywords') is not None:
		where = "keywords"
	else:
		where = "title"
	if request.form.get('and') is not None:
		how = "AND"
	else:
		how = "OR"
	results = core.search(what=search_string, how=how, where=where)
	if results is []:
		flash('No results found!')
		resp = make_response(redirect('/'))
	else:
		resp = make_response(render_template('documents/results.html', documents=results, user=get_current_user(), can_modify=can_modify(), search_form=search_form, where=checked_box('where',where), how=checked_box('how',how)))
	resp.set_cookie('how', how)
	resp.set_cookie('where', where)
	return resp


@app.route('/document/<int:doc_id>')
@login_required
def document(doc_id):
	"""rendering document page with id=doc_id"""
	document = core.find_by_id(doc_id)
	if not core.check_user_type(document['type']):
		copies = core.find("copy", {"origin_id": doc_id})
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
		return render_template('documents/document.html', document=core.find_by_id(doc_id), user=get_current_user(),
							   can_modify=can_modify(), can_delete=can_delete(),
							   available_copies=available_copies, held_copies=held_copies, checked=user_checked(doc_id),
							   names=names, overdue_days=overdue_days(held_copies), requested=user_requested_to_check_out(doc_id),
							   requested_to_return=user_requested_to_return(copy_id), copy_id=copy_id,
							   overdue=get_overdue(copy_id), can_renew=core.can_renew(doc_id, get_current_user()),
							   priority_queue=priority_queue, names_and_types=names_and_types,
							   can_place_outstanding_request = core.check_permissions(get_current_user()["type"], "outstanding-request"),
							   is_outstanding_request=core.placed_outstanding_request(doc_id))
	else:
		return redirect(url_for('sorry'))


@app.route('/edit_document/<int:doc_id>', methods=["GET", "POST"])
@can_modify_wrapper
def edit_document(doc_id):
	"""editing documents page with id=doc_id"""
	document = core.find_by_id(doc_id)
	add_copies = AddCopies(request.form)
	if document['type'] == "book" or document['type'] == "best_seller":
		form = AddBookForm(request.form)
		attributes = doc_attributes[0]["attributes"]
	elif document['type'] == "reference_book":
		form = AddReferenceBookForm(request.form)
		attributes = doc_attributes[1]["attributes"]
		add_copies = None
	elif document['type'] == "journal_article":
		form = AddJournalForm(request.form)
		attributes = doc_attributes[3]["attributes"]
	else:
		form = AddAVForm(request.form)
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
		core.log(get_current_user_id(), "modify a document", doc_id)
		if add_copies:
			add_n_copies(doc_id, add_copies.number.data)
			if add_copies.number.data is not None:
				core.log(get_current_user_id(), "add n copies", doc_id, "n="+str(add_copies.number.data))
		return redirect(url_for("document", doc_id=doc_id))
	elif request.method == 'GET':
		old_attributes = core.find_by_id(doc_id)['attributes']
		for attribute in attributes:
			form[attribute].data = old_attributes[attribute]
	return render_template("documents/add_document.html", form=form, attributes=attributes, user=get_current_user(),
						   can_add=can_add(), add_copies=add_copies,
						   can_modify=can_modify())


@app.route('/delete_document/<int:doc_id>', methods=["GET", "POST"])
@can_delete_wrapper
def delete_document(doc_id):
	"""rendering removing documents"""
	if core.delete_book(doc_id):
		core.log(get_current_user_id(), "delete a document", doc_id)
		return redirect(url_for("documents"))
	else:
		flash("Failed to delete document with doc_id={}, document has held copies".format(doc_id))
		return redirect(url_for("document", doc_id=doc_id))


@app.route('/add_documents/')
@can_modify_wrapper
def add_documents():
	"""rendering add documents page"""
	return render_template('documents/add_documents.html', user=get_current_user(),
						   can_add=can_add(), can_modify=can_modify())


@app.route('/add_document/<int:action_id>', methods=["GET", "POST"])
@can_add_wrapper
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
			form = AddBookForm(request.form)
			if form['is_best_seller'].data == 'best_seller':
				target = 'best_seller'
			else:
				target = 'book'
			attributes = doc_attributes[0]["attributes"]
		elif action_id == 2:
			form = AddReferenceBookForm(request.form)
			attributes = doc_attributes[1]["attributes"]
			target = 'reference_book'
			add_copies = None
		elif action_id == 3:
			form = AddJournalForm(request.form)
			attributes = doc_attributes[3]["attributes"]
			target = 'journal_article'
		else:
			form = AddAVForm(request.form)
			attributes = doc_attributes[4]["attributes"]
			target = 'audio_video'
		if form.validate_on_submit():
			flash('Adding document {}'.format(form.title))
			new_attributes = {}
			for attribute in attributes:
				new_attributes[attribute] = form[attribute].data
			if add_copies:
				n = add_copies.number.data if add_copies.number.data is not None else 0
				doc_id = core.add_document_with_copies(target=target, attributes=new_attributes, n=n)
				core.log(get_current_user_id(), 'add a document', doc_id)
			else:
				core.add(target=target, attributes=new_attributes)
			return redirect(url_for('add_documents'))
		return render_template("documents/add_document.html", title='Add document', form=form, attributes=attributes,
							   user=get_current_user(), add_copies=add_copies,
							   can_modify=can_modify(), can_add=can_add())
	else:
		return redirect(url_for('sorry'))


@app.route('/delete_copy/<int:origin_id>')
@can_modify_wrapper
def delete_copy(origin_id):
	"""Delete 1 copy of a document"""
	core.db.delete_one({"type": "copy", "attributes.origin_id": origin_id, "attributes.user_id": None})
	core.log(get_current_user_id(),"delete n copies", origin_id, "n=1")
	return redirect(url_for("document", doc_id=origin_id))


@app.route('/delete_copies/<int:origin_id>')
@can_modify_wrapper
def delete_copies(origin_id):
	"""Delete all available copies of a document"""
	if can_modify_wrapper():
		core.delete_available_copies(origin_id)
		core.log(get_current_user_id(), "delete n copies", origin_id, "n=all available")
		return redirect(url_for("document", doc_id=origin_id))
	else:
		return redirect(url_for("sorry"))


@app.route('/user/')
def user_free():
	"""redirecting for page with current user page"""
	return redirect(url_for('user', user=get_current_user()))


@app.route('/user/<int:user_id>')
@can_edit_user_page_wrapper
def user(user_id):
	"""rendering user page with id=user_id"""
	copies = get_copies(user_id)
	documents_names = user_documents_names(copies)
	(overdues_and_fines, total_fine) = overdue_days_and_fines(copies)
	notifications = core.get_notifications(user_id)
	return render_template("users/user.html", user=get_current_user(), a_user=core.find_by_id(user_id), copies=copies,
						   documents=documents_names, overdues_and_fines=overdues_and_fines, total_fine=total_fine,
						   notifications=notifications, can_delete=can_delete(),
						   a_user_can_check_out=True if can_do_a_thing_to_cookie(user_id, "check_out") == "1" else False,
						   can_modify=can_modify(), can_change_password=user_id == get_current_user_id())


@app.route('/edit_profile/<int:user_id>', methods=["POST", "GET"])
@can_edit_user_page_wrapper
@admin_required
def edit_profile(user_id):
	"""rendering editing profile page"""
	form = EditProfileForm(request.form)
	select_type_form = SelectForm(request.form)  # Select new type of a user
	user = core.find_by_id(user_id)
	if form.validate_on_submit():
		if select_type_form.type.data == "None":
			new_type = user['type']
		else:
			new_type = select_type_form.type.data
		attributes = {"login": form.login.data, "name": form.name.data,
					  "address": form.address.data, "phone-number": form.phone_number.data,
					  "card-number": form.card_number.data}
		core.modify(id=user_id, attributes=attributes, new_type=new_type)
		core.log(get_current_user_id(), "modify a user", user_id)
		flash('Your changes have been saved.')
		return redirect(url_for('user', user_id=user_id))
	elif request.method == 'GET':
		form.login.data = user['attributes']['login']
		form.name.data = user['attributes']['name']
		form.address.data = user['attributes']['address']
		form.phone_number.data = user['attributes']['phone-number']
		form.card_number.data = user['attributes']['card-number']
	return render_template('users/edit_profile.html', title='Edit Profile',
						   form=form, user=get_current_user(), approve_form=select_type_form,
						   can_modify=can_modify())


@app.route('/change_password/<int:user_id>', methods=["POST", "GET"])
@can_edit_user_page_wrapper
def change_password(user_id):
	"""rendering change password"""
	form = ChangePasswordForm(request.form)
	if form.validate_on_submit():
		attributes = {"password": form.password.data}
		core.modify(user_id, attributes)
		core.log(get_current_user_id(), "modify a user", user_id, "change password")
		flash('Your changes have been saved.')
		return redirect(url_for('user', user_id=user_id))
	return render_template('users/change_password.html', title='Edit Profile',
						   form=form, user=get_current_user(), can_modify=can_modify())


@app.route('/request_document/<int:doc_id>', methods=["GET", "POST"])
@can_check_out_wrapper
def request_document(doc_id):
	"""For user to request a document to check out"""
	if core.request_check_out(doc_id, get_current_user()):
		return redirect(url_for("document", doc_id=doc_id))
	else:
		flash("Failed to request a document with id={}".format(doc_id))
		return redirect(url_for("document", doc_id=doc_id))


@app.route('/request_return/<int:copy_id>', methods=["POST", "GET"])
@can_check_out_wrapper
def request_return(copy_id):
	"""For user to request a document to return"""
	if not core.request_return(copy_id, get_current_user()):
		flash("Failed to return document with id={}".format(copy_id))
	return redirect(url_for("document", doc_id=core.find_by_id(copy_id)['attributes']['origin_id']))


@app.route("/renew/<int:doc_id>")
@can_check_out_wrapper
def renew(doc_id):
	"""Renew a document by current user"""
	if not core.renew(doc_id, get_current_user()):
		flash("Failed to renew book with id= {}".format(doc_id))
	return redirect(url_for("document", doc_id=doc_id))


@app.route('/check_out/<int:doc_id>')
@can_check_out_wrapper
def check_out(doc_id):
	"""check our document with id=doc_id"""
	if core.check_out(doc_id, dict()):
		core.log(get_current_user_id(), "check out", doc_id)
		flash("Checked out document with id {}".format(doc_id))
	else:
		flash("Failed to checked out document with id {}".format(doc_id))
	return redirect(url_for('document', doc_id=doc_id))


@app.route("/users")
@can_modify_wrapper
def users():
	return render_template("users/users.html", users=core.find_all_users(), user=get_current_user(), can_modify=can_modify())


@app.route("/overdue_users")
@can_modify_wrapper
def overdue_users():
	"""For librarian to get users with overdue"""
	return render_template("users/users.html", users=core.get_all_users_with_overdue(), user=get_current_user(), can_modify=can_modify())


@app.route('/return/<int:copy_id>')
@can_modify_wrapper
def return_document(copy_id):
	"""rendering returning copy with id=copy_id"""
	if core.give_back(copy_id) is not None:
		flash("Returned book with id {}".format(copy_id))
	else:
		flash("Failed to return book with id {}".format(copy_id))
	return redirect(url_for('document', doc_id=core.find_by_id(copy_id)['attributes']['origin_id']))


@app.route('/checked_out')
@can_modify_wrapper
def checked_out():
	"""Check if a current user can check out"""
	checked_out = core.get_all_checked_out_documents()
	fines = [get_fines(document) for document in checked_out]
	return render_template("documents/checked_out.html", documents=checked_out, user=get_current_user(), fines=fines,
						   can_modify=can_modify())


@app.route('/delete_user/<int:user_id>')
@can_delete_wrapper
def delete_user(user_id):
	"""Delete a user with given id"""
	copies = get_copies(user_id)
	if len(copies) > 0:
		flash("Failed to delete user with id {}. He has documents to return".format(user_id))
		return redirect(url_for("user", user_id=user_id))
	core.db.delete(user_id)
	core.log(get_current_user_id(), "delete a user", user_id)
	return redirect(url_for("users"))


@app.route('/registration_requests', methods=["GET", "POST"])
@can_add_wrapper
def registration_requests():
	"""For librarian to assign a user's status"""
	users = core.get_all_unconfirmed_users()
	forms = [ApproveForm(request.form) for i in range(len(users))]
	for i in range(len(forms)):
		if forms[i].validate_on_submit():
			if forms[i].student.data:
				new_type = "student"
			elif forms[i].faculty.data:
				new_type = "faculty"
			elif forms[i].visiting_professor.data:
				new_type = "visiting-professor"
			elif forms[i].libr1.data:
				new_type = "librarian-privilege-1"
			elif forms[i].libr2.data:
				new_type = "librarian-privilege-2"
			elif forms[i].libr3.data:
				new_type = "librarian-privilege-3"
			if forms[i].decline.data:
				core.delete(id=users[i]['id'])
				core.log(get_current_user_id(), "decline registration", users[i]['id'], new_type)
			else:
				core.modify(id=users[i]['id'], new_type=new_type)
				core.log(get_current_user_id(), "accept registration", users[i]['id'], new_type)
			return redirect(url_for("registration_requests"))
	return render_template("users/registration_requests.html", user=get_current_user(), users=users, forms=forms,
						   can_modify=can_modify())


@app.route('/documents_requests/', methods=['GET', 'POST'])
@can_modify_wrapper
def documents_requests():
	"""For librarian to work with documents' requests"""
	requests = core.courteous_find({"type": "request"})
	if requests:
		users = get_users(requests)
		documents = get_documents(requests)
	else:
		users = []
		documents = []
	return render_template("documents/documents_requests.html", user=get_current_user(), requests=requests, users=users,
						   documents=documents, can_modify=can_modify())


@app.route('/approve_request/<int:req_id>')
@can_modify_wrapper
def approve_request(req_id):
	"""for librarian: approve request"""
	req = core.find_by_id(req_id)
	if req['attributes']['action'] == "check_out":
		if not core.approve_check_out(req['id'], get_current_user()):
			flash("failed to approve check out")
		core.log(get_current_user_id(), 'approve to check out', req['attributes']['target_id'], "of a user with id " + str(req['attributes']['user_id']))
	else:
		if not core.approve_return(req['id'], get_current_user()):
			flash("failed to approve return")
		core.log(get_current_user_id(), 'approve to return', req['attributes']['target_id'],
				 "of a user with id " + str(req['attributes']['user_id']))
	return redirect(url_for("documents_requests"))


@app.route('/decline_request/<int:req_id>')
@can_modify_wrapper
def decline_request(req_id):
	"""for librarian: decline request"""
	req = core.find_by_id(req_id)
	if req['attributes']['action'] == "check_out":
		if not core.decline_check_out(req['id'], get_current_user()):
			flash("failed to decline check out")
		core.log(get_current_user_id(), 'decline to check out', req['attributes']['target_id'],
					 "of a user with id " + str(req['attributes']['user_id']))
	else:
		if not core.decline_return(req['id'], get_current_user()):
			flash("failed to decline return")
		core.log(get_current_user_id(), 'decline to return', req['attributes']['target_id'],
				 "of a user with id " + str(req['attributes']['user_id']))
	return redirect(url_for("documents_requests"))


@app.route('/outstanding_request_on/<int:doc_id>')
@can_place_outstanding_request_wrapper
def outstanding_request_on(doc_id):
	"""for librarian: place an outstanding request"""
	core.outstanding_request(doc_id, get_current_user())
	core.log(get_current_user_id(), "place an outstanding request", doc_id)
	return redirect(url_for("document", doc_id=doc_id))


@app.route('/outstanding_request_off/<int:doc_id>')
@can_place_outstanding_request_wrapper
def outstanding_request_off(doc_id):
	"""for librarian: take off an outstanding request"""
	core.delete_outstanding_request(doc_id)
	core.log(get_current_user_id(), "take off an outstanding request", doc_id)
	return redirect(url_for("document", doc_id=doc_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
	"""rendering registration"""
	form = RegistrationForm(request.form)
	if form.validate_on_submit():
		new_user = {"login": form.login.data, "password": form.password.data, "name": form.name.data,
					"address": form.address.name, "phone-number": form.phone_number.data,
					"card-number": form.card_number.data}
		# if core.register(form.type.data, new_user):
		if core.register("unconfirmed", new_user):
			flash('Register requested for user {}'.format(
				form.login.data))
			return redirect(url_for('login'))
		else:
			flash('Failed to register')
	return render_template('users/register.html', title='Register', form=form, user=get_current_user(),
						   can_modify=can_modify())


@app.route('/login', methods=['GET', 'POST'])
def login():
	"""rendering login"""
	form = LoginForm(request.form)
	if form.validate_on_submit():
		user_id = core.login(form.login.data, form.password.data)
		if user_id is not False:
			session['user_id'] = user_id
			flash('Login requested for user {}, remember_me={}'.format(
				form.login.data, form.remember_me.data))
			resp = make_response(redirect(url_for('documents')))
			permissions = get_set_of_permissions_in_cookie()
			for permission in permissions:
				resp.set_cookie("can_" + permission, can_do_a_thing_to_cookie(user_id, permission))
			return resp
	return render_template('users/login.html', title='Sign In', form=form, can_modify=can_modify())


@app.route('/logout')
def logout():
	"""login without attributes - means logout"""
	core.login()
	session.pop('user_id', None)
	resp = make_response(redirect(url_for('login')))
	permissions = get_set_of_permissions_in_cookie()
	for permission in permissions:
		resp.set_cookie("can_" + permission, "0")
	return resp


@app.route('/all_notifications')
@can_modify_wrapper
def all_notifications():
	"""for librarian: all notification of all users"""
	notifications = core.get_all_notifications()
	return render_template("users/all_notifications.html", notifications=notifications, user=get_current_user(),
						   can_modify=can_modify())


@app.route('/delete_all_notifications')
@can_modify_wrapper
def delete_all_notifications():
	"""for librarian: delete all notification of all users"""
	core.delete_all_notifications()
	return redirect(url_for('all_notifications'))


@app.route('/logs')
@admin_required
def logs():
	"""for admin: see all logs of the system"""
	logs = core.get_sorted_logs()
	return render_template("logs.html", logs=logs, user=get_current_user(), can_modify=can_modify())


@app.route('/delete_all_logs')
@admin_required
def delete_all_logs():
	"""for admin: delete all logs"""
	core.delete_all_logs()
	return redirect(url_for("logs"))


@app.route('/sorry')
def sorry():
	"""page for wrong permissions"""
	return render_template('sorry.html', info='No permissions', user=get_current_user(),
						   can_modify=can_modify())


if __name__ == '__main__':
	core = Core(True)
	app.run(debug=True, threaded=True)