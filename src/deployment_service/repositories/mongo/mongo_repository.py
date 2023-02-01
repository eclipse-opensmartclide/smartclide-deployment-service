import urllib.parse
from pymongo import MongoClient
from deployment_service.config.settings import Settings

class MongoRepo:
    def __init__(self, collection_name='deployment_component', page_size=50 )-> None:
        settings = Settings()
        self.host = settings.repositories['mongo']['host']
        self.port = int(settings.repositories['mongo']['port'])
        self.user = urllib.parse.quote_plus(settings.repositories['mongo']['user'])
        self.password = urllib.parse.quote_plus(settings.repositories['mongo']['password'])
        self.database = settings.repositories['mongo']['database']
        db = self.__get_mongo_client()
        self.deployments_col = db[collection_name]

    def __get_mongo_client(self):
        if self.user and self.password:
            client = MongoClient('mongodb://{}:{}@{}:{}'.format(
                self.user,
                self.password, 
                self.host, 
                self.port
            ))
        else:
            client = MongoClient(
                self.host,
                port=self.port, 
            )
        return client