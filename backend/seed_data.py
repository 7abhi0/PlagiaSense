from datetime import datetime, timedelta, timezone

import bcrypt

from app import create_app
from app.extensions import db


def seed_db():
    app = create_app()

    with app.app_context():
        demo_user = db.users.find_one({"email": "demo@plagiasense.com"})
        admin_user = db.users.find_one({"email": "admin@plagiasense.com"})

        if not demo_user:
            demo_result = db.users.insert_one(
                {
                    "email": "demo@plagiasense.com",
                    "password": bcrypt.hashpw(b"Password123", bcrypt.gensalt()).decode("utf-8"),
                    "name": "Demo User",
                    "role": "user",
                }
            )
            demo_user_id = demo_result.inserted_id
        else:
            demo_user_id = demo_user["_id"]

        if not admin_user:
            db.users.insert_one(
                {
                    "email": "admin@plagiasense.com",
                    "password": bcrypt.hashpw(b"Admin123", bcrypt.gensalt()).decode("utf-8"),
                    "name": "Administrator",
                    "role": "admin",
                }
            )

        if db.scans.count_documents({"user_id": demo_user_id}) >= 3:
            print("Seed data already exists.")
            return

        sample_scans = [
            {
                "user_id": demo_user_id,
                "text_excerpt": "Artificial intelligence and machine learning have changed academic writing workflows.",
                "plagiarism_score": 45.5,
                "matches": [],
                "highlighted_sentences": [],
                "ai_generated": True,
                "ai_confidence": 88.4,
                "ai_heatmap": [],
                "stylometry": {"avg_sentence_length": 15.5},
                "perplexity": {"burstiness": 4.2},
                "created_at": datetime.now(timezone.utc) - timedelta(days=2),
            },
            {
                "user_id": demo_user_id,
                "text_excerpt": "The quick brown fox jumps over the lazy dog.",
                "plagiarism_score": 92.0,
                "matches": [],
                "highlighted_sentences": [],
                "ai_generated": False,
                "ai_confidence": 5.2,
                "ai_heatmap": [],
                "stylometry": {"avg_sentence_length": 12.0},
                "perplexity": {"burstiness": 8.5},
                "created_at": datetime.now(timezone.utc) - timedelta(days=1),
            },
            {
                "user_id": demo_user_id,
                "text_excerpt": "We present a novel approach to unsupervised learning with graph representations.",
                "plagiarism_score": 0.0,
                "matches": [],
                "highlighted_sentences": [],
                "ai_generated": False,
                "ai_confidence": 11.5,
                "ai_heatmap": [],
                "stylometry": {"avg_sentence_length": 18.0},
                "perplexity": {"burstiness": 12.4},
                "created_at": datetime.now(timezone.utc),
            },
        ]

        for scan in sample_scans:
            db.scans.insert_one(scan)

        print("Seeded Firestore with demo users and sample scans.")


if __name__ == "__main__":
    seed_db()
