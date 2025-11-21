# src/core/db_client.py
from pymongo import MongoClient
from .config import MONGO_URI, DB_NAME

class DBClient:
    def __init__(self, uri=MONGO_URI, dbname=DB_NAME):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[dbname]

    def ping(self):
        return self.client.admin.command("ping")

    def list_collections(self):
        return self.db.list_collection_names()

    def find_docs(self, coll, filt=None, limit=200):
        return list(self.db[coll].find(filt or {}).limit(limit))

    def insert_doc(self, coll, doc):
        return self.db[coll].insert_one(doc)

    def delete_doc(self, coll, ident):
        return self.db[coll].delete_one({"_id": ident})

    def update_doc(self, coll, ident, update):
        return self.db[coll].update_one({"_id": ident}, {"$set": update})
