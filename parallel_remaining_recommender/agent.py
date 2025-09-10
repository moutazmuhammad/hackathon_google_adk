from . import instruction
import google.auth
from google.cloud import bigquery
from google.adk.agents import LlmAgent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode



client = bigquery.Client()
application_default_credentials, _ = google.auth.default()

credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)

tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)

bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config,
    # bigquery_tool_config=tool_config
)

GEMINI_MODEL = "gemini-2.5-flash"


lead_user_usage_remaining_agent = LlmAgent(
    name="LeadUsageRemainigAgent",
    model=GEMINI_MODEL,
    instruction=instruction.user_usage_remaining_agent,
    description="",
    tools=[bigquery_toolset],
    output_key="user_usage_remaining",
)

update_pointes_agent = LlmAgent(
    name="LeadUsageRemainigAgent",
    model=GEMINI_MODEL,
    instruction=instruction.pointes_agent_instruction,
    description="",
    tools=[bigquery_toolset],
    output_key="user_usage_remaining",
)
