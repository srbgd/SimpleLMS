from command import Command
import datetime
import json


class Core:
	"""Core class"""

	current_user = None
	"""Current user"""
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

	def add(self, target, attributes):
		"""Add new item to database"""
		self.db.add({
			'id': self.id,
			'type': target,
			'attributes': attributes
		})
		self.id += 1
		return self.id - 1

	def register(self, target, attributes):  # interchanged and added default
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
		if self.check_document_type(type) or self.check_user_type(type) or type in ['', 'copy', 'request', 'renew', 'notification', 'outstanding-request']:
			return self.db.lookup(type, attributes)
		else:
			return None

	def search(self, string):
		pass

	@staticmethod
	def check_available_copy(copy):
		return copy['attributes']['user_id'] is None

	@staticmethod
	def get_overdue(item):
		if not Core.check_available_copy(item):
			return (datetime.datetime.now() - datetime.datetime.strptime(item['attributes']['deadline'], '%d/%m/%Y')).days
		else:
			return None

	def get_fine(self, item):
		overdue = Core.get_overdue(item)
		if overdue is None or overdue <= 0:
			return 0
		price = int(self.find_by_id(int(item['attributes']['origin_id']))['attributes']['price'])
		return min(overdue * 100, price)

	def check_overdue(self, i):
		overdue = self.get_overdue(i)
		if overdue is None or overdue <= 0:
			return False
		else:
			return True

	def check_fine(self, i):
		if self.get_fine(i):
			return True
		else:
			return False

	def get_overdue_by_id(self, copy_id):
		item = self.find_by_id(copy_id)
		if item['type'] != 'copy':
			return None
		return Core.get_overdue(item)

	def get_fine_by_id(self, copy_id):
		item = self.find_by_id(copy_id)
		if item['type'] != 'copy':
			return None
		return self.get_fine(item)

	def get_all_users_with_overdue(self):
		users = set()
		copies = self.find('copy', dict())
		for i in copies:
			if self.check_overdue(i):
				users.add(i['attributes']['user_id'])
		if users:
			users = self.courteous_find({"$or": [{"id": i} for i in users]})
		return list(users)

	def get_all_unconfirmed_users(self):
		return list(self.db.courteous_lookup({"type": "unconfirmed"}))

	def delete_available_copies(self, doc_id):
		copies = self.find('copy', {'origin_id': doc_id})
		for i in copies:
			if self.check_available_copy(i):
				self.delete(i['id'])

	def delete_book(self, doc_id):
		copies = self.find('copy', {'origin_id': doc_id})
		if all(self.check_available_copy(i) for i in copies):
			self.delete_available_copies(doc_id)
			self.delete_all_requests(doc_id)
			self.delete(doc_id)
			return True
		else:
			return False

	def delete_all_requests(self, doc_id):
		requests = [i for i in self.find('request', {}) if i['attributes']['target_id'] == doc_id]
		for i in requests:
			self.delete(i['id'])

	def add_document_with_copies(self, target, attributes, n):
		id = self.add(target, attributes)
		for i in range(n):
			self.add_copy(id)

	def get_all_checked_out_documents(self):
		documents = set()
		copies = self.find('copy', dict())
		for i in copies:
			if not self.check_available_copy(i):
				documents.add(i['attributes']['origin_id'])
		if documents:
			documents = self.courteous_find({"$or": [{"id": i} for i in documents]})
		return list(documents)

	def courteous_find(self, attributes):
		return self.db.courteous_lookup(attributes)

	def find_all_documents(self):
		return self.courteous_find({"$or":[{'type': i['type']} for i in self.documents]})

	def find_all_users(self):
		return self.courteous_find({"$or":[{'type': i['type']} for i in self.users]})

	def find_by_id(self, id):
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
			self.current_user = None
			self.normalize_request_list()
			return True
		if login == password == '':
			for i in self.users:
				for j in i['permissions']:
					if j not in self.permissions:
						self.permissions.append(j)
			self.normalize_request_list()
			return True
		user = self.db.lookup('', {'login': login, 'password': password})
		if user:
			self.current_user = user[0]
			self.permissions = self.get_permissions(user[0])
			self.normalize_request_list()
			return True
		else:
			return False

	def add_copy(self, id, attributes = None):
		"""Add copy to database"""
		document = self.db.get_by_id(id)
		if self.check_document_type(document['type']) and 'reference-book' != document['type']:
			self.add('copy', {'origin_id': id, 'user_id': None, 'deadline': ''})
			return True
		else:
			return False

	def request(self, doc_id, action):
		if action not in ['check-out', 'return']:
			return False
		type, attributes = 'request', {'user_id': self.current_user['id'], 'target_id': doc_id, 'action': action}
		if self.find(type, attributes):
			return False
		else:
			self.add(type, attributes)
			return True

	def approve_cmd(self, id, attributes = None):
		request = self.find_by_id(id)
		action = request['attributes']['action']
		return self.approve(id, action)

	def decline_cmd(self, id, attributes = None):
		request = self.find_by_id(id)
		action = request['attributes']['action']
		return self.decline(id, action)

	def approve(self, request_id, action):
		request = self.find_by_id(request_id)
		if request['type'] != 'request':
			return False
		elif request['attributes']['action'] != action:
			return False
		elif self.current_user['type'] != 'librarian':
			return False
		else:
			self.delete(request_id)
			if action == 'check-out':
				return self.check_out(request['attributes']['target_id'], request['attributes']['user_id'])
			if action == 'return':
				return self.give_back(request['attributes']['target_id'])
			return False

	def decline(self, request_id, action):
		request = self.find_by_id(request_id)
		if request['type'] != 'request':
			return False
		elif request['attributes']['action'] != action:
			return False
		elif self.current_user['type'] != 'librarian':
			return False
		else:
			return self.delete(request_id)

	def delete_queue(self, doc_id):
		queue = self.get_queue(doc_id)
		for i in queue:
			self.delete(i['id'])

	def can_renew(self, id):
		if self.find('renew', {'user_id': self.current_user['id'], 'origin_id': id}):
			return False
		copy = self.find('copy', {'user_id': self.current_user['id'], 'origin_id': id})
		if copy:
			copy = copy[0]
		else:
			return False
		return not self.check_overdue(id)

	def request_check_out(self, doc_id):
		return self.request(doc_id, 'check-out')

	def approve_check_out(self, request_id):
		return self.approve(request_id, 'check-out')

	def decline_check_out(self, request_id):
		return self.decline(request_id, 'check-out')

	def request_return(self, doc_id):
		return self.request(doc_id, 'return')

	def approve_return(self, request_id):
		return self.approve(request_id, 'return')

	def decline_return(self, request_id):
		return self.decline(request_id, 'return')

	def get_queue(self, id):
		priority = ['student', 'faculty', 'visiting-professor']
		return sorted(self.find('request', {'target_id': id, 'action': 'check-out'}), key=lambda x: priority.index(self.find_by_id(x['attributes']['user_id'])['type']))

	@staticmethod
	def get_duration(user_type, doc_type):
		duration = 21
		if user_type == 'visiting-professor':
			duration = 7
		if user_type == 'faculty':
			duration = 28
		elif doc_type == 'best_seller':
			duration = 14
		return datetime.timedelta(days=duration)

	def renew(self, id, attributes=None):
		id = int(id)
		copy = self.find('copy', {'user_id': self.current_user['id'], 'origin_id': id})
		if copy and not self.find('renew', {'user_id': self.current_user['id'], 'origin_id': id}):
			if self.current_user['type'] != 'visiting-professor':
				self.add('renew', {'user_id': self.current_user['id'], 'origin_id': id})
			timedelta = Core.get_duration(self.current_user['type'], self.find_by_id(id)['type'])
			self.modify(copy[0]['id'], {'deadline': (datetime.datetime.now() + timedelta).strftime('%d/%m/%Y')})
			return True
		return False

	def notify(self, user_id, message):
		return self.add('notification', {'user_id': user_id, 'date': datetime.datetime.now().strftime('%d/%m/%Y'), 'message': message})

	def outstanding_request(self, doc_id):
		if self.current_user['type'] != 'librarian':
			return False
		doc = self.find_by_id(doc_id)
		if not self.check_document_type(doc['type']):
			return False
		queue = self.get_queue(doc_id)
		message = 'You cannot check out a document with id {} because of an outstanding request'
		for request in queue:
			self.notify(request['attributes']['user_id'], message.format(doc_id))
		self.delete_queue(doc_id)
		message = 'You must immediately return your copy of the document with id {} because of an outstanding request'
		copies = self.find('copy', {'origin_id': doc_id})
		for copy in copies:
			if not self.check_available_copy(copy):
				self.notify(copy['attributes']['user_id'], message.format(doc_id))
				self.modify(copy['id'], {'deadline': datetime.datetime.now().strftime('%d/%m/%Y')})
		self.add('outstanding-request', {'target_id': doc_id})
		return True

	def delete_outstanding_request(self, doc_id):
		request = self.find('outstanding-request', {'target_id': doc_id})
		if request:
			request = request[0]
		else:
			return False
		return self.delete(request['id'])

	def placed_outstanding_request(self, doc_id):
		return self.find('outstanding-request', {'target_id': doc_id}) != []

	@staticmethod
	def sort_notifications(notifications):
		return list(reversed(sorted(notifications, key = lambda x: datetime.datetime.strptime(x['attributes']['date'], '%d/%m/%Y'))))

	def get_notifications(self, user_id):
		return Core.sort_notifications(self.find('notification', {'user_id': user_id}))

	def get_all_notifications(self):
		return Core.sort_notifications(self.find('notification', {}))

	def delete_all_notifications(self):
		notifications = self.get_all_notifications()
		for notification in notifications:
			self.delete(notification['id'])

	def normalize_request_list(self):
		date = datetime.datetime.now().strftime('%d/%m/%Y')
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
			self.request_list['requests'] = temp_list

	def append_request_list(self, request):
		self.normalize_request_list()
		self.request_list['requests'].append(request)

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
			if not queue:
				request = queue[0]
				user_id = request['attributes']['user_id']
				message = 'You can check out an available copy of the document with id {}'
				self.notify(user_id, message.format(doc['id']))
				self.append_request_list(request)
			return True

	def check_copies(self, id, attributes):
		if id == '':
			return self.find('copy', {})
		else:
			return [i for i in self.find('copy', {}) if i['attributes']['origin_id'] == id]

	def drop(self, id, attributes):
		"""Clear database"""
		self.db.drop()
		self.current_user = None
		self.id = 0
		self.permissions = []
		self.login('', '')
		return True

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
			'decline': self.decline_cmd
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

	def execute(self, cmd: Command):
		"""Execute the command"""
		if cmd.cmd() in self.permissions:
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
		self.permissions = []
