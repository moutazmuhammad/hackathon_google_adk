from . import instruction
import google.auth
from google.cloud import bigquery
import logging
from google.adk.agents import LlmAgent
from google.adk.tools.function_tool import FunctionTool
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


def get_user_usage(user_email: str) -> dict:
    try:
        query = """
        SELECT 
            AVG(calls_minutes) AS avg_calls,
            AVG(sms_count) AS avg_sms,
            AVG(data_gb) AS avg_data
        FROM `vf-mc2dev-ca-nonlive.vodafone_hackathon.user_usage`
        WHERE user_email = @user_email
          AND month >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH)
        """

        # Dry run to estimate cost
        dry_run_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("user_email", "STRING", user_email)],
            dry_run=True,
            use_query_cache=False,
        )
        dry_run_job = client.query(query, job_config=dry_run_config)
        bytes_billed = dry_run_job.total_bytes_billed
        max_bytes = 104857600  # 100 MB limit

        if bytes_billed > max_bytes:
            logging.error(f"Query exceeds max bytes: {bytes_billed}")
            return {"error": f"Query too costly: estimated {bytes_billed} > {max_bytes}"}

        # Actual execution
        exec_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("user_email", "STRING", user_email)],
            dry_run=False,
        )
        result = client.query(query, job_config=exec_config).result()

        for row in result:
            if row.avg_calls is not None:
                logging.info(f"Retrieved usage for {user_email}")
                return {
                    "user_email": user_email,
                    "avg_calls": row.avg_calls,
                    "avg_sms": row.avg_sms,
                    "avg_data": row.avg_data,
                }

        logging.warning(f"No usage data found for {user_email}")
        return {}

    except Exception as e:
        logging.error(f"Error retrieving usage for {user_email}: {e}", exc_info=True)
        return {}


def get_plans(_: str = "") -> list[dict]:

    try:
        query = """
        SELECT 
            plan_name,
            calls_limit,
            sms_limit,
            data_limit,
            price,
            benefits
        FROM `vf-mc2dev-ca-nonlive.vodafone_hackathon.plans`
        LIMIT 100
        """

        dry_run_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        dry_run_job = client.query(query, job_config=dry_run_config)
        bytes_billed = dry_run_job.total_bytes_billed
        max_bytes = 104857600  # 100 MB limit

        if bytes_billed > max_bytes:
            logging.error(f"Plans query exceeds max bytes: {bytes_billed}")
            return [{"error": f"Query too costly: estimated {bytes_billed} > {max_bytes}"}]

        # Actual execution
        exec_config = bigquery.QueryJobConfig(dry_run=False)
        result = client.query(query, job_config=exec_config).result()

        plans = [
            {
                "plan_name": row.plan_name,
                "calls_limit": row.calls_limit,
                "sms_limit": row.sms_limit,
                "data_limit": row.data_limit,
                "price": row.price,
                "benefits": row.benefits,
            }
            for row in result
        ]

        logging.info("Successfully retrieved plans")
        return plans

    except Exception as e:
        logging.error(f"Error retrieving plans: {e}", exc_info=True)
        return []


get_plans_tool = FunctionTool(get_plans)
get_user_usage_tool = FunctionTool(get_user_usage)

lead_user_usage_agent = LlmAgent(
    name="LeadUsageAgent",
    model=GEMINI_MODEL,
    instruction=instruction.usage_instruction,
    description="",
    tools=[bigquery_toolset, get_user_usage_tool],
    output_key="usage_status",
)

lead_plan_agent = LlmAgent(
    name="LeadPlanAgent",
    model=GEMINI_MODEL,
    instruction=instruction.plan_instruction,
    description="",
    tools=[get_plans_tool],
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