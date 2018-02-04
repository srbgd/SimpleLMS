from pymongo import MongoClient


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