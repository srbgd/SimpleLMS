import os
import json

class DateBase:

	client = None
	db = client.db
	shelf = db.shelf

	def __init__(self):
		# if port is not None:
		# 	client = MongoClient(port)
		# 	db = client.db
		# 	shelf = db.shelf
		client = MongoClient("mongodb://iskander:aslamhamna@ds040898.mlab.com:40898/dbslms")
		pass
class DataBase:

	db = []
	file = 'db.json'

	def __init__(self):
		if os.path.isfile(self.file):
			s = open(self.file).read()
			if s != '':
				self.db = json.loads(s)

	def update(self):
		json.dump(self.db, open(self.file, 'w'))

	def add(self, item):
		self.db.append(item)
		self.update()

	def lookup(self, type, attributes):
		return [i for i in self.db if type == i['type'] or type == '' and all(v == i['attributes'][k] for k, v in attributes.items())]

	def delete(self, id):
		size = len(self.db)
		self.db = [item for item in self.db if item['id'] != id]
		self.update()
		if len(self.db) != size:
			return True
		else:
			return False

	def modify(self, id, attributes):
		for i in self.db:
			if i['id'] == id:
				for key, value in attributes.items():
					i['attributes'][key] = value
				self.update()
				return True
		return False

	def get_max_id(self):
		return max(i['id'] for i in self.db) if self.db else -1
