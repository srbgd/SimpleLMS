from database import DataBase

from command import Command
import json


class Core:

	permissions = []
	documents = None
	users = None
	map = None
	db = None
	id = 0

	def add(self, target, attributes):
		self.db.add({
			'id': self.id,
			'type': target,
			'attributes': attributes
		})
		self.id += 1

	def register(self, target, attributes):
		if self.check_user(target, attributes):
			self.add(target, attributes)
			return True
		else:
			return False

	def insert(self, type, attributes):
		print(type)
		print(attributes)
		if self.check_document(type, attributes):
			self.add(type, attributes)
			return True
		else:
			return False

	def find(self, type, attributes):
		if self.check_document_type(type) or self.check_user_type(type):
			return self.db.lookup(type, attributes)
		else:
			return None

	def delete(self, id, attributes):
		if attributes != dict():
			return None
		else:
			return self.db.delete(int(id))

	def modify(self, id, attributes):
		return self.db.modify(int(id), attributes)

	def check_document(self, type, attributes):
		return self.check_document_type(type) and self.check_attributes(type, attributes)

	def check_attributes_soundness(self, type, attributes):
		return all(i in [j for j in self.documents if j['type'] == type][0]['attributes'] for i in attributes.keys())

	def check_attributes_completeness(self, type, attributes):
		return all(i in attributes.keys() for i in [j for j in self.documents if j['type'] == type][0]['attributes'])

	def check_attributes(self, type, attributes):
		return self.check_attributes_soundness(type, attributes) and self.check_attributes_completeness(type, attributes)

	def check_document_type(self, type):
		return any(i['type'] == type for i in self.documents)

	def check_user(self, type, attributes):
		return self.check_user_type(type) and self.check_user_attributes(type, attributes)

	def check_user_attributes(self, type, attributes):
		return sorted([i for i in self.users if i['type'] == type][0]['attributes']) == sorted(list(attributes.keys()))

	def check_user_type(self, type):
		return any(i['type'] == type for i in self.users)

	def login(self, login, password):
		if login == password == '':
			for i in self.users:
				for j in i['permissions']:
					if j not in self.permissions:
						self.permissions.append(j)
			return True
		user = self.db.lookup('', {'login': login, 'password': password})
		if user:
			self.permissions = self.get_permissions(user[0])
			return True
		else:
			return False

	def init_db(self):
		self.db = DataBase("file")

	def init_map(self):
		self.map = {
			'insert': self.insert,
			'register': self.register,
			'find': self.find,
			'delete': self.delete,
			'modify': self.modify
		}

	def init_users(self):
		self.users = json.loads(open('users.json').read())

	def init_documents(self):
		self.documents = json.loads(open('documents.json').read())

	def init_id(self):
		self.id = self.db.get_max_id() + 1

	def get_permissions(self, user):
		return [i for i in self.users if i['type'] == user['type']][0]['permissions']

	def execute(self, cmd: Command):
		if cmd.cmd() in self.permissions:
			return self.map[cmd.cmd()](cmd.target(), cmd.attributes())
		else:
			return "The current user doesn't have a permission to execute this command"

	def __init__(self):
		self.init_db()
		self.init_map()
		self.init_users()
		self.init_documents()
		self.init_id()
		self.permissions = []
