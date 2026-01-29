"""
roles 子系統專用 logging 設定
"""

import logging

logger = logging.getLogger("voice_assistant.roles")
logger.setLevel(logging.INFO)
# 實際部署時可在主流程設定 handler、formatter
