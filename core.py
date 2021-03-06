from command import Command
import datetime
import json


class Core:
	"""Core class"""

	permissions = []
	"""List of command which are allowed to execute for current user"""
	documents = None
	"""List of types of documents"""
	users = None
	"""List of types of users"""
	map = None
	"""Map from command to function"""
	db = None
	"""Database"""
	id = 0
	"""Current id"""
	request_list = {'last_modified': None, 'requests': []}
	"""List of all users who must checkout a document today"""
	admin = None

	def search(self, what, where="", how=""):
		"""Searches for documents"""
		return list(filter(lambda x: (all if how == 'AND' else any)(map(lambda s: ((lambda i: str().join(map(str, i['attributes'].value()))) if where == str() else (lambda i: i['attributes'][where] if where in i['attributes'].keys() else ''))(x).lower().find(s) != -1, what.lower().split())), self.find_all_documents()))

	def log(self, user_id, action, target_id, comment=''):
		"""Logs an action"""
		self.add('log', {'user_id': user_id, 'action': action, 'target_id': target_id, 'comment': comment, 'time': datetime.datetime.now().strftime('[%d/%m/%y-%H:%M:%S]')})

	def add(self, target, attributes):
		"""Add new item to database"""
		self.db.add({
			'id': self.id,
			'type': target,
			'attributes': attributes
		})
		self.id += 1
		return self.id - 1

	def register(self, target, attributes):
		"""Add new user to database"""
		if self.check_user(target, attributes):
			self.add(target, attributes)
			return True
		else:
			return False

	def insert(self, type, attributes):
		"""Add new document to database"""
		if self.check_document(type, attributes):
			self.add(type, attributes)
			return True
		else:
			return False

	def find(self, type, attributes):
		"""Find item in database"""
		if self.check_document_type(type) or self.check_user_type(type) or type in ['', 'copy', 'request', 'renew', 'notification', 'outstanding-request', 'log']:
			return self.db.lookup(type, attributes)
		else:
			return None

	@staticmethod
	def check_available_copy(copy):
		"""Check if the copy is available"""
		return copy['attributes']['user_id'] is None

	@staticmethod
	def get_overdue(item):
		"""Get overdue of the item"""
		if not Core.check_available_copy(item):
			return (datetime.datetime.now() - datetime.datetime.strptime(item['attributes']['deadline'], '%d/%m/%Y')).days
		else:
			return None

	def get_fine(self, item):
		"""Get fine of the item"""
		overdue = Core.get_overdue(item)
		if overdue is None or overdue <= 0:
			return 0
		price = int(self.find_by_id(int(item['attributes']['origin_id']))['attributes']['price'])
		return min(overdue * 100, price)

	def check_overdue(self, i):
		"""Check if the item is overdue"""
		overdue = self.get_overdue(i)
		if overdue is None or overdue <= 0:
			return False
		else:
			return True

	def check_fine(self, i):
		"""Check if the item has fines"""
		if self.get_fine(i):
			return True
		else:
			return False

	def get_overdue_by_id(self, copy_id):
		"""Get the overdue of the copy with current id"""
		item = self.find_by_id(copy_id)
		if item['type'] != 'copy':
			return None
		return Core.get_overdue(item)

	def get_fine_by_id(self, copy_id):
		"""Get the fine of the copy with current id"""
		item = self.find_by_id(copy_id)
		if item['type'] != 'copy':
			return None
		return self.get_fine(item)

	def get_all_users_with_overdue(self):
		"""Get all users with overdue"""
		users = set()
		copies = self.find('copy', dict())
		for i in copies:
			if self.check_overdue(i):
				users.add(i['attributes']['user_id'])
		if users:
			users = self.courteous_find({"$or": [{"id": i} for i in users]})
		return list(users)

	def get_all_unconfirmed_users(self):
		"""Get all unconfirmed users"""
		return self.find('unconfirmed', {})

	def delete_available_copies(self, doc_id):
		"""Delete all copies of the document which aren't checked out now"""
		copies = self.find('copy', {'origin_id': doc_id})
		for i in copies:
			if self.check_available_copy(i):
				self.delete(i['id'])

	def delete_book(self, doc_id):
		"""Delete document with current id"""
		copies = self.find('copy', {'origin_id': doc_id})
		if all(self.check_available_copy(i) for i in copies):
			self.delete_available_copies(doc_id)
			self.delete_all_requests(doc_id)
			self.delete(doc_id)
			return True
		else:
			return False

	def delete_all_requests(self, doc_id):
		"""Delete all requests for the document"""
		requests = [i for i in self.find('request', {}) if i['attributes']['target_id'] == doc_id]
		for i in requests:
			self.delete(i['id'])

	def add_document_with_copies(self, target, attributes, n):
		"""Add new document and n copies of this document"""
		id = self.add(target, attributes)
		for i in range(n):
			self.add_copy(id)
		return id  # WARNING: CHANGED

	def get_all_checked_out_documents(self):
		"""Get all documents which have at least one checked out copy"""
		documents = set()
		copies = self.find('copy', dict())
		for i in copies:
			if not self.check_available_copy(i):
				documents.add(i['attributes']['origin_id'])
		if documents:
			documents = self.courteous_find({"$or": [{"id": i} for i in documents]})
		return list(documents)

	def courteous_find(self, attributes):
		"""Another way to find documents"""
		return self.db.courteous_lookup(attributes)

	def find_all_documents(self):
		"""Get all documents"""
		return sum([self.find(i['type'], {}) for i in self.documents], [])

	def find_all_users(self):
		"""Get all users"""
		return sum([self.find(i['type'], {}) for i in self.users], [])

	def find_by_id(self, id):
		"""Get an item by id"""
		return self.db.get_by_id(id)

	def delete(self, id, attributes = None):
		"""Delete item from database"""
		return self.db.delete(id)

	def modify(self, id, attributes={}, new_type=None):
		"""Modify item in database"""
		old_attributes = self.find_by_id(id)['attributes']
		if attributes is not None:
			for item, value in attributes.items():
				old_attributes[item] = value
		if new_type:
			return self.db.modify_and_change_type(id, attributes=old_attributes, type=new_type)
		return self.db.modify(id, old_attributes)

	def modify_user(self, user_id, attributes):
		"""Modify users attributes"""
		user = self.find_by_id(user_id)
		for item, value in attributes.items():
			user['attributes'][item] = value
		self.db.modify(user_id, user['attributes'])

	def check_document(self, type, attributes):
		"""Check if type and attributes are correct"""
		return self.check_document_type(type) and self.check_attributes(type, attributes)

	def check_attributes_soundness(self, type, attributes):
		"""Check that there are not unexpected attributes"""
		return all(i in [j for j in self.documents if j['type'] == type][0]['attributes'] for i in attributes.keys())

	def check_attributes_completeness(self, type, attributes):
		"""Check that all attributes which should be presented are presented"""
		return all(i in attributes.keys() for i in [j for j in self.documents if j['type'] == type][0]['attributes'])

	def check_attributes(self, type, attributes):
		"""Check if the attributes are sound and complete"""
		return self.check_attributes_soundness(type, attributes) and self.check_attributes_completeness(type, attributes)

	def check_document_type(self, type):
		"""Check if current type of a document exists"""
		return any(i['type'] == type for i in self.documents)

	def check_user(self, type, attributes):
		"""Check if type and attributes are correct"""
		return self.check_user_type(type) and self.check_user_attributes(type, attributes)

	def check_user_attributes(self, type, attributes):
		"""Check if the attributes are sound and complete"""
		return sorted([i for i in self.users if i['type'] == type][0]['attributes']) == sorted(list(attributes.keys()))

	def check_user_type(self, type):
		"""Check if current type of a user exists"""
		return any(i['type'] == type for i in self.users)

	def login(self, login = None, password = None):
		"""Change current user"""
		if login is password is None:
			self.normalize_request_list()
			return True
		user = self.find('', {'login': login, 'password': password})
		if user:
			self.permissions = self.get_permissions(user[0])
			self.normalize_request_list()
			return user[0]['id']
		else:
			return False

	def check_permissions(self, user_type, command):
		"""Checks if the user with current type has a permission to execute the current command"""
		if user_type == 'admin':
			return True
		return command in [i for i in self.users if i['type'] == user_type][0]['permissions']

	def add_copy(self, id, attributes = None):
		"""Add copy to database"""
		id = int(id)
		document = self.db.get_by_id(id)
		if self.check_document_type(document['type']) and 'reference-book' != document['type']:
			self.add('copy', {'origin_id': id, 'user_id': None, 'deadline': ''})
			return True
		else:
			return False

	def request(self, doc_id, action, current_user):
		"""Request an action with a document"""
		if action not in ['check_out', 'return']:
			return False
		type, attributes = 'request', {'user_id': current_user['id'], 'target_id': doc_id, 'action': action}
		if self.find(type, attributes):
			return False
		else:
			self.add(type, attributes)
			return True

	def approve_cmd(self, id, attributes = None):
		"""Approve an action (with console signature)"""
		id = int(id)
		request = self.find_by_id(id)
		action = request['attributes']['action']
		return self.approve(id, action)

	def decline_cmd(self, id, attributes = None):
		"""Decline an action (with console signature)"""
		id = int(id)
		request = self.find_by_id(id)
		action = request['attributes']['action']
		return self.decline(id, action)

	def approve(self, request_id, action, current_user):
		"""Approve an action"""
		request = self.find_by_id(request_id)
		if request['type'] != 'request':
			return False
		elif request['attributes']['action'] != action:
			return False
		elif not self.check_permissions(current_user['type'], 'approve'):
			return False
		else:
			if action == 'check_out':
				result = self.check_out(request['attributes']['target_id'], request['attributes']['user_id'])
				if result:
					self.delete(request_id)
				return result
			if action == 'return':
				result = self.give_back(request['attributes']['target_id'])
				if result:
					self.delete(request_id)
				return result
			return False

	def decline(self, request_id, action, current_user):
		"""Approve an action"""
		request = self.find_by_id(request_id)
		if request['type'] != 'request':
			return False
		elif request['attributes']['action'] != action:
			return False
		elif not self.check_permissions(current_user['type'], 'decline'):
			return False
		else:
			return self.delete(request_id)

	def delete_queue(self, doc_id):
		"""Delete all requests in the queue"""
		queue = self.get_queue(doc_id)
		for i in queue:
			self.log(i['attributes']['user_id'], 'was removed from queue', doc_id)
			self.delete(i['id'])

	def can_renew(self, id, current_user):
		"""Check if it is possible to renew the current document for the current user"""
		if self.find('renew', {'user_id': current_user['id'], 'origin_id': id}):
			return False
		if self.placed_outstanding_request(id):
			return False
		copy = self.find('copy', {'user_id': current_user['id'], 'origin_id': id})
		if copy:
			copy = copy[0]
		else:
			return False
		return not self.check_overdue(copy)

	def request_check_out(self, doc_id, current_user):
		"""Request check out a document"""
		result = self.request(doc_id, 'check_out', current_user)
		if all(not self.check_available_copy(i) for i in self.find('copy', {'origin_id': doc_id})) and result:
			message = 'You are added in a queue for the document with id {} because the document is not available right now'
			self.notify(current_user['id'], message.format(doc_id))
		return result

	def approve_check_out(self, request_id, current_user):
		"""Approve check out"""
		request = self.find_by_id(request_id)
		result = self.approve(request_id, 'check_out', current_user)
		self.notify_queue(request['attributes']['target_id'])
		return result

	def decline_check_out(self, request_id, current_user):
		"""Decline check out"""
		request = self.find_by_id(request_id)
		result = self.decline(request_id, 'check_out', current_user)
		self.notify_queue(request['attributes']['target_id'])
		return result

	def request_return(self, doc_id, current_user):
		"""Request return a document"""
		return self.request(doc_id, 'return', current_user)

	def approve_return(self, request_id, current_user):
		"""Approve return"""
		return self.approve(request_id, 'return', current_user)

	def decline_return(self, request_id, current_user):
		"""Decline return"""
		return self.decline(request_id, 'return', current_user)

	def request_check_out_cmd(self, id, attibutes = None):
		"""Request check out a document (with console signature)"""
		return self.request_check_out(int(id))

	def get_queue(self, id):
		"""Get queue for current document"""
		priority = ['student', 'visiting-professor', 'faculty']
		return sorted(self.find('request', {'target_id': id, 'action': 'check_out'}), key=lambda x: priority.index(self.find_by_id(x['attributes']['user_id'])['type']))

	@staticmethod
	def get_duration(user_type, doc_type):
		"""Get how long a user with current type can hold a document with current type"""
		duration = 21
		if user_type == 'visiting-professor':
			duration = 7
		elif user_type == 'faculty':
			duration = 28
		elif doc_type == 'best_seller':
			duration = 14
		return datetime.timedelta(days=duration)

	def renew(self, id, current_user, attributes=None):
		"""Renew a document"""
		id = int(id)
		copy = self.find('copy', {'user_id': current_user['id'], 'origin_id': id})
		if copy and not self.find('renew', {'user_id': current_user['id'], 'origin_id': id}):
			if current_user['type'] != 'visiting-professor':
				self.add('renew', {'user_id': current_user['id'], 'origin_id': id})
			timedelta = Core.get_duration(current_user['type'], self.find_by_id(id)['type'])
			self.modify(copy[0]['id'], {'deadline': (datetime.datetime.now() + timedelta).strftime('%d/%m/%Y')})
			return True
		return False

	def notify(self, user_id, message):
		"""Notify a user"""
		return self.add('notification', {'user_id': user_id, 'date': datetime.datetime.now().strftime('%d/%m/%Y'), 'message': message})

	def outstanding_request(self, doc_id, current_user):
		"""Place an outstanding request on the document"""
		if not self.check_permissions(current_user['type'], 'outstanding-request'):
			return False
		doc = self.find_by_id(doc_id)
		if not self.check_document_type(doc['type']):
			return False
		queue = self.get_queue(doc_id)
		message = 'You have been removed from the waiting list of the document with id {} because of an outstanding request'
		for request in queue:
			self.notify(request['attributes']['user_id'], message.format(doc_id))
		self.delete_queue(doc_id)
		self.log(current_user['id'], 'deleted waiting list', doc_id)
		message = 'You must immediately return your copy of the document with id {} because of an outstanding request'
		copies = self.find('copy', {'origin_id': doc_id})
		for copy in copies:
			if not self.check_available_copy(copy):
				self.notify(copy['attributes']['user_id'], message.format(doc_id))
				self.modify(copy['id'], {'deadline': datetime.datetime.now().strftime('%d/%m/%Y')})
				self.log(copy['attributes']['user_id'], 'was notified to return', doc_id)
		self.add('outstanding-request', {'target_id': doc_id})
		return True

	def delete_outstanding_request(self, doc_id):
		"""Delete an outstanding request"""
		request = self.find('outstanding-request', {'target_id': doc_id})
		if request:
			request = request[0]
		else:
			return False
		return self.delete(request['id'])

	def placed_outstanding_request(self, doc_id):
		"""Check if an outstanding request is placed on the document"""
		return self.find('outstanding-request', {'target_id': doc_id}) != []

	def get_sorted_logs(self):
		"""Returnes sorted list of all logs"""
		return list(reversed((sorted(self.find('log', {}), key = lambda x: datetime.datetime.strptime(x['attributes']['time'], '[%d/%m/%y-%H:%M:%S]')))))

	@staticmethod
	def sort_notifications(notifications):
		"""Sort notification in chronological order"""
		return list(reversed(sorted(notifications, key = lambda x: datetime.datetime.strptime(x['attributes']['date'], '%d/%m/%Y'))))

	def get_notifications(self, user_id):
		"""Get all notifications for current user"""
		return Core.sort_notifications(self.find('notification', {'user_id': user_id}))

	def get_all_notifications(self):
		"""Get all notifications for all users"""
		return Core.sort_notifications(self.find('notification', {}))

	def delete_all_notifications(self):
		"""Delete all notifications for all users"""
		notifications = self.get_all_notifications()
		for notification in notifications:
			self.delete(notification['id'])

	def delete_all_logs(self):
		"""Deletes all logs"""
		self.db.delete_many({"type": "log"})

	def normalize_request_list(self):
		"""Normalize request list (delete old requests and notify users)"""
		date = datetime.datetime.now().strftime('%d/%m/%Y')
		print("request list", self.request_list)
		if date != self.request_list['last_modified']:
			temp_list = []
			self.request_list['last_modified'] = date
			for r in self.request_list['requests']:
				doc_id = r['attributes']['target_id']
				queue = self.get_queue(doc_id)
				if queue:
					new_request = queue[0]
					temp_list.append(new_request)
					user_id = new_request['attributes']['user_id']
					message = 'You can check out an available copy of the document with id {}'
					self.notify(user_id, message.format(doc_id))
				message = 'Your request of the document with id {} was deleted because you haven\'t checked it out'
				self.notify(r['attributes']['user_id'], message.format(doc_id))
				self.delete(r['id'])
				self.notify_queue(doc_id)
			self.request_list['requests'] = temp_list

	def append_request_list(self, request):
		"""Add new request in request list"""
		self.normalize_request_list()
		self.request_list['requests'].append(request)

	def notify_queue(self, doc_id):
		"""Notify all users in the queue about how long they should wait for a document"""
		queue = self.get_queue(doc_id)
		message = 'You will be able to check out a document with id ' + str(doc_id) + ' in {} days'
		for i in range(len(queue)):
			self.notify(queue[i]['attributes']['user_id'], message.format(14 * (i + 1)))

	def check_out(self, doc_id, user_id):
		"""Checkout document"""
		if any([i['attributes']['origin_id'] == doc_id and i['attributes']['user_id'] == user_id for i in self.find('copy', {})]):
			return False
		found = [i for i in self.find('copy', {}) if i['attributes']['origin_id'] == doc_id and i['attributes']['user_id'] is None]
		if not found:
			return False
		if self.placed_outstanding_request(doc_id):
			return False
		item = found[0]
		user = self.find_by_id(user_id)
		doc = self.db.get_by_id(doc_id)
		item['attributes']['user_id'] = user_id
		timedelta = Core.get_duration(user['type'], doc['type'])
		item['attributes']['deadline'] = (datetime.datetime.now() + timedelta).strftime('%d/%m/%Y')
		self.modify(item['id'], item['attributes'])
		return True

	def give_back(self, copy_id):
		"""Return document"""
		item = self.find_by_id(copy_id)
		if not item:
			return None
		else:
			self.modify(item['id'], {'user_id': None, 'deadline': ''})
			doc = self.find_by_id(item['attributes']['origin_id'])
			queue = self.get_queue(doc['id'])
			if queue:
				request = queue[0]
				user_id = request['attributes']['user_id']
				message = 'You can check out an available copy of the document with id {}'
				self.notify(user_id, message.format(doc['id']))
				self.append_request_list(request)
			return True

	def check_copies(self, id, attributes):
		"""Get all copies all books or all copies of one book"""
		if id == '':
			return self.find('copy', {})
		else:
			return [i for i in self.find('copy', {}) if i['attributes']['origin_id'] == id]

	def drop(self, id, attributes):
		"""Clear database"""
		self.db.drop()
		self.id = 0
		self.permissions = []
		self.login('', '')
		return True

	def init_admin(self, password):
		"""Initialize admin"""
		self.admin = self.find('admin', {})
		if self.admin:
			self.admin = self.admin[0]
		else:
			self.register('admin', {'login': 'admin', 'password': password})
			self.admin = self.find('admin', {})[0]

	def init_db(self, mode):
		"""Initialize database"""
		if mode:
			from mongo_database import DataBase
		else:
			from database import DataBase
		self.db = DataBase()

	def init_map(self):
		"""Initialize map"""
		self.map = {
			'insert': self.insert,
			'register': self.register,
			'find': self.find,
			'delete': self.delete,
			'modify': self.modify,
			'checkout': self.check_out,
			'return': self.give_back,
			'copy': self.add_copy,
			'drop': self.drop,
			'check': self.check_copies,
			'approve': self.approve_cmd,
			'decline': self.decline_cmd,
			'checkout-request': self.request_check_out_cmd
		}

	def init_users(self):
		"""Initialize users"""
		self.users = json.loads(open('users.json').read())

	def init_documents(self):
		"""Initialize documents"""
		self.documents = json.loads(open('documents.json').read())

	def init_id(self):
		"""Initialize id"""
		self.id = self.db.get_max_id() + 1

	def get_permissions(self, user):
		"""Get permissions of current type of user"""
		return [i for i in self.users if i['type'] == user['type']][0]['permissions']

	def execute(self, current_user, cmd: Command):
		"""Execute the command"""
		if current_user is None:
			return "User is not logged in"
		if self.check_permissions(current_user['type'], cmd.cmd()):
			return self.map[cmd.cmd()](cmd.target(), cmd.attributes())
		else:
			if cmd.cmd() not in self.map.keys():
				return "Command not found"
			else:
				return "The current user doesn't have a permission to execute this command"

	def __init__(self, mode):
		"""Initialize class"""
		self.init_db(mode)
		self.init_map()
		self.init_users()
		self.init_documents()
		self.init_id()
		self.init_admin('')
		self.permissions = []
