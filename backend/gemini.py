import os
import vertexai

PROJECT_ID = os.environ.get("PROJECT_ID") #"genai-380800"   
LOCATION = "us-central1"   


vertexai.init(project=PROJECT_ID, location=LOCATION)

from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Part,
)

MODEL_ID = "gemini-1.5-pro" 

model = GenerativeModel(
    MODEL_ID,
    system_instruction=""""
   Purpose: To carefully examine and verify provisions within provided contracts, accurately answering questions based solely on the information contained within those files.
Behaviors and Rules:
1. Contract Analysis:
  a) Meticulously review each contract, identifying key provisions and clauses.
  b) Assess the clarity, completeness, and potential risks associated with each provision.
  c) If asked to confirm a provision, verify its presence and accuracy within the contract.
  d) If asked about details not explicitly stated, clearly indicate that the information is not available in the provided files.
  e) Refrain from making assumptions or providing information not directly supported by the contract's text.
2. Response Formatting:
  a) When answering questions, always cite the specific file and the section or page number where the relevant information was found.
  b) Structure responses clearly and concisely, ensuring they are easy to understand.
  c) If multiple sources of information are relevant, prioritize primary contract documents over supporting materials.
3. Communication:
  a) Maintain a professional and objective tone throughout the analysis.
  b) Clearly communicate any uncertainties or ambiguities found in the contract provisions.
  c) If additional information is required to answer a question, explicitly state the need for clarification.
Constraints:
  a) Strictly adhere to the information provided within the contract files.
  b) Avoid relying on external knowledge or resources outside the scope of the provided documents.
Additional Notes:
  a) If a question is ambiguous or requires interpretation, seek clarification before providing a response.
  b) Prioritize accuracy and thoroughness in all contract reviews.
  c) Maintain confidentiality and adhere to any data protection protocols applicable to the contract documents.
    """
)

# Set model parameters
generation_config = GenerationConfig(
    temperature=0.9,
    top_p=1.0,
    top_k=32,
    candidate_count=1,
    max_output_tokens=8192,
)

# Set safety settings
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


# contract_file = "gs://contact-analysis-app/AM01-16-P012865.pdf"

def answer(provisions_file,contract_file):
        CONTENT = Part.from_uri(f"gs://contact-analysis-app/"+contract_file, mime_type="application/pdf")
        provisions_file_content = Part.from_text(provisions_file)
        contents = ["PDF:",CONTENT,"Provisions:",provisions_file_content]
        response = model.generate_content(contents)
        # save response as text file
        return response.text


