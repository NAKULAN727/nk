class MongoRouter:
    """
    Database router for directing specific models to MongoDB
    """
    
    # Models that should use MongoDB
    mongodb_models = [
        'UserLoginLog', 
        'AdminActivityLog', 
        'UserSessionInfo',
        'SensorData'
    ]
    
    def db_for_read(self, model, **hints):
        """
        Attempts to read mongodb models go to mongodb database.
        """
        if model._meta.model_name in self.mongodb_models or getattr(model, 'mongodb_model', False):
            return 'mongodb'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Attempts to write mongodb models go to mongodb database.
        """
        if model._meta.model_name in self.mongodb_models or getattr(model, 'mongodb_model', False):
            return 'mongodb'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in mongodb is involved.
        """
        # Allow any relation between two models that are both in the mongodb database
        if obj1._meta.model_name in self.mongodb_models and obj2._meta.model_name in self.mongodb_models:
            return True
        # Allow if neither is in mongodb
        elif obj1._meta.model_name not in self.mongodb_models and obj2._meta.model_name not in self.mongodb_models:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure mongodb models only appear in the mongodb database.
        """
        if db == 'mongodb':
            # Only allow migration of MongoDB models to the mongodb database
            return model_name in self.mongodb_models or hints.get('model', None) and getattr(hints['model'], 'mongodb_model', False)
        else:
            # Allow migration of all other models to the default database
            return model_name not in self.mongodb_models and not (hints.get('model', None) and getattr(hints['model'], 'mongodb_model', False))