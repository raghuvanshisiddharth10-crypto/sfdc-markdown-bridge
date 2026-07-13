import os
from flask import Flask, request
from flask_cors import CORS  # Ensure flask-cors is in your requirements.txt
from markitdown import MarkItDown

try:
    import pytesseract
    from PIL import Image as PILImage
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

app = Flask(__name__)

# --- CONFIGURE CORS POLICY FOR SALESFORCE ORG ---
CORS(app, resources={
    r"/*": {
        "origins": ["https://sidd-idp2-dev-ed.trailblaze.lightning.force.com"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-File-Name"]
    }
})

@app.route('/convert', methods=['POST', 'OPTIONS'])
def convert():
    # Instantly intercept and pass the browser's preflight check
    if request.method == 'OPTIONS':
        return '', 200

    try:
        filename = request.headers.get('X-File-Name', 'document.pdf').lower()
        print(f"Processing inbound request for file: {filename}")

        if not request.data:
            return "Empty request body", 400

        temp_filename = f"temp_{filename}"
        with open(temp_filename, "wb") as f:
            f.write(request.data)

        # --- ROUTE A: IMAGE FILES ---
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            if TESSERACT_AVAILABLE:
                print("Routing image through Docker-optimized Tesseract engine...")
                extracted_text = pytesseract.image_to_string(PILImage.open(temp_filename))
                
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                
                return extracted_text if extracted_text.strip() else "OCR complete: No readable text found.", 200
            else:
                return "Error: Tesseract not available inside Docker container.", 500

        # --- ROUTE B: STRUCTURAL FILES ---
        if filename.endswith(('.xml', '.json', '.txt')):
            text_content = request.data.decode('utf-8', errors='ignore')
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            return f"```{filename.split('.')[-1]}\n{text_content}\n```", 200

        # --- ROUTE C: STANDARD DOCUMENTS ---
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
