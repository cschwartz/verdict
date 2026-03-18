# pyright: reportPrivateImportUsage=none
import factory

from app.models.gold_source import GoldSourceType
from app.models.user import Permission, Role, RolePermission, User, UserRole
from tests.factories import BaseModelFactory


class UserFactory(BaseModelFactory):
    class Meta:  # type: ignore[override]  # factory-boy expects Meta override per subclass
        model = User

    username = factory.Sequence(lambda n: f"user-{n:04d}")
    email = factory.Sequence(lambda n: f"user-{n:04d}@example.com")
    is_active = True
    gold_source_id = factory.Sequence(lambda n: f"iam-user-{n:04d}")
    gold_source_type = GoldSourceType.IAM_USER


class RoleFactory(BaseModelFactory):
    class Meta:  # type: ignore[override]  # factory-boy expects Meta override per subclass
        model = Role

    name = factory.Sequence(lambda n: f"role-{n:04d}")
    description = factory.Faker("sentence")
    gold_source_id = factory.Sequence(lambda n: f"iam-group-{n:04d}")
    gold_source_type = GoldSourceType.IAM_GROUP


class UserRoleFactory(BaseModelFactory):
    class Meta:  # type: ignore[override]  # factory-boy expects Meta override per subclass
        model = UserRole

    user_id = None
    role_id = None


class RolePermissionFactory(BaseModelFactory):
    class Meta:  # type: ignore[override]  # factory-boy expects Meta override per subclass
        model = RolePermission

    role_id = None
    permission_id = None


class PermissionFactory(BaseModelFactory):
    class Meta:  # type: ignore[override]  # factory-boy expects Meta override per subclass
        model = Permission

    resource = factory.Sequence(lambda n: f"resource-{n:04d}")
    subresource = None
    action = factory.Iterator(["read", "write", "delete", "admin"])
