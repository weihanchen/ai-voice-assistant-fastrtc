"""
RoleRegistry 單元測試：註冊、查詢、唯一性、移除、重設、日誌檢查
"""

import pytest

from src.voice_assistant.roles.exceptions import RoleRegistryError
from src.voice_assistant.roles.predefined.assistant import AssistantRole
from src.voice_assistant.roles.predefined.coach import CoachRole
from src.voice_assistant.roles.registry import RoleRegistry


@pytest.fixture
def registry():
    reg = RoleRegistry()
    yield reg
    reg.reset()


def test_register_and_get_role(registry):
    role = AssistantRole()
    registry.register(role)
    got = registry.get("assistant")
    assert got.id == "assistant"
    assert got.name == "助理"


def test_register_duplicate_role_fail(registry):
    role1 = AssistantRole()
    role2 = AssistantRole()
    registry.register(role1)
    with pytest.raises(RoleRegistryError):
        registry.register(role2)


def test_remove_role(registry):
    role = CoachRole()
    registry.register(role)
    registry.remove("coach")
    assert len(registry.list_roles()) == 0
    with pytest.raises(RoleRegistryError):
        registry.get("coach")


def test_remove_nonexistent_role_fail(registry):
    with pytest.raises(RoleRegistryError):
        registry.remove("notfound")


def test_reset_registry(registry):
    registry.register(AssistantRole())
    registry.register(CoachRole())
    assert len(registry.list_roles()) == 2
    registry.reset()
    assert len(registry.list_roles()) == 0


def test_list_roles(registry):
    r1 = AssistantRole()
    r2 = CoachRole()
    registry.register(r1)
    registry.register(r2)
    ids = sorted([r.id for r in registry.list_roles()])
    assert ids == ["assistant", "coach"]
