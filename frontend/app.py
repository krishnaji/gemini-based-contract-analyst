import gradio as gr
from google.cloud import storage
import os
import requests
import logging
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel, Content, Part

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your Google Cloud project ID
project_id = os.environ.get("PROJECT_ID") # "genai-380800"

aiplatform.init(project=project_id, location="us-central1")

# Gemini model
model = GenerativeModel("gemini-1.5-flash-001",system_instruction="""
You will analyze any order forms, master agreements, service agreements, or similar documents provided by the user and identify any misalignment or discrepancies with previously agreed-upon terms within those agreements. You will also identify potentially risky terms or clauses. 

**Key points to keep in mind:**

* **Confidentiality and Discretion:** You will be provided with potentially sensitive legal documents. You will not share or reproduce these outside of this interaction. You will protect the user's confidential information at all times.

* **Attention to Detail:** Meticulously examine the order forms and agreements, paying close attention to details such as product names, quantities, dates, pricing, and specific terms and conditions. 

* **Legal Knowledge:** You do not need to be a legal expert. However, a basic understanding of contract terminology and common legal provisions will be helpful. 

* **Clear Communication:** Clearly articulate any inconsistencies, risks, or potential issues that you identify, ensuring that the user understands your findings.


**Process:**


1. **Document Submission:** The user will provide you with one or more order forms or agreements. The documents may be in various formats (PDF, text, image).

2. **Reference Agreement Identification:** The user will specify which agreement (master agreement, service agreement, etc.) should be used as the reference for comparison.

3. **Analysis:** You will carefully compare the order form or agreement against the reference agreement, looking for discrepancies, inconsistencies, or areas of concern.

4. **Issue Identification:** Identify any inconsistencies between the order form/agreement and the reference agreement. This includes:

    * **Price/Quantity Mismatches:**  Is the price or quantity different from what was agreed upon?

    * **Term Mismatches:** Do the terms of service or delivery differ from what was agreed upon?

    * **Payment/Renewal Issues:** Are there inconsistencies in payment terms, auto-renewal clauses, or other financial aspects?

    * **Omissions/Additions:**  Are there any key clauses missing or new terms added that were not in the original agreement?

    * **Ambiguous Language:**  Are there any vague terms that could lead to future disputes?

5. **Risk Assessment:** Identify any clauses or terms in the order form/agreement that could pose risks for the user. This includes:

    * **Liability Clauses:** Who is liable in case of disputes or damages?

    * **Warranty Limitations:** Are there any limitations on warranties or guarantees?

    * **Termination Clauses:** Under what conditions can the agreement be terminated?

    * **Dispute Resolution:** How are disputes to be handled (arbitration, court)?

6. **Report:** You will provide a clear, concise summary of your findings to the user. This will include:

    * A list of any inconsistencies or discrepancies found.

    * A summary of any potential risks identified.

    * Recommendations for further action, such as seeking legal advice or renegotiating certain terms.
""")

# chat session
chat_session = None

# Replace with your Google Cloud Storage bucket name
bucket_name = os.environ.get("BUCKET_NAME") #"contract-analysis-app"


# Create a storage client
storage_client = storage.Client(project=project_id)
# Get the bucket
bucket = storage_client.bucket(bucket_name)
# List to store uploaded file URIs
uploaded_file_uris = []
def initialize_chat():
    global chat_session
    chat_session = model.start_chat(history=[])

def upload_to_gcs(files):
    global uploaded_file_uris
    if not files:
        return "No files uploaded"
    
    new_uris = []
    for file in files:
        try:
           if file is not None:
            blob = bucket.blob(os.path.basename(file.name))
            blob.upload_from_filename(file.name)
            
            uri = f"gs://{bucket_name}/{os.path.basename(file.name)}"
            new_uris.append(uri)
            
        except Exception as e:
            return f"Error uploading file {file.name} to GCS: {str(e)}"
    
    uploaded_file_uris.extend(new_uris)
    return f"Files uploaded successfully. Total files: {len(uploaded_file_uris)}"

def chat_with_gemini(message, history):
    global chat_session, uploaded_file_uris
    if chat_session is None:
        initialize_chat()

    # Convert the history to the format expected by the Gemini SDK
    gemini_history = []
    for human, assistant in history:
        gemini_history.append(Content(role="user", parts=[Part.from_text(human)]))
        if assistant:
            gemini_history.append(Content(role="model", parts=[Part.from_text(assistant)]))

    # Update the chat session with the new history
    chat_session = model.start_chat(history=gemini_history)

    # Prepare the content for the new user message
    new_message_parts = []

    # Add all uploaded files to the message
    for uri in uploaded_file_uris:
        file_part = Part.from_uri(uri, mime_type="application/pdf")
        new_message_parts.append(file_part)
    
    if uploaded_file_uris:
        new_message_parts.append(Part.from_text("Please consider the uploaded documents in your response."))
        # uploaded_file_uris = []  # Reset after use

    new_message_parts.append(Part.from_text(message))

    print(new_message_parts)
    # Send the new message and get the response
    response = chat_session.send_message(new_message_parts)


    # Return the response text
    return response.text

def bot(message, history):
    bot_message = chat_with_gemini(message, history)
    history.append((message, bot_message))
    print(history)
    print("--*--")
    return "", history

def clear_files():
    global uploaded_file_uris
    uploaded_file_uris = []
    return "All uploaded files cleared."

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
  
  with gr.Tabs():
     with gr.TabItem("Review Contract"):
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
     with gr.TabItem("Chat Assistant"):
        with gr.Row():
          with gr.Column(scale=2):
              file_upload = gr.File(label="Upload PDF Files", file_count="multiple")
              upload_button = gr.Button("Upload Files")
              clear_files_button = gr.Button("Clear Uploaded Files")
              upload_status = gr.Textbox(label="Upload Status")
          
          with gr.Column(scale=3):
              chatbot = gr.Chatbot()
              msg = gr.Textbox()
              clear = gr.Button("Clear Chat")
        upload_button.click(upload_to_gcs, inputs=[file_upload], outputs=[upload_status])
        clear_files_button.click(clear_files, outputs=[upload_status])
        msg.submit(bot, [msg, chatbot], [msg, chatbot])
        clear.click(lambda: None, None, chatbot, queue=False)
demo.launch()   