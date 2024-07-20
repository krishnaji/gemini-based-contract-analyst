import gradio as gr
from google.cloud import storage
import os
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your Google Cloud project ID
project_id = os.environ.get("PROJECT_ID") # "genai-380800"

# Replace with your Google Cloud Storage bucket name
bucket_name = os.environ.get("BUCKET_NAME") #"contract-analysis-app"


# Create a storage client
storage_client = storage.Client(project=project_id)
# Get the bucket
bucket = storage_client.bucket(bucket_name)
def upload_files(file1, file2):
  """Uploads two files to a Google Cloud Storage bucket."""

  success_messages =[]
  uploaded_files = []
  for file in [file1,file2]:
    if file is not None:
      blob = bucket.blob(os.path.basename(file.name))
      blob.upload_from_filename(file.name)
      success_messages.append(f"Sucessfully uploaded {file.name}")
      uploaded_files.append(os.path.basename(file.name))
    else:
      success_messages.append("No file uploaded")
  if len(uploaded_files) == 2:
    cloud_run_url = "http://127.0.0.1:8080"
    payload = {
       "provisions_file": uploaded_files[0],
       "contract_file": uploaded_files[1]
    }
    logger.info(f"payload: {payload}")
    try:
       response= requests.post(cloud_run_url,json=payload)
       if response.status_code == 200:
          success_messages.append(f"Files processed Successfully:{response.text}")
       else:
          success_messages.append(f"Error processing files:{response.text}")
    except Exception as e:
       success_messages.append(f"Error processing files:{e}")

  return "\n".join(success_messages)

def list_txt_files():
  """List all .txt files in GCS bucket"""
  blobs = bucket.list_blobs()
  return [blob.name for blob in blobs if blob.name.endswith(".txt")]

def read_file_contnet(filename):
  """Read and return the content of a selected file"""
  if not filename:
        return "No File selected"
  blob = bucket.blob(filename)
  return blob.download_as_text()

def update_output(filename):
   """Update the output with the content of the selected file"""
   return read_file_contnet(filename)
 
def refresh_file_list(dummy):
   return gr.Dropdown(choices= list_txt_files())


with gr.Blocks(theme=gr.themes.Soft()) as demo:
  gr.Markdown("""
              # Contract Analyst
              """)
  gr.Markdown("----------------------")
  with gr.Row():
        with gr.Column():
            file1 = gr.File(label="Upload Provisions",scale=0)
            file2 = gr.File(label="Upload Contract PDF file",scale=0)
            upload_button = gr.Button("Upload Files")
        with gr.Column():
            file_list = gr.Dropdown(choices=list_txt_files(), label="Select a file to view", interactive=True)
            refresh_button = gr.Button("Refresh")

  output = gr.Textbox(label="Output", lines=10)
  # output = gr.Markdown(label="Output")
  dummy = gr.Textbox(visible=False)

  upload_button.click(upload_files, inputs=[file1, file2], outputs=output)
  file_list.change(update_output, inputs=[file_list], outputs=output)
  refresh_button.click(refresh_file_list, inputs=[dummy],outputs=[file_list])

demo.launch()   