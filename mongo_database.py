from pymongo import MongoClient
import pymongo
import config


class DataBase:

	client = None
	db = None
	shelf = None

	def __init__(self):
		"""Initialize database"""
		self.client = MongoClient(config.mongodb_link)
		self.db = self.client.dbslms
		self.shelf = self.db.shelf
		# self.indexing()

	def drop(self):
		"""delete all documents from database"""
		self.shelf.delete_many({})

	def indexing(self):
		"""Initial indexing"""
		self.shelf.create_index([('id', pymongo.ASCENDING)], unique=True)
		self.shelf.insert_one({"type": "librarian", "attributes": {"login": "login", "password": "pass"}, "id": 0})

	def add(self, item):
		"""Add new iten to database"""
		self.shelf.insert_one(item)

	def lookup(self, type, attributes):
		"""Find item in database"""
		if type is not "":
			found = list(self.shelf.find({"type": type}, {"_id":False}))
			return [i for i in found if set(attributes.keys()).issubset(
				set(i['attributes'].keys())) and all(v == i['attributes'][k] for k, v in attributes.items())]
		else:
			found = list(self.shelf.find({}, {"_id":False}))
			return [i for i in found if set(attributes.keys()).issubset(
				set(i['attributes'].keys())) and all(v == i['attributes'][k] for k, v in attributes.items())]

	def courteous_lookup(self, attributes):
		return list(self.shelf.find(attributes))

	def delete(self, some_id):
		"""Delete item from database"""
		return self.shelf.delete_many({"id": some_id}).deleted_count != 0

	def delete_many(self, items):
		self.shelf.delete_many(items)

	def delete_one(self, items):
		self.shelf.delete_one(items)

	def modify_and_change_type(self, some_id, attributes, type):
		self.shelf.update_one({"id":some_id}, {
			"$set": {"attributes":attributes, "type":type}
		})

	def modify(self, some_id, attributes):
		"""Modify item in database"""
		self.shelf.update_one({"id": some_id},
							  {"$set": {"attributes": attributes}}
							  # "$currentDate": {"lastModified": True}}
							  )

	def get_max_id(self):
		"""Get tne maximum id in database"""
		# return self.shelf.find().sort("id", -1).limit(1).next()["id"]
		return list(self.shelf.find().sort("id", -1).limit(1))[0]["id"]

	def get_by_id(self, some_id):
		"""Get a document with given id"""
		found = list(self.shelf.find({"id": some_id}))
		# print(found)
		return found[0] if found else {}
