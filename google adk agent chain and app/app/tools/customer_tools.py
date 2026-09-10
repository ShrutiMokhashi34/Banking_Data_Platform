from google.cloud import bigquery
from google.adk.tools import ToolContext

PROJECT_ID = "bankingdataplatform"
DATASET = "ABC_BANK"

client = bigquery.Client(project=PROJECT_ID)


def _get_user_context(tool_context: ToolContext) -> dict:
    user_context = tool_context.state.get("user_context")

    if not user_context:
        return {}

    return user_context


def get_my_customer_profile(tool_context: ToolContext) -> dict:
    """
    Return the authenticated customer's own profile.

    Customer identity comes from trusted backend session state,
    never from the user's message.
    """

    user = _get_user_context(tool_context)

    if user.get("user_type") != "CUSTOMER":
        return {"error": "This tool is available only to customers."}

    customer_id = user.get("customer_id")

    if not customer_id:
        return {"error": "Authenticated customer ID is unavailable."}

    query = f"""
        SELECT
            CUSTOMER_ID,
            CUSTOMER_NAME,
            CUSTOMER_STATUS
        FROM `{PROJECT_ID}.{DATASET}.DIM_CUSTOMER`
        WHERE CUSTOMER_ID = @customer_id
        LIMIT 1
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "customer_id",
                "STRING",
                customer_id,
            )
        ]
    )

    try:
        results = client.query(
            query,
            job_config=job_config,
        ).result()

        rows = [dict(row.items()) for row in results]

        if not rows:
            return {"error": "Customer profile not found."}

        return rows[0]

    except Exception as e:
        return {"error": f"Unable to retrieve customer profile: {str(e)}"}
