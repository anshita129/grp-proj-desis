"""
Database router to send all operations for the `trading` app to the
`trading` Postgres database and keep other apps on the default DB.
"""


class TradingRouter:
    """A router to control DB operations for the trading app."""

    route_app_labels = {"trading"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'trading'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'trading'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
            # allow relations if both objects are in the trading DB
            if getattr(obj1, '_state', None) and getattr(obj2, '_state', None):
                return obj1._state.db == obj2._state.db
            return None
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == 'trading'
        # Ensure the trading DB only gets migrations for the trading app
        if db == 'trading':
            return False
        return None
