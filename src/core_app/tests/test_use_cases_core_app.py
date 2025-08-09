from unittest.mock import MagicMock

from core_app.domain.use_cases import Core_appUseCase


def test_use_case_calls_repository_save_and_returns_result():
    repo = MagicMock()
    repo.save.return_value = {"id": 1, "name": "item"}
    uc = Core_appUseCase(repo)

    data = {"name": "item"}
    result = uc.execute(data)

    repo.save.assert_called_once_with(data)
    assert result == {"id": 1, "name": "item"}


def test_use_case_propagates_repo_errors():
    repo = MagicMock()
    repo.save.side_effect = ValueError("bad data")
    uc = Core_appUseCase(repo)

    try:
        uc.execute({})
        assert False, "Expected ValueError"
    except ValueError as e:
        assert str(e) == "bad data"
