import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.docx_processor import DocxProcessor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
folder_path = os.path.join(BASE_DIR, "data", "rag")

processor = DocxProcessor(folder_path)

processor.process_all()

print("Finished processing the docx")

