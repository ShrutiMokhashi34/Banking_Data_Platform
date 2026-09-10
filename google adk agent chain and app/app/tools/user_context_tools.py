from google.adk.tools import ToolContext


def get_current_user(tool_context: ToolContext) -> dict:
    """
    Return the authenticated user's trusted identity from ADK session state.

    The identity is populated by the FastAPI backend after successful
    authentication. The user cannot control this value through chat.
    """

    user_context = tool_context.state.get("user_context")

    if not user_context:
        return {
            "authenticated": False,
            "message": "No authenticated user context is available."
        }

    return {
        "authenticated": True,
        "user_type": user_context.get("user_type"),
        "user_id": user_context.get("user_id"),
        "display_name": user_context.get("display_name"),
        "customer_id": user_context.get("customer_id"),
        "role": user_context.get("role"),
        "employee_status": user_context.get("employee_status"),
        "branch_id": user_context.get("branch_id"),
        "branch_name": user_context.get("branch_name"),
    }
