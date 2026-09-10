import json
import uuid

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.auth.authentication import (
    authenticate_user,
    create_access_token,
    decode_access_token,
)

from app.agent import root_agent
from app.tools.dashboard_tools import execute_dashboard_query
from app.tools.dashboard_summary_tools import get_dashboard_summary


# ============================================================
# Configuration
# ============================================================

APP_NAME = "banking_data_platform"


# ============================================================
# FastAPI
# ============================================================

app = FastAPI(
    title="Banking Data Platform API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://bankingdataplatform.web.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ADK Session / Runner
# ============================================================

session_service = InMemorySessionService()

runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service,
)


# ============================================================
# Request models
# ============================================================

class LoginRequest(BaseModel):
    user_type: str
    user_id: str
    password: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


# ============================================================
# Authentication helper
# ============================================================

def get_authenticated_user(
    authorization: str | None = None,
    x_access_token: str | None = None,
) -> dict:

    token = None

    # --------------------------------------------------------
    # Cloud Shell / development authentication
    # --------------------------------------------------------
    #
    # The frontend sends the JWT using X-Access-Token because
    # Cloud Shell can intercept the standard Authorization header.
    #
    if x_access_token:
        token = x_access_token.strip()

    # --------------------------------------------------------
    # Standard production authentication
    # --------------------------------------------------------
    #
    # This keeps normal Bearer token authentication available
    # when the application is deployed outside Cloud Shell.
    #
    elif authorization:

        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header",
            )

        token = authorization.replace(
            "Bearer ",
            "",
            1,
        ).strip()

    # --------------------------------------------------------
    # No token supplied
    # --------------------------------------------------------

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    # --------------------------------------------------------
    # Decode and validate JWT
    # --------------------------------------------------------

    try:

        identity = decode_access_token(token)

        if not identity:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token",
            )

        return identity

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )


# ============================================================
# Health check
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
    }


# ============================================================
# Login
# ============================================================

@app.post("/auth/login")
async def login(request: LoginRequest):

    # --------------------------------------------------------
    # Authenticate against AUTH_USERS + employee/customer data
    # --------------------------------------------------------

    identity = authenticate_user(
        user_type=request.user_type,
        user_id=request.user_id,
        password=request.password,
    )

    if identity is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    # --------------------------------------------------------
    # Create JWT
    # --------------------------------------------------------

    access_token = create_access_token(
        identity,
    )

    # --------------------------------------------------------
    # Create ADK session
    #
    # IMPORTANT:
    # The identity comes from the database after authentication.
    # It is NOT supplied by the frontend.
    # --------------------------------------------------------

    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=identity["user_id"],
        session_id=session_id,
        state={
            "user_context": identity,
        },
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "session_id": session_id,
        "user": identity,
    }


# ============================================================
# Verify current session
# ============================================================

@app.get("/auth/me")
def get_current_user(
    authorization: str | None = Header(default=None),
    x_access_token: str | None = Header(default=None),
):

    identity = get_authenticated_user(
        authorization=authorization,
        x_access_token=x_access_token,
    )

    return {
        "authenticated": True,
        "user": identity,
    }

# ============================================================
# Dashboard summary
# ============================================================

@app.get("/dashboard/summary")
def dashboard_summary(
    authorization: str | None = Header(default=None),
    x_access_token: str | None = Header(default=None),
):

    identity = get_authenticated_user(
        authorization=authorization,
        x_access_token=x_access_token,
    )

    result = get_dashboard_summary(
        identity
    )

    if result.get("error"):
        raise HTTPException(
            status_code=403,
            detail=result["error"],
        )

    return result

# ============================================================
# Chat
# ============================================================

