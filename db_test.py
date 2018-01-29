from pymongo import MongoClient
"""
This file is not part of a project. I will delete it later.
"""
import datetime
import pprint

client = MongoClient()
db = client.db
shelf = db.shelf
post_id = shelf.insert_one({"hell":"yeah"})
# print(db.collection_names(include_system_collections=False))

# pprint.pprint(shelf.find_one())

new_posts = [{"author": "Mike",
               "text": "Another post!",
               "tags": ["bulk", "insert"],
               "date": datetime.datetime(2009, 11, 12, 11, 14)},
              {"author": "Eliot",
               "title": "MongoDB is fun",
               "text": "and pretty easy too!",
               "date": datetime.datetime(2009, 11, 10, 10, 45)}]
result = shelf.insert_many(new_posts)
# print(result.inserted_ids)
for post in shelf.find():
	pprint.pprint(post)
client.drop_database("db")