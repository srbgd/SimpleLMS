from mongo_database import DataBase
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

	def add(self, target, attributes): #RISHAT
		"""Add new item to database"""
		self.db.add({
			'id': self.id,
			'type': target,
			'attributes': attributes
		})
		self.id += 1
		return self.id - 1 #HERE

	# def gentle_add(self, new_document):
	# 	self.db.add(new_document)

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

	def search(self, string):  # RISHAT TODO SERGEY GET LIST OF DOCUEMETNS
		pass

	def courteous_find(self, attributes):  # RISHAT
		return self.db.courteous_lookup(attributes)

	def find_all_documets(self):  # RISHAT
		return self.courteous_find({"$or":[{"type": "book"}, {"type": "reference_book"}, {"type": "journal_article"}, {"type": "audio_video"}, {"type": "best_seller"}]})

	def find_by_id(self, some_id):  # RISHAT
		return self.db.get_by_id(some_id)

	def delete(self, some_id, attributes):
		"""Delete item from database"""
		if attributes != dict():
			return None
		else:
			return self.db.delete(some_id) #RISHAT CHANGED int(id) to id

	def modify(self, some_id, attributes, new_type = None):  # RISHAT
		"""Modify item in database"""
		old_attributes = self.find_by_id(some_id)['attributes']
		for item, value in attributes.items():
			old_attributes[item] = value
		if new_type:
			return self.db.modify_and_change_type(some_id, attributes=old_attributes, type=new_type)
		return self.db.modify(some_id, old_attributes) #RISHAT CHANGED int(id) to id

	def modify_current_user(self, some_id, attributes):  # RISHAT
		for item, value in attributes.items():
			self.current_user['attributes'][item] = value
		self.db.modify(some_id, self.current_user['attributes']) #RISHAT CHANGED int(id) to id

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

	def login(self, login=None, password=None):
		if login is password is None:
			self.current_user = None
			return True
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
			# raise Exception("yeah")
			self.permissions = self.get_permissions(user[0])
			return True
		else:
			return False

	def add_copy(self, some_id, attributes):
		"""Add copy to database"""
		document = self.db.get_by_id(some_id) #RISHAT CHANGED int(id) to id
		if self.check_document_type(document['type']) and 'reference-book' != document['type']:
			self.add('copy', {'origin_id': some_id, 'user_id': None, 'deadline': ''})
			return True
		else:
			return False

	def check_out(self, some_id, attributes):
		"""Checkout document"""
		if attributes != dict():
			return None
		if any([i['attributes']['origin_id'] == some_id and i['attributes']['user_id'] == self.current_user['id'] for i in self.find('copy', {})]):
			# print("второе")
			return False
		found = [i for i in self.find('copy', {}) if i['attributes']['origin_id'] == some_id and i['attributes']['user_id'] is None]
		if not found:
			# print('not found')
			return False
		else:
			item = found[0]
			item['attributes']['user_id'] = self.current_user['id']
			# print(self.current_user['id'])
			if self.current_user['type'] == 'faculty':
				duration = 28
			elif self.db.get_by_id(some_id)['type'] == 'best-seller': #RISHAT CHANGED int(id) to id
				duration = 14
			else:
				duration = 21
			item['attributes']['deadline'] = (datetime.datetime.now() + datetime.timedelta(days = duration)).strftime('%d/%m/%Y')
			self.modify(item['id'], item['attributes'])
			print(str(item))
			return True


	def give_back(self, copy_id, attributes):  # RISHAT: 'give_back' didn't do anything in database
		"""Return document"""
		if attributes != dict():
			return None
		# found = [i for i in self.find('copy', {}) if i['attributes']['origin_id'] == id and i['attributes']['user_id'] == self.current_user['id']]
		found = [self.find_by_id(copy_id)] # RISHAT - LIBRARIAN SHOULD GET RETURNS, i.e. IT IS HIS WORK TO DO RETURNS
		# print('found', found)
		if not found:
			return False
		else:
			item = found[0]
			overdue = (datetime.datetime.now() - datetime.datetime.strptime(item['attributes']['deadline'], '%d/%m/%Y')).days
			# fines = max(0, min(int(self.db.get_by_id(item['attributes']['price'])), overdue * 100)) #RISHAT
			fines = max(0, min(self.db.get_by_id(item['attributes']['origin_id'])['attributes']['price'], overdue * 100)) #RISHAT
			self.modify(item['id'], {'origin_id': item['attributes']['origin_id'], 'user_id': None, 'deadline': ''}) #RISHAT
			if fines != 0:
				return "You have to pay {} RUB".format(fines)
			else:
				return True

	def check_copies(self, some_id, attributes):
		if some_id == '':
			return self.find('copy', {})
		else:
			return [i for i in self.find('copy', {}) if i['attributes']['origin_id'] == some_id]

	def drop(self, some_id, attributes):
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
