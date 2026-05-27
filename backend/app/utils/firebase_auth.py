from firebase_admin import auth


def verify_firebase_id_token(id_token, project_id=None):
    if not id_token:
        raise ValueError("Firebase ID token is required")

    return auth.verify_id_token(id_token)