@app.post("/chat")
async def chat(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
    x_access_token: str | None = Header(default=None),
):

    # --------------------------------------------------------
    # 1. Authenticate request
    # --------------------------------------------------------

    identity = get_authenticated_user(
        authorization=authorization,
        x_access_token=x_access_token,
    )

    # --------------------------------------------------------
    # 2. Retrieve the ADK session
    # --------------------------------------------------------

    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=identity["user_id"],
        session_id=request.session_id,
    )

    if session is None:

        raise HTTPException(
            status_code=404,
            detail="Chat session not found",
        )

    # --------------------------------------------------------
    # 3. Security check
    #
    # Make sure the session belongs to the authenticated user.
    # --------------------------------------------------------

    if session.user_id != identity["user_id"]:

        raise HTTPException(
            status_code=403,
            detail="You do not have access to this session",
        )

    # --------------------------------------------------------
    # 4. Build user message
    # --------------------------------------------------------

    user_message = types.Content(
        role="user",
        parts=[
            types.Part.from_text(
                text=request.message,
            )
        ],
    )

    # --------------------------------------------------------
    # 5. Run ADK
    #
    # The trusted identity is refreshed from the JWT on every
    # request. It is NOT taken from the user's message.
    # --------------------------------------------------------

    final_response = None

    async for event in runner.run_async(
        user_id=identity["user_id"],
        session_id=request.session_id,
        new_message=user_message,
        state_delta={
            "user_context": identity,
        },
    ):

        if event.is_final_response():

            if (
                event.content
                and event.content.parts
            ):

                final_response = event.content.parts[0].text

    if not final_response:

        final_response = (
            "I was unable to generate a response."
        )

    # --------------------------------------------------------
    # 6. Convert Dashboard Agent output into REAL dashboard data
    #
    # The dashboard JSON is an internal contract. It is never
    # shown directly to the user. The query is executed only
    # after the server-side authorization checks in
    # execute_dashboard_query().
    # --------------------------------------------------------

    dashboard = None
    response_text = final_response

    def parse_dashboard_payload(text: str):

        if not text:
            return None

        cleaned = text.strip()

        # ----------------------------------------------------
        # Handle accidental Markdown code fences from the model
        # ----------------------------------------------------

        if cleaned.startswith("```"):

            lines = cleaned.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        try:

            payload = json.loads(cleaned)

        except json.JSONDecodeError:

            return None

        # ----------------------------------------------------
        # Validate dashboard payload type
        # ----------------------------------------------------

        if (
            isinstance(payload, dict)
            and payload.get("type") in {
                "dashboard",
                "dashboard_error",
            }
        ):

            return payload

        return None

    dashboard_payload = parse_dashboard_payload(
        final_response
    )

    # --------------------------------------------------------
    # 7. Execute dashboard query if applicable
    # --------------------------------------------------------

    if dashboard_payload:

        # ----------------------------------------------------
        # Dashboard generation error
        # ----------------------------------------------------

        if dashboard_payload.get("type") == "dashboard_error":

            response_text = dashboard_payload.get(
                "message",
                "I could not generate that dashboard from the available data.",
            )

        # ----------------------------------------------------
        # Dashboard generated successfully
        # ----------------------------------------------------

        else:

            dashboard_result = execute_dashboard_query(
                dashboard_payload.get("query", ""),
                identity,
            )

            # ------------------------------------------------
            # Dashboard query failed
            # ------------------------------------------------

            if dashboard_result.get("error"):

                response_text = dashboard_result["error"]

            # ------------------------------------------------
            # Dashboard query succeeded
            # ------------------------------------------------

            else:

                dashboard = {
                    "title": dashboard_payload.get(
                        "title",
                        "Banking Dashboard",
                    ),
                    "description": dashboard_payload.get(
                        "description",
                        "",
                    ),
                    "charts": dashboard_payload.get(
                        "charts",
                        [],
                    ),
                    "columns": dashboard_result.get(
                        "columns",
                        [],
                    ),
                    "rows": dashboard_result.get(
                        "rows",
                        [],
                    ),
                    "row_count": dashboard_result.get(
                        "row_count",
                        0,
                    ),
                }

                response_text = (
                    dashboard_payload.get("description")
                    or "I've generated the dashboard from your authorized banking data."
                )

    # --------------------------------------------------------
    # 8. Return response
    # --------------------------------------------------------

    return {
        "session_id": request.session_id,
        "response": response_text,
        "dashboard": dashboard,
    }