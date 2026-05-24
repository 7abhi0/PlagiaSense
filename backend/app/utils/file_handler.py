import os

def extract_text(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf':
        from pdfminer.high_level import extract_text as pdf_extract
        return pdf_extract(filepath)
    elif ext in ['.docx', '.doc']:
        import docx
        doc = docx.Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs])
    elif ext == '.txt':
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        raise ValueError("Unsupported file type")
