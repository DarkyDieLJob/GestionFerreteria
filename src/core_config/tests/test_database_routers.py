import types

from core_config.database_routers import DynamicDatabaseRouter


class DummyModel:
    class _Meta:
        def __init__(self, app_label):
            self.app_label = app_label

    def __init__(self, app_label):
        self._meta = self._Meta(app_label)


def test_db_for_read_routes_core_app_and_cart_and_default():
    r = DynamicDatabaseRouter()
    assert r.db_for_read(DummyModel("core_app")) == "articles_db"
    assert r.db_for_read(DummyModel("cart")) == "cart_db"
    assert r.db_for_read(DummyModel("other")) == "default"


def test_db_for_write_routes_core_app_and_cart_and_default():
    r = DynamicDatabaseRouter()
    assert r.db_for_write(DummyModel("core_app")) == "articles_db"
    assert r.db_for_write(DummyModel("cart")) == "cart_db"
    assert r.db_for_write(DummyModel("other")) == "default"


def test_allow_migrate_core_app_cart_and_default():
    r = DynamicDatabaseRouter()
    # core_app allowed only on articles_db
    assert r.allow_migrate("articles_db", "core_app") is True
    assert r.allow_migrate("default", "core_app") is False
    # cart allowed only on cart_db
    assert r.allow_migrate("cart_db", "cart") is True
    assert r.allow_migrate("default", "cart") is False
    # others on default
    assert r.allow_migrate("default", "other") is True
    assert r.allow_migrate("articles_db", "other") is False
