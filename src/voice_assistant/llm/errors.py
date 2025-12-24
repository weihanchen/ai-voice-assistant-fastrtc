"""LLM error classes for voice assistant."""


class LLMError(Exception):
    """LLM 相關錯誤基底類別。"""

    pass


class LLMConnectionError(LLMError):
    """連線錯誤。"""

    pass


class LLMAuthenticationError(LLMError):
    """認證錯誤（API Key 無效）。"""

    pass


class LLMRateLimitError(LLMError):
    """速率限制錯誤。"""

    pass
