# Mock server for local development and testing -- not for production use,
# and intentionally untested.

from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException

from asset_inventory.models import AssetIndexItem, AssetItem

_data_dir = Path(__file__).parent / "data"

with (_data_dir / "assets.yaml").open() as f:
    _raw = yaml.safe_load(f)

_items: list[AssetItem] = [AssetItem.model_validate(item) for item in _raw]
_index: dict[str, AssetItem] = {item.id: item for item in _items}

app = FastAPI(title="Asset Inventory Mock")


@app.get("/assets", response_model=list[AssetIndexItem])
def list_assets(offset: int = 0, limit: int = 50) -> list[AssetIndexItem]:
    return [
        AssetIndexItem(id=item.id, name=item.name)
        for item in _items[offset : offset + limit]
    ]


@app.get("/assets/{asset_id}", response_model=AssetItem)
def get_asset(asset_id: str) -> AssetItem:
    if asset_id not in _index:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    return _index[asset_id]
