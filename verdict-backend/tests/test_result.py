import pytest

from app.errors import DBError, DuplicateError, FetchError, ValidationError
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
        assert str(Err(DBError(statement=None, raw="connection lost"))) == "database error"


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
    def test_message_is_safe(self):
        err = DBError(statement="SELECT * FROM users WHERE id = :id_1", raw="connection lost")
        assert err.message == "database error"

    def test_detail_includes_statement(self):
        err = DBError(statement="SELECT * FROM users WHERE id = :id_1", raw="connection lost")
        assert err.detail == "database error: SELECT * FROM users WHERE id = :id_1"

    def test_detail_without_statement(self):
        err = DBError(statement=None, raw="connection lost")
        assert err.detail == "database error"

    def test_str_returns_message(self):
        err = DBError(statement="SELECT 1", raw="connection lost")
        assert str(err) == "database error"


class TestDuplicateError:
    def test_message_is_safe(self):
        err = DuplicateError(model="User", key="email:a@b.com")
        assert err.message == "duplicate User"

    def test_detail_includes_key(self):
        err = DuplicateError(model="User", key="email:a@b.com")
        assert err.detail == "duplicate User: email:a@b.com"


class TestFetchError:
    def test_message_is_safe(self):
        err = FetchError(url="http://example.com/api", raw="500 Internal Server Error")
        assert err.message == "upstream service error"

    def test_detail_includes_url_and_raw(self):
        err = FetchError(url="http://example.com/api", raw="500 Internal Server Error")
        assert err.detail == "fetch error (http://example.com/api): 500 Internal Server Error"


class TestValidationError:
    def test_message_is_safe(self):
        err = ValidationError(raw="field 'name' is required")
        assert err.message == "validation error"

    def test_detail_includes_raw(self):
        err = ValidationError(raw="field 'name' is required")
        assert err.detail == "validation error: field 'name' is required"


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
        result: Result[Option[int], DBError] = Err(DBError(statement=None, raw="connection lost"))
        match result:
            case Ok():
                pytest.fail("Should not match Ok")
            case Err(value=err):
                assert err.raw == "connection lost"
