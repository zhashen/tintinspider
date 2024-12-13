import pymongo

class MongodbObject:
    
    def __init__(self, mongodb_config):
        self.mongodb_config = mongodb_config
        self.client = pymongo.MongoClient(mongodb_config['server'])
        self._db = self.client[mongodb_config['database']]
    
    @property
    def db(self):
        return self._db
    
    def coll_sites(self):
        return self._db[self.mongodb_config['coll_sites']]
    
    def coll_iurls(self):
        return self._db[self.mongodb_config['coll_iurls']]
    
    def coll_curls(self):
        return self._db[self.mongodb_config['coll_curls']]
    
    def coll_items(self):
        return self._db[self.mongodb_config['coll_items']]
    