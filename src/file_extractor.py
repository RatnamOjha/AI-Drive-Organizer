# # Extracts text from all file types
# import io
# from PyPDF2 import PdfReader
# from docx import Document
# from PIL import Image
# import pytesseract
# import pdfplumber

# def extract_text_from_file(service, file):
#     """Extract text from Google Drive file"""
#     file_id = file['id']
#     mime_type = file['mimeType']
#     name = file['name']
    
#     try:
#         if mime_type == 'application/vnd.google-apps.document':
#             request = service.files().export_media(fileId=file_id, mimeType='text/plain')
#             return request.execute().decode('utf-8')
            
#         elif mime_type == 'application/pdf':
#             request = service.files().get_media(fileId=file_id)
#             pdf_data = request.execute()
#             # Try pdfplumber first (better for tables)
#             with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
#                 text = "\n".join(page.extract_text() or "" for page in pdf.pages)
#             return text
            
#         elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
#             request = service.files().get_media(fileId=file_id)
#             doc_data = request.execute()
#             doc = Document(io.BytesIO(doc_data))
#             return "\n".join(para.text for para in doc.paragraphs)
            
#         elif mime_type.startswith('image/'):
#             request = service.files().get_media(fileId=file_id)
#             img_data = request.execute()
#             img = Image.open(io.BytesIO(img_data))
#             return pytesseract.image_to_string(img)
            
#         else:
#             return name  # Fallback to filename
            
#     except Exception as e:
#         print(f"⚠️ Extraction failed for {name}: {str(e)}")
#         return name
    
# src/file_extractor.py
import io
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract
import pdfplumber
from googleapiclient.http import MediaIoBaseDownload

def extract_text_from_file(service, file):
    """Extract text from supported file types. Skip video/audio."""
    file_id = file['id']
    mime_type = file['mimeType']
    name = file['name']
    
    try:
        # --- GOOGLE DOCS ---
        if mime_type == 'application/vnd.google-apps.document':
            request = service.files().export_media(fileId=file_id, mimeType='text/plain')
            return request.execute().decode('utf-8')
            
        # --- GOOGLE SHEETS ---
        elif mime_type == 'application/vnd.google-apps.spreadsheet':
            request = service.files().export_media(fileId=file_id, mimeType='text/csv')
            return request.execute().decode('utf-8')
            
        # --- PLAIN TEXT ---
        elif mime_type == 'text/plain':
            request = service.files().get_media(fileId=file_id)
            return request.execute().decode('utf-8')
            
        # --- PDF ---
        elif mime_type == 'application/pdf':
            request = service.files().get_media(fileId=file_id)
            pdf_data = request.execute()
            with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            return text
            
        # --- DOCX ---
        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            request = service.files().get_media(fileId=file_id)
            doc_data = request.execute()
            doc = Document(io.BytesIO(doc_data))
            return "\n".join(para.text for para in doc.paragraphs)
        
        # --- IMAGES (OCR) ---
        elif mime_type.startswith('image/'):
            request = service.files().get_media(fileId=file_id)
            img_data = request.execute()
            img = Image.open(io.BytesIO(img_data))
            return pytesseract.image_to_string(img)
        
        # --- UNSUPPORTED FILES (e.g., .mov, .zip, .exe) ---
        else:
            return name  # Fallback to filename for classification
            
    except Exception as e:
        print(f"⚠️ Extraction failed for {name}: {str(e)}")
        return name