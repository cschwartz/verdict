# pyright: reportPrivateImportUsage=none
import factory

from app.models.gold_source import GoldSourceType
from app.models.system import System
from tests.factories import BaseModelFactory


class SystemFactory(BaseModelFactory):
    class Meta:  # type: ignore[override]  # factory-boy expects Meta override per subclass
        model = System

    primary_fqdn = factory.Sequence(lambda n: f"host-{n:04d}.prod.example.com")
    tags = factory.LazyFunction(lambda: ["env:production", "tier:backend"])
    gold_source_id = factory.Sequence(lambda n: f"SYS-{n:04d}")
    gold_source_type = GoldSourceType.CMDB
