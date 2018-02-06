from database import DataBase
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

	def add(self, target, attributes):
		"""Add new item to database"""
		self.db.add({
			'id': self.id,
			'type': target,
			'attributes': attributes
		})
		self.id += 1

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
		if self.check_document_type(type) or self.check_user_type(type) or type == '' or type == 'copy':
			return self.db.lookup(type, attributes)
		else:
			return None

	def delete(self, id, attributes):
		"""Delete item from database"""
		if attributes != dict():
			return None
		else:
			return self.db.delete(int(id))

	def modify(self, id, attributes):
		"""Modify item in database"""
		return self.db.modify(int(id), attributes)

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

	def login(self, login, password):
		"""Change current user"""
		if login == password == '':
			for i in self.users:
				for j in i['permissions']:
					if j not in self.permissions:
						self.permissions.append(j)
			return True
		user = self.db.lookup('', {'login': login, 'password': password})
		if user:
			self.current_user = user[0]
			self.permissions = self.get_permissions(user[0])
			return True
		else:
			return False

	def add_copy(self, id, attributes):
		"""Add copy to database"""
		document = self.db.get_by_id(int(id))
		if self.check_document_type(document['type']) and 'reference-book' != document['type']:
			self.add('copy', {'origin_id': id, 'user_id': None, 'deadline': ''})
			return True
		else:
			return False

	def check_out(self, id, attributes):
		"""Checkout document"""
		if attributes != dict():
			return None
		if any([i['attributes']['origin_id'] == id and i['attributes']['user_id'] == self.current_user['id'] for i in self.find('copy', {})]):
			return False
		found = [i for i in self.find('copy', {}) if i['attributes']['origin_id'] == id and i['attributes']['user_id'] is None]
		if not found:
			return False
		else:
			item = found[0]
			item['attributes']['user_id'] = self.current_user['id']
			if self.current_user['type'] == 'faculty':
				duration = 28
			elif self.db.get_by_id(int(id))['type'] == 'best-seller':
				duration = 14
			else:
				duration = 21
			item['attributes']['deadline'] = (datetime.datetime.now() + datetime.timedelta(days = duration)).strftime('%d/%m/%Y')
			return True

	def give_back(self, id, attributes):
		"""Return document"""
		if attributes != dict():
			return None
		found = [i for i in self.find('copy', {}) if i['attributes']['origin_id'] == int(id) and i['attributes']['user_id'] == self.current_user['id']]
		if not found:
			return False
		else:
			item = found[0]
			overdue = (datetime.datetime.now() - datetime.datetime.strptime(item['attributes']['deadline'], '%d/%m/%Y')).days
			fines = max(0, min(int(self.db.get_by_id(item['attributes']['price'])), overdue * 100))
			if fines != 0:
				return "You have to pay {} RUB".format(fines)
			else:
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

	def init_db(self):
		"""Initialize database"""
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
			'check': self.check_copies
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
			return "The current user doesn't have a permission to execute this command"

	def __init__(self):
		"""Initialize class"""
		self.init_db()
		self.init_map()
		self.init_users()
		self.init_documents()
		self.init_id()
		self.permissions = []
