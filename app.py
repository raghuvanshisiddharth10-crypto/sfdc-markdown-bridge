from flask import Flask, request, jsonify
from markitdown import MarkItDown
import os

app = Flask(__name__)
md = MarkItDown()

# This route accepts the incoming file stream from Salesforce
@app.route('/convert', methods=['POST'])
def convert_file():
    # 1. Grab the original filename from the Salesforce header
    filename = request.headers.get('X-File-Name', 'document.pdf')
    _, ext = os.path.splitext(filename)
    
    try:
        # 2. Read the raw binary file data sent by Salesforce Apex
        file_bytes = request.get_data()
        
        if not file_bytes:
            return jsonify({"error": "No file data received"}), 400
            
        # 3. Use Microsoft MarkItDown to convert the binary stream
        result = md.convert_stream(file_bytes, file_extension=ext)
        
        # 4. Return the raw Markdown string back to Salesforce
        return result.text_content, 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Start the server locally on port 5000
    app.run(host='0.0.0.0', port=5000)