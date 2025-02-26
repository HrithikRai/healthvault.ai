import os
import shutil
import tomli
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from PIL import Image
from agno.agent import Agent
from agno.models.google import Gemini
import streamlit as st
from agno.tools.duckduckgo import DuckDuckGoTools
from chromadb import PersistentClient

google_api_key = 'AIzaSyBsyYp75IoJzbCcWSdAHSfhaqfvHUARFjY'

image_analysis_query = """

You are a highly skilled medical imaging expert with extensive knowledge in 
radiology and diagnostic imaging. Analyze the patient's medical image and 
structure your response as follows:

### 0. Medical Report Type

- Only mention the imaging modality or the type of report

### 1. Image Type & Region

- Specify imaging modality (X-ray/MRI/CT/Ultrasound/etc.)
- Identify the patient's anatomical region and positioning
- Comment on image quality and technical adequacy

### 2. Key Findings

- List primary observations systematically
- Note any abnormalities in the patient's imaging with precise descriptions
- Include measurements and densities where relevant
- Describe location, size, shape, and characteristics
- Rate severity: Normal/Mild/Moderate/Severe

### 3. Diagnostic Assessment

- Provide primary diagnosis with confidence level
- List differential diagnoses in order of likelihood
- Support each diagnosis with observed evidence from the patient's imaging
- Note any critical or urgent findings

### 4. Patient-Friendly Explanation

- Explain the findings in simple, clear language that the patient can understand
- Avoid medical jargon or provide clear definitions
- Include visual analogies if helpful
- Address common patient concerns related to these findings

### 5. Research Context

IMPORTANT: Use the DuckDuckGo search tool to:
- Find recent medical literature about similar cases
- Search for standard treatment protocols
- Provide a list of relevant medical links of them too
- Research any relevant technological advances
- Include 2-3 key references to support your analysis

### 6. Recommendations & Next Steps

- Suggest additional tests or imaging if needed for further clarification.
- Recommend possible treatment approaches based on the observed findings.
- Indicate whether follow-up imaging or specialist consultation is necessary.

Format your response using clear markdown headers and bullet points. Be concise yet thorough.
"""

video_analysis_query = """

You are a highly skilled medical imaging expert with extensive knowledge in 
radiology, diagnostic imaging, and video-based medical assessments. Analyze 
the provided medical video (e.g., ultrasonography, endoscopy, echocardiography, MRI sequences) 
and structure your response as follows:

### 0. Medical Report Type

- Only mention the imaging modality or the type of report

### 1. Video Type & Examination Context

- Specify the imaging modality (Ultrasound/MRI/CT/Endoscopy/Echocardiography/etc.).
- Identify the anatomical region being examined and the purpose of the imaging study.
- Assess video quality: resolution, clarity, frame rate, and any artifacts affecting interpretation.
- Comment on patient positioning and probe/transducer movement (if applicable).

### 2. Key Observations (Frame-by-Frame or Dynamic)

- Summarize key findings based on sequential frames and overall motion.
- Identify any structural abnormalities, lesions, fluid accumulations, masses, or dynamic changes.
- Describe organ/tissue movement patterns, blood flow (Doppler findings), and functional anomalies.
- If applicable, include measurements of structures (e.g., cardiac chamber dimensions, Doppler velocities).

### 3. Diagnostic Assessment

- Provide a primary diagnosis with a confidence level based on video analysis.
- List differential diagnoses in order of likelihood.
- Support each diagnosis with observed evidence from the video.
- Highlight critical findings that may require urgent medical attention.

### 4. Patient-Friendly Explanation

- Explain findings in simple, clear language that a non-specialist can understand.
- Use layman's terms to describe motion patterns, abnormalities, and potential implications.
- Provide relatable analogies or comparisons (e.g., "The heart valve is not opening fully, similar to a stiff door hinge").
- Address common patient concerns related to these findings.

### 5. Research Context

IMPORTANT: Use the DuckDuckGo search tool to:
- Find recent medical literature about similar cases involving video-based imaging.
- Search for updated clinical guidelines and best practices for interpreting such videos.
- Provide links to relevant research papers or trusted medical sources.
- If applicable, include insights from AI-based video analysis advancements in medical imaging.

### 6. Recommendations & Next Steps

- Suggest additional tests or imaging if needed for further clarification.
- Recommend possible treatment approaches based on the observed findings.
- Indicate whether follow-up imaging or specialist consultation is necessary.

Format your response using clear markdown headers and bullet points. Ensure precision, clarity, and conciseness while maintaining a thorough analysis.
"""

