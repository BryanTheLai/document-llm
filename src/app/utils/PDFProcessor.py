# utils.py
import pymupdf
import json

class PDFProcessor:
    def pdf_to_text(self, pdf_file_path): # Correct instance method definition with 'self'
        """
        Extracts text content from a PDF file.

        Args:
            pdf_file_path (str): The path to the PDF file.

        Returns:
            str: The extracted text content from the PDF, or None if an error occurs.
        """
        text = ""
        try:
            doc = pymupdf.open(pdf_file_path)
            for page in doc:
                text += page.get_text()
            result = text.strip()
            if len(result) < 5:
                raise ValueError("No text content found in the PDF. PDF might be full of images.")
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None