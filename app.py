import os
import gc
import io
from flask import Flask, request, Response
from flask_cors import CORS  
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

# Instantiate MarkItDown globally once to avoid re-allocation memory overhead per request
md = MarkItDown()

@app.route('/convert', methods=['POST', 'OPTIONS'])
def convert():
    if request.method == 'OPTIONS':
        return '', 200

    try:
        filename = request.headers.get('X-File-Name', 'document.pdf').lower()
        file_ext = "." + filename.split('.')[-1]
        print(f"Processing inbound request for file: {filename}")

        # Stream the body directly into an in-memory byte buffer instead of request.data
        # request.stream reads the chunk sequentially, bypassing heavy string caching
        file_bytes = io.BytesIO(request.get_data(parse_form_data=False))
        
        if file_bytes.getbuffer().nbytes == 0:
            return "Empty request body", 400

        # --- ROUTE A: IMAGE FILES ---
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            if TESSERACT_AVAILABLE:
                print("Routing image through Docker-optimized Tesseract engine...")
                img = PILImage.open(file_bytes)
                extracted_text = pytesseract.image_to_string(img)
                
                # Explicit cleanup
                del img
                file_bytes.close()
                
                response_text = extracted_text if extracted_text.strip() else "OCR complete: No readable text found."
                return Response(response_text, mimetype='text/plain')
            else:
                file_bytes.close()
                return "Error: Tesseract not available inside Docker container.", 500

        # --- ROUTE B: STRUCTURAL TEXT FILES ---
        if filename.endswith(('.xml', '.json', '.txt')):
            text_content = file_bytes.getvalue().decode('utf-8', errors='ignore')
            file_bytes.close()
            return Response(f"```{filename.split('.')[-1]}\n{text_content}\n```", mimetype='text/plain')

        # --- ROUTE C: STANDARD DOCUMENTS (PDF & XLSX) ---
        print(f"Streaming document matrix through Microsoft MarkItDown using extension: {file_ext}")
        
        # We use convert_stream to parse byte-by-byte from memory instead of loading files from disk
        result = md.convert_stream(file_bytes, file_extension=file_ext)
        markdown_text = result.text_content
        
        # Explicitly destroy structural references before finishing the execution cycle
        del result
        file_bytes.close()

        return Response(markdown_text, mimetype='text/plain')

    except Exception as e:
        print(f"!!! CRITICAL PYTHON CRASH !!!: {str(e)}")
        if 'file_bytes' in locals():
            file_bytes.close()
        return f"Internal Server Error: {str(e)}", 500

    finally:
        # CRITICAL FIX FOR 256MB TIERS: Clear dangling memory addresses instantly
        # Forces Python to immediately free memory blocks back to Render
        gc.collect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
