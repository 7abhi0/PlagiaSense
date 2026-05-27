from firebase_admin import auth


def verify_firebase_id_token(id_token, project_id=None):
    if not id_token:
        raise ValueError("Firebase ID token is required")

    # Use the provided project_id (when available) to ensure correct audience checks.
    # Some Firebase setups fail verification if the wrong audience is used.
    if project_id:
        return auth.verify_id_token(id_token, audience=project_id)

    return auth.verify_id_token(id_token)

