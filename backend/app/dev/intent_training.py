import sys
import os
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from services.intent_service import IntentClassifierSDC



CSV_PATH = "../../data/intent_data.csv"   # of the form: sentence, label

if __name__ == "__main__":
    
    df = pd.read_csv(CSV_PATH)
    sentences = df["sentence"].tolist()
    labels = df["label"].tolist()

    unique, counts = np.unique(labels, return_counts=True)

    for value, count in zip(unique, counts):
        print(f"Value {value} appears {count} times.")

    
    
    # Train and save model
    service = IntentClassifierSDC()
    service.train(sentences, labels)


    test_queries = [
       "What are the specific requirements for Idoom Fibre Pro 100 Mbps subscription?",
       "Je veux consulter immédiatement le détail de ma consommation data du mois en cours",
       "ما هي ميزات عرض Idoom 4G LTE Contrôle وكيف يمكنني تفعيله؟ ثم قم بالتفعيل لشريحتي",
       "Comment puis-je vérifier l'éligibilité de mon adresse pour la fibre optique?",
       "I need to report a complete internet outage in my area since this morning",
       "كيف يمكنني الحصول على خدمة البريد الإلكتروني المهني وما هي سعره؟ ثم قم بإنشاء حساب لشركتي" ,
       "What is the exact process for migrating from ADSL to VDSL technology?",
       "Signaler un problème de qualité d'appel sur ma ligne Idoom Fixe 500 DA",
       "ما هي عروض الحزم الأمنية الإلكترونية للشركات الصغيرة؟ ثم قم بحجز موعد لتدقيق أمني",
       "Je souhaite connaître les délais d'intervention pour un dérangement fibre",
       "اعطيني اخر فاتورة",
       "اعطيني اخر فاتورة ديالي",
       "اعطيني اخر فكتور ديالي"
       
    ]
    
    for query in test_queries:
        try:
            result = service.predict(query)
            print(result)
        except RuntimeError as e:
            print(f"Error: {e}")
            break
