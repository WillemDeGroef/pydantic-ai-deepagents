__version__ = "0.1.0"

from pydantic_ai_deepagents.agent import create_deep_agent
from pydantic_ai_deepagents.deps import DeepAgentDeps, Skill
from pydantic_ai_deepagents.skills import load_skill_from_text

__all__ = [
    "__version__",
    "create_deep_agent",
    "DeepAgentDeps",
    "Skill",
    "load_skill_from_text",
]
