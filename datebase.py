"""
"""
from pymongo import MongoClient


class Database:
	client = MongoClient()
	db = client.db
	shelf = db.shelf

	def __init__(self, port = None):
		if port is None:
			self.client = MongoClient(port)

	def get(self, match):
		pass
