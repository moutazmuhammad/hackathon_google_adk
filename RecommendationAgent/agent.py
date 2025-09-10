from . import instruction
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from .subagents.parallel_usage_recommender import usage_recommandation_agent
from .subagents.parallel_remaining_recommender import lead_user_usage_remaining_agent, update_pointes_agent

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
        AgentTool(agent=lead_user_usage_remaining_agent),
        AgentTool(agent=update_pointes_agent),
    ],
)
