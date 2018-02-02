from pymongo import MongoClient


class DateBase:
	client = MongoClient()
	db = client.db
	shelf = db.shelf

	def __init__(self, port=None):
		if port is not None:
			client = MongoClient(port)
			db = client.db
			shelf = db.shelf

	def add(self, item):
		self.shelf.insert_one(item)

	def lookup(self, attributes):
		return self.shelf.find(attributes)

	def delete(self, id):
		self.shelf.delete_many({"id" : id})

	def modify(self, id, attributes):
		self.shelf.update_many({"id":id},
							{"$set": attributes},
							{"$currentDate": {"lastModified": True}})