import httpx
from pydantic import TypeAdapter
from pydantic import ValidationError as PydanticValidationError

from app.errors import FetchError, RemoteValidationError
from app.result import Err, Ok, Result


def fetch_json[T](
    client: httpx.Client,
    url: str,
    adapter: TypeAdapter[T],
) -> Result[T, FetchError | RemoteValidationError]:
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as e:
        return Err(FetchError(url=url, raw=str(e)))
    try:
        return Ok(adapter.validate_json(response.content))
    except PydanticValidationError as e:
        return Err(RemoteValidationError(raw=str(e), url=url))
