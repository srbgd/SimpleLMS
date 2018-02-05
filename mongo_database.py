from pymongo import MongoClient
import pymongo


class DataBase:

	client = None
	db = None
	shelf = None

	def __init__(self):
		self.client = MongoClient("mongodb://reshreshus:1JohnBardeen@ds040898.mlab.com:40898/dbslms")
		self.db = self.client.dbslms
		self.shelf = self.db.shelf
		# self.indexing()

	def indexing(self):
		self.shelf.create_index([('id', pymongo.ASCENDING)], unique=True)
		self.shelf.insert_one({"type": "librarian", "attributes": {"login": "login", "password": "pass"}, "id": 0})

	def add(self, item):
		self.shelf.insert_one(item)

	def lookup(self, type, attributes):
		"""Find item in database"""
		if type is not "":
			found = list(self.shelf.find({"type": type}))
			return [i for i in found if set(attributes.keys()).issubset(
				set(i['attributes'].keys())) and all(v == i['attributes'][k] for k, v in attributes.items())]
		else:
			found = list(self.shelf.find())
			return [i for i in found if set(attributes.keys()).issubset(
				set(i['attributes'].keys())) and all(v == i['attributes'][k] for k, v in attributes.items())]

	def delete(self, id):
		self.shelf.delete_many({"id": id})

	def modify(self, id, attributes):
		self.shelf.update_many({"id": id},
							{"$set": attributes},
							{"$currentDate": {"lastModified": True}})

	def get_max_id(self):
		# print(self.shelf.find().sort("user_id", 1).limit(1))
		# print(self.shelf.find().sort("id", -1).limit(1).next()["id"])
		return self.shelf.find().sort("id", -1).limit(1).next()["id"]
		# return max(i['id'] for i in self.db) if self.db else -1