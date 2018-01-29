import datebase

class Core:

	user = None
	db = None

	def login(self, login, password):
		if db.check_user(login, password):
			user = User(login, password)
			return 0
		else:
			return 1

	def init_db(self):
		pass

	def __init__(self):
		init_db()