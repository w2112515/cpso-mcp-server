"""
Configuration Management for CPSO-Protocol
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class Config:
    """Configuration class for CPSO-Protocol."""
    
    # API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Service URLs
    # 在 Vercel 等 serverless 环境中，如果未设置 REDIS_URL，使用 None 而不是 localhost
    # 这样可以避免 DNS_HOSTNAME_RESOLVED_PRIVATE 错误
    _redis_url = os.getenv("REDIS_URL")
    if _redis_url is None:
        # 检查是否在 Vercel 环境中
        is_vercel = os.getenv("VERCEL") == "1"
        if is_vercel:
            # 在 Vercel 中，如果没有配置 Redis，设置为 None（禁用 Redis）
            REDIS_URL = None
        else:
            # 本地开发环境，使用默认的 localhost
            REDIS_URL = "redis://localhost:6379"
    else:
        REDIS_URL = _redis_url
    
    CHROMADB_PATH = os.getenv("CHROMADB_PATH", "./chroma_db")
    
    # Model Configuration
    DEEPSEEK_MODEL_NAME = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
    CLAUDE_SONNET_MODEL_NAME = os.getenv("CLAUDE_SONNET_MODEL_NAME", "claude-3-5-sonnet-20240620")
    CLAUDE_HAIKU_MODEL_NAME = os.getenv("CLAUDE_HAIKU_MODEL_NAME", "claude-3-haiku-20240307")
    
    # Limits and Budgets
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))
    TOKEN_BUDGET_USD = float(os.getenv("TOKEN_BUDGET_USD", "2.0"))
    TOKEN_BUDGET_CLAUDE = int(os.getenv("TOKEN_BUDGET_CLAUDE", "100000"))

    @classmethod
    def validate(cls):
        """Validate that all required configuration values are set."""
        # Either Anthropic or OpenAI (DeepSeek) API key must be set
        if not cls.ANTHROPIC_API_KEY and not cls.OPENAI_API_KEY:
            raise ValueError("Either ANTHROPIC_API_KEY or OPENAI_API_KEY is required but not set in environment variables.")
        
        return True