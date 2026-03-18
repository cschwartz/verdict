from pathlib import Path

from iam.models import IAMUserIndexItem, IAMUserItem
from mock_helpers import create_mock_app

app, _ = create_mock_app(
    title="IAM Mock",
    data_path=Path(__file__).parent / "data" / "users.yaml",
    full_model=IAMUserItem,
    index_model=IAMUserIndexItem,
    resource_name="users",
)
