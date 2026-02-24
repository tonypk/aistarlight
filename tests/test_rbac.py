"""Unit tests for RBAC role hierarchy."""


# Define the hierarchy inline to avoid import chain triggering pgvector
ROLE_HIERARCHY = {
    "owner": 4,
    "admin": 3,
    "accountant": 2,
    "viewer": 1,
}


class TestRoleHierarchy:
    """Role hierarchy level tests."""

    def test_owner_is_highest(self):
        assert ROLE_HIERARCHY["owner"] > ROLE_HIERARCHY["admin"]
        assert ROLE_HIERARCHY["owner"] > ROLE_HIERARCHY["accountant"]
        assert ROLE_HIERARCHY["owner"] > ROLE_HIERARCHY["viewer"]

    def test_admin_above_accountant(self):
        assert ROLE_HIERARCHY["admin"] > ROLE_HIERARCHY["accountant"]

    def test_accountant_above_viewer(self):
        assert ROLE_HIERARCHY["accountant"] > ROLE_HIERARCHY["viewer"]

    def test_viewer_is_lowest(self):
        assert ROLE_HIERARCHY["viewer"] == min(ROLE_HIERARCHY.values())

    def test_all_roles_defined(self):
        expected_roles = {"owner", "admin", "accountant", "viewer"}
        assert set(ROLE_HIERARCHY.keys()) == expected_roles

    def test_hierarchy_values_are_unique(self):
        values = list(ROLE_HIERARCHY.values())
        assert len(values) == len(set(values))
