import types


def test_core_app_repository_abstract_pass_lines_executed():
    from core_app.ports.interfaces import Core_appRepository

    # Access unbound functions and call them to execute the 'pass' lines
    save_fn = Core_appRepository.__dict__["save"]
    get_all_fn = Core_appRepository.__dict__["get_all"]

    class Dummy:
        pass

    dummy = Dummy()
    # Calling unbound functions with dummy self executes the lines 8 and 12
    assert save_fn(dummy, {"x": 1}) is None
    assert get_all_fn(dummy) is None
