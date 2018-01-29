from pymongo import MongoClient
import pymongo


class Database:
	client = MongoClient()
	db = client.db
	shelf = db.shelf
	result = shelf.create_index([('id', pymongo.ASCENDING)], unique = True) #say we do id like this

	def __init__(self, port = None):
		if port is None:
			self.client = MongoClient(port)

	def get(self, match):
		if match is None:
			return self.shelf.find()
		else:
			return self.shelf.find(match)

	def get_ids(self, match):
		found = self.get_books(match)
		result = []
		for document in found:
			result.append(document['id'])
		return result

	# We can get ids of inserted documents (if we need)
	def insert_one(self, document):
		self.shelf.insert_one(document)

	def insert_many(self, documents = [{}]):
		self.shelf.insert_many(documents)

	def update_one(self, match, setting):
		self.shelf.update_one(match, {"$set": setting,
									  "$currentDate":{"lastModified": True}})

	def update_many(self, match, setting):
		self.shelf.update_many(match, {"$set": setting,
									  "$currentDate":{"lastModified": True}})

	def replace_one(self, match, replacement):
		self.shelf.replace_one(match, replacement)

	def replace_many(self, match, replacement):
		self.shelf.replace_many(match, replacement)




