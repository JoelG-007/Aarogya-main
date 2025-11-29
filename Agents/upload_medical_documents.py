"""
Patient Medical Document Processor
Upload and process patient medical PDFs/images using OCR
Stores extracted text by patient ID
"""

import os
import json
from datetime import datetime
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    
    # Set Tesseract path
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # Set Poppler path for pdf2image
    POPPLER_PATH = r'C:\Program Files\poppler-24.08.0\Library\bin'
except ImportError as e:
    print(f"Error: {e}")
    print("Please install required packages and Tesseract OCR")
    print("Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")


class MedicalDocumentProcessor:
    """Process and store patient medical documents."""
    
    def __init__(self, storage_dir='patient_medical_records'):
        self.storage_dir = storage_dir
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        
        self.records_file = os.path.join(storage_dir, 'document_registry.json')
        self.records = self._load_registry()
    
    def _load_registry(self):
        """Load document registry."""
        if os.path.exists(self.records_file):
            with open(self.records_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_registry(self):
        """Save document registry."""
        with open(self.records_file, 'w', encoding='utf-8') as f:
            json.dump(self.records, f, indent=2, ensure_ascii=False)
    
    def process_image(self, image_path, patient_id):
        """Process image file using OCR."""
        try:
            # Open image
            img = Image.open(image_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(img)
            
            return text.strip()
        
        except Exception as e:
            return f"Error processing image: {str(e)}"
    
    def process_pdf(self, pdf_path, patient_id):
        """Process PDF file using OCR."""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
            
            # Extract text from each page
            all_text = []
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image)
                all_text.append(f"--- Page {i+1} ---\n{text.strip()}")
            
            return "\n\n".join(all_text)
        
        except Exception as e:
            return f"Error processing PDF: {str(e)}"
    
    def upload_document(self, file_path, patient_id, document_type='medical_report'):
        """
        Upload and process a patient document.
        
        Args:
            file_path: Path to the document file
            patient_id: Patient identifier (e.g., 'Person_1')
            document_type: Type of document (e.g., 'medical_report', 'prescription', 'lab_result')
        
        Returns:
            dict with status and extracted text
        """
        if not os.path.exists(file_path):
            return {'status': 'error', 'message': 'File not found'}
        
        # Get file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        print(f"\nProcessing document for {patient_id}...")
        print(f"File: {os.path.basename(file_path)}")
        print(f"Type: {document_type}")
        
        # Process based on file type
        if ext == '.pdf':
            extracted_text = self.process_pdf(file_path, patient_id)
        elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            extracted_text = self.process_image(file_path, patient_id)
        else:
            return {'status': 'error', 'message': f'Unsupported file type: {ext}'}
        
        # Create patient directory
        patient_dir = os.path.join(self.storage_dir, patient_id)
        if not os.path.exists(patient_dir):
            os.makedirs(patient_dir)
        
        # Generate unique document ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        doc_id = f"{document_type}_{timestamp}"
        
        # Save extracted text
        text_file = os.path.join(patient_dir, f"{doc_id}.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"Patient ID: {patient_id}\n")
            f.write(f"Document Type: {document_type}\n")
            f.write(f"Upload Date: {datetime.now().isoformat()}\n")
            f.write(f"Original File: {os.path.basename(file_path)}\n")
            f.write("="*60 + "\n\n")
            f.write(extracted_text)
        
        # Update registry
        if patient_id not in self.records:
            self.records[patient_id] = []
        
        self.records[patient_id].append({
            'document_id': doc_id,
            'document_type': document_type,
            'original_file': os.path.basename(file_path),
            'upload_date': datetime.now().isoformat(),
            'text_file': text_file,
            'text_preview': extracted_text[:200] + '...' if len(extracted_text) > 200 else extracted_text
        })
        
        self._save_registry()
        
        print(f"✓ Document processed and saved")
        print(f"✓ Text file: {text_file}")
        
        return {
            'status': 'success',
            'document_id': doc_id,
            'patient_id': patient_id,
            'text_file': text_file,
            'extracted_text': extracted_text
        }
    
    def get_patient_documents(self, patient_id):
        """Get all documents for a patient."""
        return self.records.get(patient_id, [])
    
    def get_document_text(self, patient_id, document_id):
        """Get text content of a specific document."""
        patient_docs = self.records.get(patient_id, [])
        
        for doc in patient_docs:
            if doc['document_id'] == document_id:
                with open(doc['text_file'], 'r', encoding='utf-8') as f:
                    return f.read()
        
        return None
    
    def list_all_patients(self):
        """List all patients with documents."""
        return list(self.records.keys())


def simulate_upload(processor):
    """Simulate document upload (for testing without frontend)."""
    print("\n" + "="*60)
    print("MEDICAL DOCUMENT UPLOAD SYSTEM")
    print("="*60)
    
    while True:
        print("\nOptions:")
        print("1. Upload document")
        print("2. View patient documents")
        print("3. Read document")
        print("4. List all patients with documents")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            patient_id = input("Enter Patient ID (e.g., Person_1): ").strip()
            file_path = input("Enter file path (PDF or image): ").strip()
            
            doc_types = ['medical_report', 'prescription', 'lab_result', 'diagnosis', 'xray', 'scan']
            print("\nDocument types:", ', '.join(doc_types))
            doc_type = input("Enter document type: ").strip() or 'medical_report'
            
            result = processor.upload_document(file_path, patient_id, doc_type)
            
            if result['status'] == 'success':
                print(f"\n✓ Document uploaded successfully!")
                print(f"Document ID: {result['document_id']}")
                print(f"\nExtracted text preview:")
                print("-" * 60)
                preview = result['extracted_text'][:500]
                print(preview + "..." if len(result['extracted_text']) > 500 else preview)
            else:
                print(f"\n❌ Error: {result['message']}")
        
        elif choice == '2':
            patient_id = input("Enter Patient ID: ").strip()
            docs = processor.get_patient_documents(patient_id)
            
            if docs:
                print(f"\n{len(docs)} document(s) for {patient_id}:")
                for i, doc in enumerate(docs, 1):
                    print(f"\n{i}. Document ID: {doc['document_id']}")
                    print(f"   Type: {doc['document_type']}")
                    print(f"   File: {doc['original_file']}")
                    print(f"   Date: {doc['upload_date']}")
                    print(f"   Preview: {doc['text_preview']}")
            else:
                print(f"\nNo documents found for {patient_id}")
        
        elif choice == '3':
            patient_id = input("Enter Patient ID: ").strip()
            document_id = input("Enter Document ID: ").strip()
            
            text = processor.get_document_text(patient_id, document_id)
            
            if text:
                print("\n" + "="*60)
                print("DOCUMENT CONTENT")
                print("="*60)
                print(text)
            else:
                print("\n❌ Document not found")
        
        elif choice == '4':
            patients = processor.list_all_patients()
            
            if patients:
                print(f"\nPatients with documents ({len(patients)}):")
                for patient in patients:
                    doc_count = len(processor.get_patient_documents(patient))
                    print(f"  - {patient}: {doc_count} document(s)")
            else:
                print("\nNo patients with documents")
        
        elif choice == '5':
            print("\nGoodbye!")
            break
        
        else:
            print("\n❌ Invalid option")


def main():
    """Main function."""
    print("Medical Document Processor")
    print("="*60)
    
    # Check if Tesseract is installed
    try:
        pytesseract.get_tesseract_version()
        print("✓ Tesseract OCR is installed")
    except Exception:
        print("\n⚠️  WARNING: Tesseract OCR not found!")
        print("Please install Tesseract OCR:")
        print("Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("After installation, you may need to set the path:")
        print("pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'")
        print("\nContinuing anyway...")
    
    processor = MedicalDocumentProcessor()
    simulate_upload(processor)


if __name__ == "__main__":
    main()
