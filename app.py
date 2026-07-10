import os
from flask import Flask, request
from markitdown import MarkItDown

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        # Get filename from headers
        filename = request.headers.get('X-File-Name', 'document.pdf')
        print(f"--- INCOMING REQUEST ---")
        print(f"Filename detected: {filename}")
        print(f"Body size: {len(request.data)} bytes")

        # Check if we actually got data
        if not request.data:
            print("ERROR: Request data body is completely empty!")
            return "Empty request body", 400

        # Save the incoming binary blob to a temporary file locally on Render
        temp_filename = f"temp_{filename}"
        with open(temp_filename, "wb") as f:
            f.write(request.data)
        
        print(f"Temporary file written successfully: {temp_filename}")

        # Run MarkItDown on the temporary file
        md = MarkItDown()
        result = md.convert(temp_filename)
        
        # Clean up the file after processing
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            print("Temporary file cleaned up.")

        print("SUCCESS: Conversion completed perfectly!")
        return result.text_content, 200

    except Exception as e:
        # CRITICAL: This will force Render to show us the error text!
        print(f"!!! CRITICAL PYTHON CRASH !!!: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return f"Internal Error: {str(e)}", 500
