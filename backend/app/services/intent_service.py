import joblib
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

class IntentClassifierSDC:
    def __init__(self, model_path="../dev/models/intent_model.pkl"):
        self.embedder = SentenceTransformer("intfloat/multilingual-e5-base", trust_remote_code=True)
        self.model_path = model_path
 

        self.label_encoder, self.signatures, self.train_mean, self.train_std = None, None, None, None
         

        try:
            self.signatures, self.label_encoder, self.train_mean, self.train_std = joblib.load(self.model_path)
            print("Loaded existing intent classifier")
        except FileNotFoundError:
            print("No pre-trained classifier found. Run dev/training_intent.py first")
    

    def embed(self, text):
        return self.embedder.encode(text, normalize_embeddings=True)


    def train(self, sentences, labels):
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(labels)
        X = self.embed(sentences)

        # split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

        # normalize per dimension using training stats
        self.train_mean, self.train_std = X_train.mean(0), X_train.std(0)
        X_train = (X_train - self.train_mean) / self.train_std
        X_test = (X_test - self.train_mean) / self.train_std

        # compute signatures
        signatures = {}
        for idx, cls in enumerate(label_encoder.classes_):
            class_embeddings = X_train[y_train == idx]
            signatures[cls] = class_embeddings.mean(0)

        self.signatures, self.label_encoder = signatures, label_encoder
        print("SDC signatures built for:", list(signatures.keys()))

        # evaluate on test set
        y_pred = []
        for emb in X_test:
            scores = {cls: emb @ sig for cls, sig in signatures.items()}
            pred_cls = max(scores, key=scores.get)
            y_pred.append(pred_cls)

        y_pred = label_encoder.transform(y_pred)

        print("Accuracy:", accuracy_score(y_test, y_pred))
        print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
        joblib.dump((self.label_encoder, self.signatures, self.train_mean, self.train_std), self.model_path)
        

    def predict(self, query: str):
        embedding = self.embed([query])[0]
       
        # normalize using training mean & std
        embedding = (embedding - self.train_mean) / self.train_std
        scores = {cls: embedding @ sig for cls, sig in self.signatures.items()}
        return max(scores, key=scores.get)
       