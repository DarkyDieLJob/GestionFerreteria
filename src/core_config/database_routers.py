class DynamicDatabaseRouter:
    def db_for_read(self, model, **hints):
        # Dirige operaciones de lectura según la app_label
        if model._meta.app_label == 'core_app':
            return 'articles_db'
        if model._meta.app_label == 'cart':
            return 'cart_db'
        return 'default'

    def db_for_write(self, model, **hints):
        # Dirige operaciones de escritura según la app_label
        if model._meta.app_label == 'core_app':
            return 'articles_db'
        if model._meta.app_label == 'cart':
            return 'cart_db'
        return 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Permite migraciones solo en la base de datos correspondiente
        if app_label == 'core_app':
            return db == 'articles_db'
        if app_label == 'cart':
            return db == 'cart_db'
        return db == 'default'