text_analysis_query = """

You are a highly skilled medical expert with extensive knowledge in 
clinical diagnostics and textual medical report analysis. Analyze the patient's medical report 
and structure your response as follows:

### 0. Medical Report Type

- Only mention the imaging modality or the type of report

### 1. Report Overview

- Identify the type of report (Radiology, Pathology, Lab, Clinical Summary, etc.)
- Summarize the main components of the report
- Comment on clarity, completeness, and any missing details

### 2. Key Findings

- Extract primary clinical observations
- Note any significant abnormal results with precise descriptions
- List measurements, lab values, and critical thresholds if applicable
- Identify severity: Normal/Mild/Moderate/Severe

### 3. Diagnostic Assessment

- Provide primary diagnosis with confidence level
- List differential diagnoses in order of likelihood
- Support each diagnosis with evidence from the report
- Note any critical or urgent findings requiring immediate attention

### 4. Patient-Friendly Explanation

- Explain findings in simple, clear language that the patient can understand
- Avoid medical jargon or provide clear definitions
- Use visual analogies where helpful
- Address common patient concerns related to these findings

### 5. Research Context

IMPORTANT: Use the DuckDuckGo search tool to:
- Find recent medical literature about similar cases
- Search for standard treatment protocols
- Provide a list of relevant medical links
- Research any recent technological advances
- Include 2-3 key references to support your analysis

### 6. Recommendations & Next Steps

- Suggest additional tests or imaging if needed for further clarification.
- Recommend possible treatment approaches based on the observed findings.
- Indicate whether follow-up imaging or specialist consultation is necessary.

Format your response using clear markdown headers and bullet points. Be concise yet thorough.
"""



import mimetypes
import shutil
import re
current_user = "patient1"

reports_directory = f"../uploads/{current_user}/reports"

def get_medical_report_type(analysis_text):
    # Regex pattern to capture report type after "### 0. Medical Report Type"
    match = re.search(r"### 0\. Medical Report Type\s*-\s*(.+)", analysis_text)
    
    if match:
        return match.group(1).strip()  # Extract and return the report type
    return "Unknown Report Type"

def get_file_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    
    if mime_type:
        if mime_type.startswith("text") or mime_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            return "text", text_analysis_query
        elif mime_type.startswith("image"):
            return "image", image_analysis_query
        elif mime_type.startswith("video"):
            return "video", video_analysis_query
    return "unknown"

# Function to send file to Agno agent and get response
def analyze_file_with_agno_agent(file_path,query):
    medical_agent = Agent(
    model=Gemini(
        api_key=google_api_key,
        id="gemini-2.0-flash-exp"
    ),
    tools=[DuckDuckGoTools()],
    markdown=True
) 
    response = medical_agent.run(query,videos=[{"filepath": file_path}])
    return response.content


def append_to_doc(file_type, response_text, log_file=f"../uploads/{current_user}/{current_user}_analysis.txt"):
    report_type = get_medical_report_type(response_text)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n#{report_type}\n\n{response_text}")

# Main function
def process_files_in_directory(upload_directory):
    if not os.path.exists(upload_directory):
        print("Directory not found.")
        return
    
    for file in os.listdir(upload_directory):
        file_path = os.path.join(upload_directory, file)
        
        if os.path.isfile(file_path):
            file_type, query_type = get_file_type(file_path)
            response = analyze_file_with_agno_agent(file_path,query_type)
            append_to_doc(file_type, response)
            print(f"Processed: {file}, filetype - ({file_type})")
            new_file_path = os.path.join(reports_directory, file)
            shutil.move(file_path, new_file_path)

# Example usage: Set your project directory

