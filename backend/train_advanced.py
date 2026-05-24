import os
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from app.ml.stylometry import get_stylometry_vector
from app.ml.perplexity_analyzer import analyze_perplexity_and_burstiness

# Mock/Synthetic Dataset generator
# Human: variable sentence length, high burstiness, personal pronouns, rich vocabulary, irregular transitions.
# AI: highly structured, introductory/concluding filler phrases, consistent passive voice, uniform sentence length.
HUMAN_SAMPLES = [
    "I remember going to my local park when I was just a little kid, feeling the wind in my face, and running as fast as my legs could carry me. The playground was always bustling, yet somehow peaceful.",
    "This research paper evaluates the biochemical pathways underlying mitochondrial dysfunction. We specifically look at how enzymatic activity drops over time, leading to cellular degradation.",
    "Well, honestly, I don't think it's as simple as they make it sound. Every business has its own quirks, its own hidden costs, and ignoring those will lead you straight to bankruptcy. Trust me on this.",
    "In the early morning mist, the ancient stone temple stood silent. Vines wrapped around its crumbling pillars, a testament to the passage of centuries and the fading memories of a forgotten empire.",
    "We need to completely rethink our approach to urban architecture. Modern buildings are cold, concrete blocks devoid of soul, ignoring the psychological need for green space and natural sunlight.",
    "I was cooking dinner—spaghetti, of all things—when the phone rang. It was my sister, crying. In that single moment, the entire trajectory of my summer completely shifted. I packed my bags that night.",
    "The experimental results, though preliminary, strongly suggest a correlation. However, several confounding variables—such as temperature fluctuations and variations in sample purity—must be addressed in future trials.",
    "Hey! If you are reading this, stop scrolling. Go outside. Take a deep breath of fresh air. Your screen will still be here when you get back, but this beautiful sunset won't last forever.",
    "To build a truly democratic society, we must prioritize local community engagement. Centralized authorities are too disconnected from the daily struggles of ordinary citizens to implement meaningful reforms.",
    "The band struck a loud, discordant chord. The crowd immediately went wild, pushing forward against the barricades. I was swept up in the wave of heat, sweat, and pure, raw energy."
] * 5  # Duplicate to get 50 samples

AI_SAMPLES = [
    "It is important to note that machine learning algorithms require significant computational resources. In conclusion, optimization of hyper-parameters is essential for achieving high accuracy in predictive modeling tasks.",
    "Artificial intelligence offers numerous advantages in modern healthcare systems. Firstly, it enhances diagnostic accuracy. Secondly, it automates repetitive administrative procedures, thereby increasing efficiency.",
    "In summary, the transition to renewable energy sources is a critical step toward environmental sustainability. Furthermore, governments must implement robust policies to facilitate this technological transition.",
    "To conclude, this essay has demonstrated that literature reflects societal values. By analyzing the structural elements of the novel, we can gain a deeper understanding of historical context.",
    "Additionally, it is crucial to recognize the impact of social media on adolescent psychology. Specifically, studies indicate a correlation between screen time and anxiety levels in young adults.",
    "From a holistic perspective, organizational success depends on effective communication. Consequently, managers should foster an inclusive workplace environment that encourages open dialogue.",
    "Ultimately, the integration of automation in manufacturing processes yields substantial cost reductions. Therefore, industries must adapt to these technological advancements to remain competitive.",
    "It can be argued that climate change poses an existential threat to global biodiversity. In this context, proactive conservation strategies are imperative to protect endangered ecosystems.",
    "Moreover, the implementation of blockchain technology enhances transaction transparency. In conclusion, financial institutions should explore these decentralized solutions to minimize risk.",
    "It is widely understood that digital literacy is a fundamental requirement in the modern workforce. Thus, educational institutions must update their curricula to include advanced technical training."
] * 5  # Duplicate to get 50 samples

def generate_dataset():
    texts = HUMAN_SAMPLES + AI_SAMPLES
    # 0 = Human, 1 = AI
    labels = [0] * len(HUMAN_SAMPLES) + [1] * len(AI_SAMPLES)
    return texts, labels

def train():
    print("Generating synthetic training dataset...")
    texts, labels = generate_dataset()
    
    # 1. Fit TF-IDF Vectorizer
    print("Fitting TF-IDF Vectorizer...")
    vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
    vectorizer.fit(texts)
    
    # 2. Extract Hybrid Features
    print("Extracting hybrid features (TF-IDF + Stylometry + Perplexity)...")
    X = []
    for text in texts:
        # Get tf-idf features
        tfidf_feats = vectorizer.transform([text]).toarray()[0]
        # Get stylometry
        sty_feats = [
            val for val in get_stylometry_vector(text)
        ]
        # Get perplexity
        perp_info = analyze_perplexity_and_burstiness(text)
        perp_feats = [
            perp_info["burstiness"],
            perp_info["word_entropy"],
            perp_info["char_entropy"],
            perp_info["perplexity_proxy"],
            perp_info["duplicate_bigram_ratio"],
            perp_info["duplicate_trigram_ratio"]
        ]
        combined = np.concatenate([tfidf_feats, sty_feats, perp_feats])
        X.append(combined)
        
    X = np.array(X)
    y = np.array(labels)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Train Logistic Regression
    print("Training Logistic Regression ensemble classifier...")
    classifier = LogisticRegression(max_iter=1000)
    classifier.fit(X_train, y_train)
    
    # 4. Evaluate
    y_pred = classifier.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nTraining Results:")
    print(f"Accuracy: {acc * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Human", "AI"]))
    
    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:")
    print(cm)
    
    # Save
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, "model.pkl")
    
    # Save both vectorizer and classifier
    joblib.dump({"vectorizer": vectorizer, "classifier": classifier}, model_path)
    print(f"\nSaved ensemble model to: {model_path}")

if __name__ == "__main__":
    train()
