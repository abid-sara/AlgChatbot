import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from services.intent_service import IntentClassificationService


CSV_PATH = "../data/intent_data.csv"   # of the form: sentence, label

if __name__ == "__main__":
    
    df = pd.read_csv(CSV_PATH)
    sentences = df["sentence"].tolist()
    labels = df["label"].tolist()

    # Train and save model
    service = IntentClassificationService()
    service.train(sentences, labels)
    print("Training complete. Model saved to models/intent_model.pkl")
