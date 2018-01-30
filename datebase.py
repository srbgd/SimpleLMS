import os
import json


class DateBase:

	db = None
	file = 'db.json'

	def __init__(self, file):
		self.file = file + '.json'
		if os.path.isfile(self.file):
			self.db = json.loads(open(self.file).read())
		else:
			self.db = []

	def update(self):
		json.dump(self.db, open(self.file, 'w'))

	def add(self, item):
		self.db.append(item)
		self.update()

	def lookup(self, attributes):
		return [item for item in self.db if all(value == item['attributes'][key] for key, value in attributes.items())]

	def delete(self, id):
		self.db = [item for item in self.db if item['id'] != id]
		self.update()

	def modify(self, id, attributes):
		for i in self.db:
			if i['id'] == id:
				for key, value in attributes.items():
					i['attributes'][key] = value
		self.update()
