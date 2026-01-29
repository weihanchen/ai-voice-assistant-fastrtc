"""
基底角色抽象類別，供所有角色繼承。
"""

from abc import ABC, abstractmethod


class BaseRole(ABC):
    """AI 角色基底抽象類別"""

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        取得該角色的 LLM 系統提示語。
        """
        pass
