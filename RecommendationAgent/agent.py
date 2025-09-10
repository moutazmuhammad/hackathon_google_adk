from . import instruction
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from .subagents.parallel_usage_recommender import usage_recommandation_agent

MODEL = "gemini-2.5-flash"
APP_NAME = "RecommendationAgent"


root_agent = LlmAgent(
    name="RecommendationAgent",
    model=MODEL,
    description="",
    instruction=instruction.MAIN_INSTRUCTION,
    output_key="seminal_paper",
    tools=[
        AgentTool(agent=usage_recommandation_agent),
    ],
)