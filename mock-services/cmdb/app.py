from pathlib import Path

from cmdb.models import SystemIndexItem, SystemItem
from mock_helpers import create_mock_app

app, _ = create_mock_app(
    title="CMDB Mock",
    data_path=Path(__file__).parent / "data" / "systems.yaml",
    full_model=SystemItem,
    index_model=SystemIndexItem,
    resource_name="systems",
)
