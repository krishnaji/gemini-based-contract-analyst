import os
from flask import Flask,request
from flask_cors import CORS
from google.cloud import storage
from gemini import answer
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BUCKET_NAME = os.environ.get("BUCKET_NAME")
PROJECT_ID = os.environ.get("PROJECT_ID")

# GCS client
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.get_bucket(BUCKET_NAME)

def process_files(provisions_file_content,contract_file_path):
    """
    Process the two files
    """
    response =  answer(provisions_file_content,contract_file_path)
    return response

@app.route('/', methods=['POST'])
def process_gcs_files():
    """
    Process the GCS files
    """
    data = request.get_json()
    logger.info(f"Data: {data}")
    provisions_file = data.get("provisions_file")
    contract_file = data.get("contract_file")
    logger.info(f"provisions file: {provisions_file}")
    logger.info(f"contract file: {contract_file}")

    if not provisions_file or not contract_file:
        return "Please provide both the files", 400
    try:
        provisions_file_blob = bucket.blob(provisions_file)
        provisions_file_content = provisions_file_blob.download_as_text()
        logger.info(f"provisions_file_content: {provisions_file_content}")
        
        result = process_files(provisions_file_content,contract_file)
        
        result_blob = bucket.blob(f"processed_{provisions_file}_{contract_file}.txt")
        result_blob.upload_from_string(result)

        return f"Files processed sucessfully.Result: processed_{provisions_file}_{contract_file}.txt",200
    except Exception as e:
        logger.error(f"Error processig file:{str(e)}")
        return f"Error processig file:{str(e)}",500
    
if __name__ == "__main__":
        app.run(debug=True,host="0.0.0.0",port=int(os.environ.get("PORT",8080)))