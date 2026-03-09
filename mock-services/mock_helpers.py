from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

_BASE_DIR = Path(__file__).resolve().parent


def load_yaml(path: Path) -> list[dict[str, Any]]:
    resolved = path.resolve()
    if not resolved.is_relative_to(_BASE_DIR):
        raise ValueError(f"path {resolved} is outside base directory {_BASE_DIR}")
    with resolved.open() as f:
        data = yaml.safe_load(f)
    if data is None:
        return []
    if not isinstance(data, list):
        raise ValueError(f"expected a list in {resolved}, got {type(data).__name__}")
    return data


def create_mock_app[TFull: BaseModel, TIndex: BaseModel](
    *,
    title: str,
    data_path: Path,
    full_model: type[TFull],
    index_model: type[TIndex],
    id_field: str = "id",
    resource_name: str,
) -> tuple[FastAPI, list[TFull]]:
    raw = load_yaml(data_path)
    items: list[TFull] = [full_model.model_validate(item) for item in raw]
    index: dict[str, TFull] = {str(getattr(item, id_field)): item for item in items}

    app = FastAPI(title=title)

    @app.get(f"/{resource_name}", response_model=list[index_model])
    def list_items(offset: int = 0, limit: int = 50) -> list[index_model]:
        return [
            index_model.model_validate(item, from_attributes=True)
            for item in items[offset : offset + limit]
        ]

    @app.get(f"/{resource_name}/{{item_id}}", response_model=full_model)
    def get_item(item_id: str) -> TFull:
        if item_id not in index:
            raise HTTPException(
                status_code=404, detail=f"{resource_name} {item_id} not found"
            )
        return index[item_id]

    return app, items
