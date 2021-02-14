from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb_serialization import SerializationMiddleware
from tinydb_serialization.serializers import DateTimeSerializer

import os
from Config import Config

#a wrapper around tinydb that handles datetime objects
class _FfJsonDb(TinyDB):
    def __init__(self):
        serialization = SerializationMiddleware(JSONStorage)
        serialization.register_serializer(DateTimeSerializer(), 'TinyDate')
        dbFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), Config['DEFAULT']['LOCAL_DB_NAME'])
        super().__init__(dbFile, storage=serialization)

FfJsonDb = _FfJsonDb()
