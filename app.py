import os
from flask import Flask, request
from markitdown import MarkItDown

# Safe fallback imports for image text extraction (OCR)
try:
    import pytesseract
    from PIL import Image as PILImage
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        # 1. Grab the file extension header sent dynamically from Apex
        filename = request.headers.get('X-File-Name', 'document.pdf').lower()
        print(f"Processing inbound request for file: {filename}")

        if not request.data:
            print("Error: Request body contains 0 bytes.")
            return "Empty request body", 400

        # 2. Write the incoming binary stream into a temporary workspace file
        temp_filename = f"temp_{filename}"
        with open(temp_filename, "wb") as f:
            f.write(request.data)

        # --- ROUTE A: IMAGE FILES (.png, .jpg, .jpeg) ---
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            if TESSERACT_AVAILABLE:
                print("Routing image through local Tesseract OCR engine...")
                extracted_text = pytesseract.image_to_string(PILImage.open(temp_filename))
                
                # Clean up the file
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                
                if extracted_text.strip():
                    return extracted_text, 200
                else:
                    return "OCR complete: No readable text characters detected in this image.", 200
            else:
                return "Error: Image OCR tools are missing on the hosting server.", 500

        # --- ROUTE B: STRUCTURAL TEXT FILES (.xml, .json, .txt) ---
        if filename.endswith(('.xml', '.json', '.txt')):
            print("Routing raw text structure directly to code wrapper...")
            text_content = request.data.decode('utf-8', errors='ignore')
            
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                
            file_extension = filename.split('.')[-1]
            # Wrap the plain code inside a markdown code block for clean layout syntax
            return f"```{file_extension}\n{text_content}\n```", 200

        # --- ROUTE C: STANDARD DOCUMENTS (.pdf, .docx, .xlsx, .pptx) ---
        print("Routing standard document matrix through Microsoft MarkItDown...")
        md = MarkItDown()
        result = md.convert(temp_filename)
        
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

        return result.text_content, 200

    except Exception as e:
        print(f"!!! CRITICAL PYTHON CRASH !!!: {str(e)}")
        # Clean up temp file if a crash occurs mid-execution
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)
        return f"Internal Server Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
