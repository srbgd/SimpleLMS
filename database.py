import os
import json


class DataBase:
	"""
	Database class
	"""

	db = []
	"""List if items"""
	file = 'db.json'
	"""Name of database class"""

	def __init__(self):
		"""Initialize database"""
		if os.path.isfile(self.file):
			s = open(self.file).read()
			if s != '':
				self.db = json.loads(s)

	def update(self):
		"""Update json file"""
		json.dump(self.db, open(self.file, 'w'))

	def add(self, item):
		"""Add new iten to database"""
		self.db.append(item)
		self.update()

	def lookup(self, type, attributes):
		"""Find item in database"""
		return [i for i in self.db if type == i['type'] or type == '' and set(attributes.keys()).issubset(set(i['attributes'].keys())) and all(v == i['attributes'][k] for k, v in attributes.items())]

	def delete(self, id):
		"""Delete item from database"""
		size = len(self.db)
		self.db = [item for item in self.db if item['id'] != id]
		self.update()
		if len(self.db) != size:
			return True
		else:
			return False

	def modify(self, id, attributes):
		"""Modify item in database"""
		for i in self.db:
			if i['id'] == id:
				for key, value in attributes.items():
					i['attributes'][key] = value
				self.update()
				return True
		return False

	def get_by_id(self, id):
		return [i for i in self.db if i['id'] == id][0]

	def get_max_id(self):
		"""Get tne maximum id in database"""
		return max(i['id'] for i in self.db) if self.db else -1
