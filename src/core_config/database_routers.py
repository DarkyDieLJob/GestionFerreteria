class DynamicDatabaseRouter:
    def db_for_read(self, model, **hints):
        # Forzar lecturas en la base de datos por defecto
        return 'default'

    def db_for_write(self, model, **hints):
        # Forzar escrituras en la base de datos por defecto
        return 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Forzar que todas las migraciones se ejecuten en la base de datos por defecto
        # Independientemente de la app, solo permitir migraciones en 'default'
        return db == 'default'