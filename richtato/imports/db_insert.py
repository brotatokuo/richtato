class RichtatoDBInsert:
    def __init__(self, db):
        self.db = db

    def insert(self, data):
        self.db.insert(data)
