import os
import datetime
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

# Load configuration
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/plagiasense')

def seed_db():
    print(f"Connecting to MongoDB at: {MONGO_URI}")
    client = MongoClient(MONGO_URI)
    db = client.get_default_database() if "mongodb+srv" in MONGO_URI or "/" in MONGO_URI.split("@")[-1] else client["plagiasense"]
    
    # 1. Clean existing data (optional, but good for a fresh start)
    db.users.delete_many({})
    db.scans.delete_many({})
    print("Cleared existing users and scans collections.")
    
    # 2. Hash passwords
    demo_pw = bcrypt.hashpw(b"Password123", bcrypt.gensalt()).decode('utf-8')
    admin_pw = bcrypt.hashpw(b"Admin123", bcrypt.gensalt()).decode('utf-8')
    
    # 3. Create Users
    demo_user = {
        "email": "demo@plagiasense.com",
        "password": demo_pw,
        "name": "Demo User",
        "role": "user"
    }
    admin_user = {
        "email": "admin@plagiasense.com",
        "password": admin_pw,
        "name": "Administrator",
        "role": "admin"
    }
    
    demo_id = db.users.insert_one(demo_user).inserted_id
    admin_id = db.users.insert_one(admin_user).inserted_id
    print(f"Created user: demo@plagiasense.com (ID: {demo_id})")
    print(f"Created admin: admin@plagiasense.com (ID: {admin_id})")
    
    # 4. Insert 3 Sample Scan Records for Demo User
    sample_scans = [
        {
            "user_id": ObjectId(demo_id),
            "text_excerpt": "Artificial intelligence and machine learning have revolutionized modern computer science. Many academic studies use natural language processing models to generate articles, raising questions about authorship and authenticity.",
            "plagiarism_score": 45.5,
            "matches": [
                {
                    "original_text": "Artificial intelligence and machine learning have revolutionized modern computer science.",
                    "matched_text": "Artificial intelligence and machine learning have revolutionized modern computer science research fields.",
                    "similarity_score": 95.0,
                    "source_url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
                    "category": "exact"
                },
                {
                    "original_text": "Many academic studies use natural language processing models to generate articles.",
                    "matched_text": "Researchers and scholars often apply NLP language models to synthesize scientific publications.",
                    "similarity_score": 78.5,
                    "source_url": "https://arxiv.org/abs/2301.00001",
                    "category": "paraphrased"
                }
            ],
            "highlighted_sentences": [
                {
                    "text": "Artificial intelligence and machine learning have revolutionized modern computer science.",
                    "similarity": 95.0,
                    "category": "exact",
                    "source_url": "https://en.wikipedia.org/wiki/Artificial_intelligence"
                },
                {
                    "text": "Many academic studies use natural language processing models to generate articles, raising questions about authorship and authenticity.",
                    "similarity": 78.5,
                    "category": "paraphrased",
                    "source_url": "https://arxiv.org/abs/2301.00001"
                }
            ],
            "ai_generated": True,
            "ai_confidence": 88.4,
            "ai_heatmap": [
                {
                    "text": "Artificial intelligence and machine learning have revolutionized modern computer science.",
                    "ai_likelihood": 78.2
                },
                {
                    "text": "Many academic studies use natural language processing models to generate articles, raising questions about authorship and authenticity.",
                    "ai_likelihood": 92.6
                }
            ],
            "stylometry": {
                "avg_sentence_length": 15.5,
                "vocabulary_richness": 0.65,
                "stopword_density": 0.42,
                "punctuation_density": 0.05
            },
            "perplexity": {
                "burstiness": 4.2,
                "word_entropy": 4.8,
                "char_entropy": 2.1,
                "perplexity_proxy": 15.3,
                "duplicate_bigram_ratio": 0.08,
                "duplicate_trigram_ratio": 0.02
            },
            "created_at": datetime.datetime.utcnow() - datetime.timedelta(days=2)
        },
        {
            "user_id": ObjectId(demo_id),
            "text_excerpt": "The quick brown fox jumps over the lazy dog. This is a simple pangram containing every letter of the English alphabet. In typography, design, and typesetting, this text is often used to demonstrate layout and letterforms.",
            "plagiarism_score": 92.0,
            "matches": [
                {
                    "original_text": "The quick brown fox jumps over the lazy dog.",
                    "matched_text": "The quick brown fox jumps over the lazy dog.",
                    "similarity_score": 100.0,
                    "source_url": "https://en.wikipedia.org/wiki/The_quick_brown_fox_jumps_over_the_lazy_dog",
                    "category": "exact"
                },
                {
                    "original_text": "This is a simple pangram containing every letter of the English alphabet.",
                    "matched_text": "A quick brown fox jumps over the lazy dog is an English pangram containing all letters.",
                    "similarity_score": 85.0,
                    "source_url": "https://en.wikipedia.org/wiki/Pangram",
                    "category": "exact"
                }
            ],
            "highlighted_sentences": [
                {
                    "text": "The quick brown fox jumps over the lazy dog.",
                    "similarity": 100.0,
                    "category": "exact",
                    "source_url": "https://en.wikipedia.org/wiki/The_quick_brown_fox_jumps_over_the_lazy_dog"
                },
                {
                    "text": "This is a simple pangram containing every letter of the English alphabet.",
                    "similarity": 85.0,
                    "category": "exact",
                    "source_url": "https://en.wikipedia.org/wiki/Pangram"
                },
                {
                    "text": "In typography, design, and typesetting, this text is often used to demonstrate layout and letterforms.",
                    "similarity": 30.5,
                    "category": "unique",
                    "source_url": None
                }
            ],
            "ai_generated": False,
            "ai_confidence": 95.2,
            "ai_heatmap": [
                {
                    "text": "The quick brown fox jumps over the lazy dog.",
                    "ai_likelihood": 15.4
                },
                {
                    "text": "This is a simple pangram containing every letter of the English alphabet.",
                    "ai_likelihood": 8.2
                },
                {
                    "text": "In typography, design, and typesetting, this text is often used to demonstrate layout and letterforms.",
                    "ai_likelihood": 4.5
                }
            ],
            "stylometry": {
                "avg_sentence_length": 12.0,
                "vocabulary_richness": 0.82,
                "stopword_density": 0.38,
                "punctuation_density": 0.08
            },
            "perplexity": {
                "burstiness": 8.5,
                "word_entropy": 5.2,
                "char_entropy": 2.4,
                "perplexity_proxy": 32.1,
                "duplicate_bigram_ratio": 0.02,
                "duplicate_trigram_ratio": 0.00
            },
            "created_at": datetime.datetime.utcnow() - datetime.timedelta(days=1)
        },
        {
            "user_id": ObjectId(demo_id),
            "text_excerpt": "We present a novel approach to unsupervised learning by constructing a dynamic graph representation. This technique leverages graph neural networks to compute embeddings that are invariant to scaling and rotational transforms. Our experiments demonstrate superior classification accuracy compared to standard baseline architectures.",
            "plagiarism_score": 0.0,
            "matches": [],
            "highlighted_sentences": [
                {
                    "text": "We present a novel approach to unsupervised learning by constructing a dynamic graph representation.",
                    "similarity": 18.2,
                    "category": "unique",
                    "source_url": None
                },
                {
                    "text": "This technique leverages graph neural networks to compute embeddings that are invariant to scaling and rotational transforms.",
                    "similarity": 22.4,
                    "category": "unique",
                    "source_url": None
                },
                {
                    "text": "Our experiments demonstrate superior classification accuracy compared to standard baseline architectures.",
                    "similarity": 15.0,
                    "category": "unique",
                    "source_url": None
                }
            ],
            "ai_generated": False,
            "ai_confidence": 88.5,
            "ai_heatmap": [
                {
                    "text": "We present a novel approach to unsupervised learning by constructing a dynamic graph representation.",
                    "ai_likelihood": 12.5
                },
                {
                    "text": "This technique leverages graph neural networks to compute embeddings that are invariant to scaling and rotational transforms.",
                    "ai_likelihood": 14.8
                },
                {
                    "text": "Our experiments demonstrate superior classification accuracy compared to standard baseline architectures.",
                    "ai_likelihood": 7.2
                }
            ],
            "stylometry": {
                "avg_sentence_length": 18.0,
                "vocabulary_richness": 0.90,
                "stopword_density": 0.35,
                "punctuation_density": 0.04
            },
            "perplexity": {
                "burstiness": 12.4,
                "word_entropy": 5.6,
                "char_entropy": 2.5,
                "perplexity_proxy": 45.2,
                "duplicate_bigram_ratio": 0.01,
                "duplicate_trigram_ratio": 0.00
            },
            "created_at": datetime.datetime.utcnow()
        }
    ]
    
    db.scans.insert_many(sample_scans)
    print("Successfully seeded 3 sample scan records.")
    print("Database seeding completed successfully.")

if __name__ == '__main__':
    seed_db()
