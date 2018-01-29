import datebase

class Core:

	user = None
	db = datebase.Database

	def login(self, login, password):
		if self.db.check_user(login, password):
			user = User(login, password)
			return 0
		else:
			return 1

	def init_db(self):
		pass

	def __init__(self):
		self.init_db()