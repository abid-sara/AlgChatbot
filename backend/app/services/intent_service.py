from sentence_transformers import SentenceTransformer
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
import joblib

class IntentClassificationService:
    def __init__(self, model_path = "../dev/models/intent_model.pkl"):
        self.embedder = SentenceTransformer("jinaai/jina-embeddings-v3", trust_remote_code=True)
        self.model_path = model_path

        try:
            self.classifier, self.label_encoder = joblib.load(self.model_path)
            print("loaded existing intent classifier")
        except FileNotFoundError:
            self.classifier, self.label_encoder = None, None
            print("No pre-trained classifier found. Run dev/train_intent.py first")
        

    def embed(self, text):
        return self.embedder.encode(text)
    

    def train(self, sentences, labels):
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(labels)
        X = self.embed(sentences)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        rfClassifier = DecisionTreeClassifier()
        rfClassifier.fit(X_train, y_train)

        # Prediction & evaluation
        y_pred = rfClassifier.predict(X_test)
        print("Accuracy:", accuracy_score(y_test, y_pred))
        print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

        # save model + encoder
        joblib.dump((rfClassifier, label_encoder), self.model_path)
        print(f"Model saved to {self.model_path}")

        self.classifier, self.label_encoder = rfClassifier, label_encoder


    def predict(self, query: str):
        if self.classifier is None:
            raise RuntimeError("Classifier not trained. Please run dev/train_intent.py first.")

        embedding = self.embed([query])
        predection = self.classifier.predict(embedding)
        return self.label_encoder.inverse_transform(predection)[0]
