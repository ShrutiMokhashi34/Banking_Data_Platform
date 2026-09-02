from databricks.sdk import WorkspaceClient
import getpass

SCOPE = "snowflake-creds"
USER_KEY = "snowflake-user"
PASSWORD_KEY = "snowflake-password"

w = WorkspaceClient()

try:
    w.secrets.create_scope(scope=SCOPE)
    print(f"Created secret scope: {SCOPE}")
except Exception as e:
    if "already exists" in str(e).lower():
        print(f"Secret scope already exists: {SCOPE}")
    else:
        raise

snowflake_user = input("Enter Snowflake username: ").strip()
snowflake_password = getpass.getpass("Enter Snowflake password: ")

if not snowflake_user:
    raise ValueError("Snowflake username cannot be empty.")
if not snowflake_password:
    raise ValueError("Snowflake password cannot be empty.")

w.secrets.put_secret(scope=SCOPE, key=USER_KEY, string_value=snowflake_user)
w.secrets.put_secret(scope=SCOPE, key=PASSWORD_KEY, string_value=snowflake_password)

print(f"Stored secrets {USER_KEY} and {PASSWORD_KEY} in scope {SCOPE}.")