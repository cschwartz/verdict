# pyright: reportPrivateImportUsage=none
import factory

from app.models.asset import Asset
from app.models.gold_source import GoldSourceType
from tests.factories import BaseModelFactory


class AssetFactory(BaseModelFactory):
    class Meta:  # type: ignore[override]
        model = Asset

    name = factory.Iterator(
        [
            "Online Banking Portal",
            "Customer CRM",
            "Payment Processing Engine",
            "Internal HR System",
            "Data Analytics Platform",
        ]
    )
    description = factory.Faker("sentence")
    tags = factory.LazyFunction(lambda: ["protection-level:medium", "business-unit:engineering"])
    gold_source_id = factory.Sequence(lambda n: f"SVC-{n:04d}")
    gold_source_type = GoldSourceType.ASSET_INVENTORY
