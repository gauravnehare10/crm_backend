from bson import ObjectId

def fetch_all_items(cursor):
    items = list(cursor)
    for item in items:
        item["id"] = str(item["_id"])
    return items

def serialize_mongo_document(document):
    if isinstance(document, list):
        return [serialize_mongo_document(doc) for doc in document]
    if isinstance(document, dict):
        document["id"] = str(document["_id"]) if "_id" in document else None
        del document["_id"]
        return {key: (str(value) if isinstance(value, ObjectId) else serialize_mongo_document(value)) for key, value in document.items()}
    return document


def serialize_document(document):
    if isinstance(document, ObjectId):
        return str(document)
    elif isinstance(document, list):
        return [serialize_document(item) for item in document]
    elif isinstance(document, dict):
        return {key: serialize_document(value) for key, value in document.items()}
    else:
        return document