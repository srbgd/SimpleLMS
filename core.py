from database import DateBase
from command import Command
import json


class Core:

	permissions = []
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
		if self.check_user_type(target):
			self.add(target, attributes)

	def check_user_type(self, type):
		return any(i['type'] == type for i in self.users)

	def login(self, login, password):
		if login == password == 'admin':
			for i in self.users:
				for j in i['permissions']:
					if j not in self.permissions:
						self.permissions.append(j)
			return True
		user = self.db.lookup({'login': login, 'password': password})
		if user:
			self.permissions = self.get_permissions(user[0])
			return True
		else:
			return False

	def init_db(self):
		self.db = DateBase()

	def init_map(self):
		self.map = {
			'add': self.add,
			'register': self.register
		}

	def init_users(self):
		self.users = json.loads(open('users.json').read())

	def get_permissions(self, user):
		return [i for i in self.users if i['type'] == user['type']][0]['permissions']

	def execute(self, cmd: Command):
		if cmd.cmd() in self.permissions:
			self.map[cmd.cmd()](cmd.target(), cmd.attributes())

	def __init__(self):
		self.init_db()
		self.init_map()
		self.init_users()
		self.id = 0
		self.permissions = []
