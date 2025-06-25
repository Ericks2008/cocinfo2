#import os
import google.auth
from google.cloud import secretmanager

# The client can be initialized once and reused.
# It will automatically pick up credentials and project ID from the environment.
_secret_manager_client = secretmanager.SecretManagerServiceClient()

def get_secret_from_secret_manager_auto(secret_id: str, version_id: str = "latest") -> str:
    """
    Accesses a secret version from Google Cloud Secret Manager,
    automatically inferring the project ID from the execution environment.

    Args:
        secret_id: The ID of the secret.
        version_id: The version of the secret to access. Defaults to "latest".

    Returns:
        The decoded secret payload as a string.

    Raises:
        google.api_core.exceptions.NotFound: If the secret or version does not exist.
        google.api_core.exceptions.PermissionDenied: If the service account lacks
                                                   permission to access the secret.
        Exception: For other potential errors.
    """
    try:
        # The project ID is typically NOT required here.
        # The client will use the project associated with the ADC.
        # If you explicitly need the project ID (e.g., for logging),
        # you can get it using google.auth.default()
        credentials, project_id = google.auth.default()
        # print(f"Inferred Project ID: {project_id}") # For debugging

        # Build the resource name of the secret version.
        # Note: We still need the project ID in the resource name string.
        # But we get it automatically from the client's context.
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

        response = _secret_manager_client.access_secret_version(request={"name": name})
        secret_payload = response.payload.data.decode("UTF-8")
        return secret_payload

    except google.api_core.exceptions.NotFound as e:
        print(f"Error: Secret '{secret_id}' or version '{version_id}' not found.")
        raise e
    except google.api_core.exceptions.PermissionDenied as e:
        print(f"Error: Permission denied to access secret '{secret_id}'. "
              f"Ensure the service account has 'Secret Manager Secret Accessor' role.")
        raise e
    except Exception as e:
        print(f"An unexpected error occurred while accessing secret '{secret_id}': {e}")
        raise e

## Example Usage (in your main application code)
#if __name__ == "__main__":
#    secret_id = "app_secret_key" # The name of your secret in Secret Manager
#
#    try:
#        app_secret_value = get_secret_from_secret_manager_auto(secret_id)
#        print(f"Successfully retrieved secret '{secret_id}'.")
#        print("Secret value retrieved (not printed for security).")
#    except Exception as e:
#        print(f"Failed to retrieve secret: {e}")
