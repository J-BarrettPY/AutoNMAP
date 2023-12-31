from pymongo import MongoClient

client = MongoClient('mongodb://192.168.1.244:27017/')
db = client['AUTO_NMAP']
collection = db['very_high']

pipeline = [
    {
        '$group': {
            '_id': '$URL',
            'count': {'$sum': 1},
            'ids': {'$push': '$_id'}
        }
    },
    {
        '$match': {
            'count': {'$gt': 1}
        }
    }
]

duplicates = collection.aggregate(pipeline)

for duplicate in duplicates:
    ids_to_delete = duplicate['ids'][1:]
    collection.delete_many({'_id': {'$in': ids_to_delete}})

print("Duplicates deleted successfully.")
