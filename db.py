import pymongo
import os
import pickle
from uuid import uuid1

MONGO_URL = os.environ["MONGO_URL"]
client = pymongo.MongoClient(MONGO_URL)
database = client["mydatabase"]
conversation_collection = database["conversations"]


def parse_input(messages):
    """Pickle python objects."""
    updated_messages = []
    for message in messages:
        if type(message) is not dict:
            updated_messages.append(pickle.dumps(message))
        else:
            updated_messages.append(message)
    return updated_messages


def parse_output(messages):
    """Unpickle python objects."""
    updated_messages = []
    for message in messages:
        if type(message) is not dict:
            updated_messages.append(pickle.loads(message))
        else:
            updated_messages.append(message)
    return updated_messages


def get_conversation(conversation_id):
    conversation = conversation_collection.find_one({"conversation_id": conversation_id})
    if conversation:
        conversation["messages"] = parse_output(conversation["messages"])
    return conversation


def create_conversation(messages):
    messages = parse_input(messages)
    conversation_id = str(uuid1())
    conversation_collection.insert_one({"conversation_id": conversation_id , "messages": messages})
    return conversation_id


def update_conversation(conversation_id, messages):
    messages = parse_input(messages)
    return conversation_collection.update_one(
        {"conversation_id": conversation_id}, {"$set": {"messages": messages}}
    )
