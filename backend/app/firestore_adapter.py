from __future__ import annotations

import os
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from firebase_admin import credentials, firestore, get_app, initialize_app
import firebase_admin

ASCENDING = 1
DESCENDING = -1


def initialize_firestore(app):
    """
    Initialize Firestore client using either:
    - FIREBASE_SERVICE_ACCOUNT_JSON (preferred, JSON string)
    - fallback to ApplicationDefault (for local dev / Workload Identity)

    IMPORTANT:
    Also ensure the Firebase *default* app is initialized. Some parts of the code
    (e.g. firebase_admin.auth) use the default app implicitly.
    """
    # Prefer env vars (works in Render where config may not propagate as expected)
    service_account_json = (
        json.loads(os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "null"))
        if os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        else None
    )
    project_id = os.environ.get("FIREBASE_PROJECT_ID") or app.config.get("FIREBASE_PROJECT_ID")
    storage_bucket = os.environ.get("FIREBASE_STORAGE_BUCKET") or app.config.get("FIREBASE_STORAGE_BUCKET")
    app_name = os.environ.get("FIREBASE_APP_NAME", "plagiasense-backend") or app.config.get("FIREBASE_APP_NAME", "plagiasense-backend")

    options = {}
    if project_id:
        options["projectId"] = project_id
    if storage_bucket:
        options["storageBucket"] = storage_bucket

    # Prepare credential for initialization calls (named + default)
    credential = None
    if service_account_json:
        # service_account_json is already parsed JSON dict here
        credential = credentials.Certificate(service_account_json)

    # 1) Ensure DEFAULT app exists (firebase_admin.auth relies on it)
    try:
        firebase_admin.get_app()  # default app
    except ValueError:
        # Only initialize if we have enough info; otherwise let firebase_admin/auth fail clearly.
        firebase_admin.initialize_app(
            credential=credential,
            options=options or None,
        )

    # 2) Ensure a named app exists for Firestore client usage
    try:
        firebase_app = get_app(app_name)
    except ValueError:
        firebase_app = initialize_app(
            credential=credential,
            options=options or None,
            name=app_name,
        )

    return FirestoreDatabase(firestore.client(app=firebase_app))


@dataclass
class InsertOneResult:
    inserted_id: str


class FirestoreCursor:
    def __init__(self, documents):
        self._documents = documents

    def sort(self, field_name, direction):
        """Sort an in-memory cursor.

        This adapter mimics the subset of PyMongo behavior used by this app.
        """
        reverse = direction == DESCENDING

        def key(document):
            value = document.get(field_name)
            if isinstance(value, datetime) and value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            # None values should always sort last
            return (value is None, value)

        self._documents.sort(key=key, reverse=reverse)
        return self

    def __iter__(self):
        return iter(self._documents)


class FirestoreCollection:
    def __init__(self, client, name):
        self._client = client
        self._collection = client.collection(name)

    def find_one(self, filters, projection=None):
        if not filters:
            docs = list(self.find({}, projection))
            return docs[0] if docs else None

        # Support PyMongo-like behavior for Firestore document IDs.
        # Callers in this repo pass {'_id': <scan_id>}.
        doc_id = filters.get("_id")
        if doc_id is not None:
            snapshot = self._collection.document(str(doc_id)).get()
            if not snapshot.exists:
                return None
            document = _snapshot_to_document(snapshot)

            # Validate remaining filters (excluding _id) against loaded document.
            for key, value in filters.items():
                if key == "_id":
                    continue
                if document.get(key) != value:
                    return None

            return _apply_projection(document, projection)

        query = self._collection
        for field, value in filters.items():
            query = query.where(field, "==", value)

        for snapshot in query.limit(1).stream():
            return _apply_projection(_snapshot_to_document(snapshot), projection)
        return None

    def insert_one(self, document):
        payload = dict(document)
        doc_id = payload.pop("_id", None)
        if doc_id:
            doc_ref = self._collection.document(str(doc_id))
            doc_ref.set(payload)
        else:
            _, doc_ref = self._collection.add(payload)
        return InsertOneResult(inserted_id=doc_ref.id)

    def update_one(self, filters, update):
        document = self.find_one(filters)
        if not document:
            return None

        updates = update.get("$set", update)
        self._collection.document(str(document["_id"])).set(updates, merge=True)
        return document["_id"]

    def delete_one(self, filters):
        document = self.find_one(filters)
        if not document:
            return None

        self._collection.document(str(document["_id"])).delete()
        return document["_id"]

    def find(self, filters=None, projection=None):
        filters = filters or {}

        doc_id = filters.get("_id")
        if doc_id is not None:
            document = self.find_one(filters, projection)
            return FirestoreCursor([document] if document else [])

        query = self._collection
        for field, value in filters.items():
            query = query.where(field, "==", value)

        documents = [
            _apply_projection(_snapshot_to_document(snapshot), projection)
            for snapshot in query.stream()
        ]
        return FirestoreCursor(documents)

    def count_documents(self, filters=None):
        return sum(1 for _ in self.find(filters or {}))

    def aggregate(self, pipeline):
        filters = {}
        group = None

        for stage in pipeline:
            if "$match" in stage:
                filters = stage["$match"]
            if "$group" in stage:
                group = stage["$group"]

        documents = list(self.find(filters))
        if not group:
            return documents
        if not documents:
            return []

        result = {"_id": group.get("_id")}
        for output_field, expression in group.items():
            if output_field == "_id":
                continue

            if isinstance(expression, dict) and "$avg" in expression:
                field_name = str(expression["$avg"]).lstrip("$")
                values = [
                    float(document[field_name])
                    for document in documents
                    if isinstance(document.get(field_name), (int, float))
                ]
                result[output_field] = sum(values) / len(values) if values else 0

        return [result]


class FirestoreDatabase:
    def __init__(self, client):
        self.client = client
        self.users = FirestoreCollection(client, "users")
        self.scans = FirestoreCollection(client, "scans")


def _snapshot_to_document(snapshot):
    document = snapshot.to_dict() or {}
    document["_id"] = snapshot.id
    return document


def _apply_projection(document, projection):
    if not projection:
        return document

    included_fields = [field for field, enabled in projection.items() if enabled]
    excluded_fields = {field for field, enabled in projection.items() if not enabled}

    if included_fields:
        projected = {"_id": document.get("_id")}
        for field in included_fields:
            if field in document:
                projected[field] = document[field]
        return projected

    return {field: value for field, value in document.items() if field not in excluded_fields}
