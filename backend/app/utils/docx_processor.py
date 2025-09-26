import json
import os
from docx import Document
import pdfplumber
import openpyxl
import re

class DocxProcessor:
    def __init__(self, data_folder):
        self.data_folder = data_folder

    def convert_to_docx(self, file_path):
        """Convert pdf/excel to docx if needed"""

        ext = os.path.splitext(file_path)[1].lower()
        new_path = file_path

        if ext == ".pdf":
            new_path = file_path.replace(".pdf", ".docx")
            doc = Document()
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        doc.add_paragraph(text)
                    
            doc.save(new_path)

        elif ext in [".xls", ".xlsx"]:
            new_path = file_path.replace(ext, ".docx")
            doc = Document()
            wb = openpyxl.load_workbook(file_path)
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                doc.add_paragraph(f"== {sheet} ==")
                for row in ws.iter_rows(values_only=True):
                    row_text = " | ".join([str(cell) if cell else "" for cell in row])
                    doc.add_paragraph(row_text)
            doc.save(new_path)

        return new_path

    def extract_table_text(self, doc):
        tables_text = []
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    tables_text.append(row_text)
        return tables_text

    def iter_block_items(self, parent):
        from docx.oxml import CT_P, CT_Tbl
        from docx.text.paragraph import Paragraph
        from docx.table import Table

        for child in parent.element.body:
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)


    def chunk_faq(self, doc_path, file_title):
        doc = Document(doc_path)
        chunks = []
        intro = []
        current_qa = []
        in_question = False

        def process_table(table):
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    if in_question:
                        current_qa.append(row_text)
                    else:
                        intro.append(row_text)

        for block in self.iter_block_items(doc):
            if block.__class__.__name__ == "Paragraph":
                text = block.text.strip()
                if not text:
                    continue

                if text.endswith("?") or text.endswith("؟"):
                    if intro:
                        chunks.append(f"{file_title}: {' '.join(intro)}")
                        intro = []

                    if current_qa:
                        chunks.append(f"{file_title}: {' '.join(current_qa)}")
                        current_qa = []

                    current_qa.append(text + "\n")
                    in_question = True
                else:
                    if in_question:
                        current_qa.append(text)
                    else:
                        intro.append(text)

            elif block.__class__.__name__ == "Table":
                process_table(block)

        if current_qa:
            chunks.append(f"{file_title}: {' '.join(current_qa)}")
        if intro:
            chunks.append(f"{file_title}: {' '.join(intro)}")

        return chunks


    def chunk_offers(self, doc_path, file_title):
        doc = Document(doc_path)
        chunks = []
        buffer = []
        absorb_rest = False
        last_was_heading = False

        def is_tarifs_title(text: str) -> bool:
            tarif_keywords = ["tarifs", "الأسعار", "تسعيرة", "pricing", "prices"]
            return any(keyword in text.lower() for keyword in tarif_keywords)

        def get_heading_level(text, para):
            if not text:
                return (False, 0)

            style = (para.style.name or "").lower() if para.style else ""
            if "heading 1" in style or "titre 1" in style or "title" in style:
                return (True, 1)
            if "heading" in style or "titre" in style:
                return (True, 2)

            # Check for large blue text
            has_large_blue_text = False
            for run in para.runs:
                # check font size (>= 18pt)
                if run.font.size and run.font.size.pt >= 18:
                    # check for blue color 
                    is_blue = False

                    
                    if (run.font.color and run.font.color.rgb):
                        r, g, b = run.font.color.rgb
                        if b > max(r, g) + 50:  
                            is_blue = True

                    # Theme color blue (common blue theme colors: 4=accent1, 5=accent2, 9=accent6)
                    elif (run.font.color and run.font.color.theme_color and 
                          run.font.color.theme_color in [4, 5, 9]):
                        is_blue = True

                    # Named color (some implementations)
                    elif (run.font.color and hasattr(run.font.color, 'value') and 
                          'blue' in str(run.font.color.value).lower()):
                        is_blue = True

                    if is_blue:
                        has_large_blue_text = True
                        break
                    
            if has_large_blue_text:
                return (True, 1)

            return (False, 0)

        def process_table(table):
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    buffer.append(row_text)

        for block in self.iter_block_items(doc):
            if block.__class__.__name__ == "Paragraph":
                text = block.text.strip()
                if not text:
                    continue
            
                # If line is "Tarifs", absorb the rest into one chunk
                if absorb_rest:
                    buffer.append(text)
                    continue
            
                # Check if this is a "Tarifs" section
                if is_tarifs_title(text):
                    if buffer:
                        chunks.append(f"{file_title}: {' '.join(buffer).strip()}")
                    buffer = [text]
                    absorb_rest = True 
                    continue
                
                is_heading, level = get_heading_level(text, block)

                if is_heading:
                    if not last_was_heading and buffer:  
                        chunks.append(f"{file_title}: {' '.join(buffer).strip()}")
                        buffer = []
                    buffer.append(text)
                    last_was_heading = True
                else:
                    if last_was_heading and buffer: 
                        buffer.append(text)
                    else:
                    
                        buffer.append(text)
                    last_was_heading = False
        
            elif block.__class__.__name__ == "Table":
                process_table(block)

        if buffer:
            chunks.append(f"{file_title}: {' '.join(buffer).strip()}")

        return chunks
    

    def auto_chunk(self, doc_path, file_title):
        text = " ".join([p.text for p in Document(doc_path).paragraphs])
        if text.count("?") + text.count("؟") >= 2:
            return self.chunk_faq(doc_path, file_title)
        else:
            return self.chunk_offers(doc_path, file_title)


    def process_all(self):
        """Process all files in folder and save as JSON"""
        all_chunks = []
        for file in os.listdir(self.data_folder):
            file_path = os.path.join(self.data_folder, file)
            if not os.path.isfile(file_path):
                continue

            file_title = os.path.splitext(file)[0]  

            docx_path = self.convert_to_docx(file_path) if not file.endswith(".docx") else file_path
            chunks = self.auto_chunk(docx_path, file_title)
            all_chunks.extend(chunks)

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        folder_path = os.path.join(BASE_DIR, "data")

        save_path = os.path.join(folder_path, "rag_chunks.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)

        return all_chunks
