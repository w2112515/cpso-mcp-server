"""
LLM Router for CPSO-Protocol
"""

from typing import Literal
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from ..config import Config
from langchain_core.utils import convert_to_secret_str


class TokenBudgetTracker:
    """
    Tracks token usage and enforces budget limits.
    """
    def __init__(self, budget_claude: int = 100000):
        self.budget_claude = budget_claude
        self.used_tokens = 0
    
    def add_tokens(self, tokens: int):
        """
        Add used tokens to the tracker.
        
        Args:
            tokens: Number of tokens used
            
        Raises:
            ValueError: If adding tokens would exceed the budget
        """
        if self.used_tokens + tokens > self.budget_claude:
            raise ValueError(f"Token budget exceeded: {self.used_tokens + tokens} > {self.budget_claude}")
        self.used_tokens += tokens
    
    def get_remaining_tokens(self):
        """
        Get the number of remaining tokens in the budget.
        
        Returns:
            int: Number of remaining tokens
        """
        return self.budget_claude - self.used_tokens


# Global token tracker instance
token_tracker = TokenBudgetTracker(budget_claude=Config.TOKEN_BUDGET_CLAUDE)


def get_llm(role: Literal["cpso", "auditor", "tech", "scout"]):
    """
    Get the appropriate LLM instance based on the role.
    
    Args:
        role: The role of the agent requesting the LLM
        
    Returns:
        ChatAnthropic or ChatOpenAI: The appropriate LLM instance
        
    Priority:
        1. If ANTHROPIC_API_KEY is set, use Anthropic Claude
        2. If only OPENAI_API_KEY is set, use DeepSeek (OpenAI-compatible)
    """
    # 优先级：如果没有配置 ANTHROPIC_API_KEY，但配置了 OPENAI_API_KEY，使用 DeepSeek
    use_deepseek = Config.OPENAI_API_KEY and not Config.ANTHROPIC_API_KEY
    
    if use_deepseek:
        # Use DeepSeek API (OpenAI-compatible)
        return ChatOpenAI(
            model=Config.DEEPSEEK_MODEL_NAME,
            temperature=0.3 if role in ["cpso", "auditor", "tech"] else 0.7,
            api_key=convert_to_secret_str(Config.OPENAI_API_KEY),
            base_url="https://api.deepseek.com/v1"
        )
    
    # Use Anthropic Claude
    if role in ["cpso", "auditor", "tech"]:
        # Use Claude 3.5 Sonnet for high-level reasoning roles
        return ChatAnthropic(
            model_name=Config.CLAUDE_SONNET_MODEL_NAME,
            temperature=0.3,
            timeout=None,
            stop=None
        )
    elif role == "scout":
        # Use Claude 3 Haiku for fast, lightweight tasks
        return ChatAnthropic(
            model_name=Config.CLAUDE_HAIKU_MODEL_NAME,
            temperature=0.7,
            timeout=None,
            stop=None
        )
    else:
        raise ValueError(f"Unknown role: {role}")