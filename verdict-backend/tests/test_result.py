import pytest

from app.errors import DBError, DuplicateError
from app.result import Err, Nothing, Ok, Option, Result, Some


class TestOk:
    def test_unwrap_returns_value(self):
        assert Ok(42).unwrap() == 42

    def test_unwrap_or_returns_value(self):
        assert Ok(42).unwrap_or(0) == 42


class TestErr:
    def test_unwrap_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match="Called unwrap on Err"):
            Err("bad").unwrap()

    def test_unwrap_or_returns_default(self):
        assert Err("bad").unwrap_or(99) == 99

    def test_str_delegates_to_value(self):
        assert str(Err(DBError(message="connection lost"))) == "database error: connection lost"


class TestSome:
    def test_unwrap_returns_value(self):
        assert Some(42).unwrap() == 42

    def test_unwrap_or_returns_value(self):
        assert Some(42).unwrap_or(0) == 42


class TestNothing:
    def test_unwrap_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match="Called unwrap on Nothing"):
            Nothing().unwrap()

    def test_unwrap_or_returns_default(self):
        assert Nothing().unwrap_or(99) == 99

    def test_str(self):
        assert str(Nothing()) == "nothing"


class TestDBError:
    def test_str(self):
        assert str(DBError(message="connection lost")) == "database error: connection lost"


class TestDuplicateError:
    def test_str(self):
        err = DuplicateError(model="User", key="email:a@b.com", detail="already exists")
        assert str(err) == "duplicate User: email:a@b.com (already exists)"


class TestMatchNarrowing:
    def test_match_result_ok(self):
        result: Result[int, str] = Ok(10)
        match result:
            case Ok(value=v):
                assert v == 10
            case Err():
                pytest.fail("Should not match Err")

    def test_match_result_err(self):
        result: Result[int, str] = Err("fail")
        match result:
            case Ok():
                pytest.fail("Should not match Ok")
            case Err(value=v):
                assert v == "fail"

    def test_match_option_some(self):
        result: Option[int] = Some(10)
        match result:
            case Some(value=v):
                assert v == 10
            case Nothing():
                pytest.fail("Should not match Nothing")

    def test_match_option_nothing(self):
        result: Option[int] = Nothing()
        match result:
            case Some():
                pytest.fail("Should not match Some")
            case Nothing():
                pass  # expected

    def test_match_composed_ok_some(self):
        result: Result[Option[int], DBError] = Ok(Some(42))
        match result:
            case Ok(value=opt):
                match opt:
                    case Some(value=v):
                        assert v == 42
                    case Nothing():
                        pytest.fail("Should not match Nothing")
            case Err():
                pytest.fail("Should not match Err")

    def test_match_composed_ok_nothing(self):
        result: Result[Option[int], DBError] = Ok(Nothing())
        match result:
            case Ok(value=opt):
                match opt:
                    case Some():
                        pytest.fail("Should not match Some")
                    case Nothing():
                        pass  # expected
            case Err():
                pytest.fail("Should not match Err")

    def test_match_composed_err(self):
        result: Result[Option[int], DBError] = Err(DBError(message="connection lost"))
        match result:
            case Ok():
                pytest.fail("Should not match Ok")
            case Err(value=err):
                assert err.message == "connection lost"
