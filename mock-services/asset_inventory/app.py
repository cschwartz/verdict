from pathlib import Path

from asset_inventory.models import AssetIndexItem, AssetItem
from mock_helpers import create_mock_app

app, _ = create_mock_app(
    title="Asset Inventory Mock",
    data_path=Path(__file__).parent / "data" / "assets.yaml",
    full_model=AssetItem,
    index_model=AssetIndexItem,
    resource_name="assets",
)
