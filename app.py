import os
from flask import Flask, request
from markitdown import MarkItDown

# Safe fallback for Python-native OCR
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

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
            if EASYOCR_AVAILABLE:
                print("Routing image through native EasyOCR engine...")
                # Initialize the reader for English text
                reader = easyocr.Reader(['en'], gpu=False)
                # Extract text lines from the temporary file path
                results = reader.readtext(temp_filename, detail=0)
                
                # Clean up the temp workspace file
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                
                # Join sentences back with line breaks
                extracted_text = "\n".join(results)
                
                if extracted_text.strip():
                    return extracted_text, 200
                else:
                    return "OCR complete: No readable characters detected in this image.", 200
            else:
                return "Error: EasyOCR engine failed to initialize.", 500

        # --- ROUTE B: STRUCTURAL TEXT FILES (.xml, .json, .txt) ---
        if filename.endswith(('.xml', '.json', '.txt')):
            print("Routing raw text structure directly to code wrapper...")
            text_content = request.data.decode('utf-8', errors='ignore')
            
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                
            file_extension = filename.split('.')[-1]
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
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)
        return f"Internal Server Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
