from . import instruction
import google.auth
from google.cloud import bigquery
from google.adk.agents import LlmAgent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.adk.agents import ParallelAgent
from google.adk.agents import SequentialAgent

client = bigquery.Client()
application_default_credentials, _ = google.auth.default()

credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)

tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)

bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config,
    bigquery_tool_config=tool_config
)

GEMINI_MODEL = "gemini-2.5-flash"

lead_user_usage_agent = LlmAgent(
    name="LeadUsageAgent",
    model=GEMINI_MODEL,
    instruction=instruction.usage_instruction,
    description="",
    tools=[bigquery_toolset],
    output_key="usage_status",
)

lead_plan_agent = LlmAgent(
    name="LeadPlanAgent",
    model=GEMINI_MODEL,
    instruction=instruction.plan_instruction,
    description="",
    tools=[bigquery_toolset],
    output_key="plans_list",
)


usage_plan_agent = ParallelAgent(
     name="ParallelUsageRecommandation",
     sub_agents=[lead_user_usage_agent, lead_plan_agent],
     description=""
)


action_recommender_agent = LlmAgent(
    name="ActionRecommenderAgent",
    model=GEMINI_MODEL,
    instruction=instruction.recommender_instruction,
    description="Recommends the most suitable Vodafone plan based on usage and available plans.",
    output_key="recommended_plan",
)

usage_recommandation_agent = SequentialAgent(
    name="usage_recommandation_agent",
    sub_agents=[usage_plan_agent, action_recommender_agent],
    description="A chat pipeline agent that recommends Vodafone company plans based on user usage data from BigQuery",
)
