from pymongo import MongoClient
import pymongo
"""
This file is not part of a project. I will delete it later.
"""
import datetime
import pprint

# client = MongoClient("mongodb://reshreshus:1JohnBardeen@ds040898.mlab.com:40898/dbslms")
# client.drop_database("db")

client = MongoClient()
db = client.dbslms
shelf = db.shelf
shelf.delete_many({})
shelf.insert_one({"type": "librarian", "attributes": {"login": "login", "password": "pass"}, "id": 0})
print(shelf.find_one({"id":0}))

print(type(shelf.find_one({"id":3})))
for post in shelf.find_one({"id":3}):
    print(type(post))
# shelf.create_index([('user_id', pymongo.ASCENDING)], unique=True)
# post_id = shelf.insert_one({"hell":"yeah"})
# print(db.collection_names(include_system_collections=False))

# pprint.pprint(shelf.find_one())

# new_posts = [{"author": "Mike",
#                "text": "and",
#                "tags": ["bulk", "insert"],
#                "date": datetime.datetime(2009, 11, 12, 11, 14)},
#               {"author": "Eliot",
#                "title": "MongoDB",
#                "text": "and",
#                "date": datetime.datetime(2009, 11, 10, 10, 45)},
#              {"attributes":{"name":"loh","pass":"pas"}},
#              {"attributes": {"name": "loh", "pass": "pepsy"}}]
# result = shelf.insert_many(new_posts)
# # print(result.inserted_ids)
# attributes = {"name":"loh"}
#

# for post in shelf.find({"text": "and"}):
#     print(post)
    # pprint.pprint(post)
