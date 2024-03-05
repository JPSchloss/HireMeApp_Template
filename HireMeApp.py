# This is needed to ensure ChromaDB works properly when deployed. 
import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# import os
# import dotenv

import streamlit as st
from bs4 import BeautifulSoup
import requests
from PIL import Image

from langchain_openai import OpenAIEmbeddings 
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

from helper_functions import load_pdf, split_text_documents, text_to_doc_splitter

# Load environment variables - Use This For Testing Purposes
# dotenv.load_dotenv()
# openai_api_key = os.environ.get("OPENAI_API_KEY")

# Retrieve the OpenAI API key from the environment variable - Use This For Streamlit Deployment
openai_api_key = st.secrets["OPENAI_API_KEY"]

model = "gpt-3.5-turbo-0125"

similarity_query = """ 
                WRITE YOUR QUERY HERE FOR THE ROLE SIMILARITY TOOL. 

                This query is up to you but it should reference a resume and a job posting. The 
                framework for those other elements are still in this app, but you need to write 
                your own queries to communicate with the model. The original query was highly 
                personalized for Jonathan Schlosser. 
                 """

# Function To Load The Streamlit Page MArkdown Files
def load_markdown_file(markdown_file):
    with open(markdown_file, "r", encoding="utf-8") as file:
        return file.read()
    
# Function To Pull The Text From LinkedIn URL. 
def extract_text_from_url(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, features="html.parser")
    text = []
    for lines in soup.findAll('div', {'class': 'description__text'}):
        text.append(lines.get_text())
    
    lines = (line.strip() for line in text)
    text = '\n'.join(line for line in lines if line)

    document = text_to_doc_splitter(text)

    return document

# Role Similarity Tool Functions
def job_similarity_query(job_pdf):
    try:
        job_doc = load_pdf(job_pdf)
        job_dic = job_doc[0].dict()
        job_string = job_dic['page_content']

        res_doc = pdf_doc[0].dict()
        res_string = res_doc['page_content']
        
        query = similarity_query + job_string + "\n RESUME: \n" + res_string
        result = llm.invoke(query)

        return result.content
    
    except:
        st.write("PDF Document Did Not Load Correctly. Please Try Again.")
        pass


def linkedin_similarity_query(job_url):
    try:
        job_post = extract_text_from_url(job_url)
        job_dic = job_post[0].dict()
        job_string = job_dic['page_content']
    
        res_doc = pdf_doc[0].dict()
        res_string = res_doc['page_content']
        
        query = similarity_query + job_string + "\n RESUME: \n" + res_string
        result = llm.invoke(query)

        return result.content
    
    except:
        st.write("LinkedIn Job Posting Did Not Load Correctly. Please Try Again.")
        pass


# Define the avatar file paths (adjust paths as needed)
user_avatar = 'User_Icon.png'
assistant_avatar = 'Icon.png'

# Initialize or load your PDF here.
pdf_path = "Schlosser_Resume_Full.pdf"

# Load and process the PDF
pdf_doc = load_pdf(pdf_path)
documents = split_text_documents(pdf_doc)

# Build The Chatbot Chain
vectordb = Chroma.from_documents(documents, embedding=OpenAIEmbeddings(openai_api_key=openai_api_key))
llm = ChatOpenAI(temperature=0.3, model_name=model, openai_api_key=openai_api_key)
pdf_qa = RetrievalQA.from_chain_type(llm, retriever=vectordb.as_retriever(search_kwargs={'k': 4}), chain_type="stuff")

# Add in Streamlit Sidebar Navigation
st.sidebar.title(":blue[Navigation]")
page = st.sidebar.radio("Navigation", ("Intro", "Resume", "Sample Projects", "Experience Chatbot", "Role Similarity Tool"), 
                        label_visibility = 'hidden')

# Build Intro Page For Streamlit App
if page == "Intro":
    st.title("YOUR INTRO TITLE HERE")
    # st.image(Image.open('LINK TO IMAGE'))
    intro_content = load_markdown_file("intro.md")
    st.markdown(intro_content, unsafe_allow_html=True)

# Build Resume Page For Streamlit App
elif page == "Resume":
    st.title("YOUR NAME HERE")
    resume_content = load_markdown_file("resume.md")
    st.markdown(resume_content, unsafe_allow_html=True)

elif page == "Sample Projects":
    st.title("Sample Projects")
    project_content = load_markdown_file("sample_projects.md")
    st.markdown(project_content, unsafe_allow_html=True)


elif page == "Experience Chatbot":
    st.title("Experience Chatbot")
    st.markdown("""
    Welcome to the Experience Chatbot! This is a unique tool designed to bridge the gap between recruiters' 
    questions and the depth of a candidate's qualifications. 
    
    Please feel free to give it a go! 
    """)

    with st.expander(":red[Disclaimer]"):
        st.markdown("""
        Please note that while this chatbot is designed to provide as accurate and insightful responses as possible based 
        on my experiences and qualifications, it operates within the constraints of an LLM model. As such, 
        there may be limitations to its understanding and interpretation of complex queries, and the potential 
        for inaccuracies cannot be entirely ruled out.

        The chatbot's responses are generated based on predefined data and algorithms inherent to LLMs, which 
        means it may not always capture the full nuance or context of professional experiences and qualifications. 
        It's a powerful tool for initial exploration and engagement, but it should not be the sole basis for 
        decisions regarding fit or qualifications.

        For detailed discussions or clarifications beyond the chatbot's scope, I encourage you to reach out and connect. 
        
        This application is used at your own risk and its accuracy is not gauranteed. Please proceed with caution. 
        """)
    
    # Check for session state initialization for messages
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Chat interface
    if prompt := st.chat_input("What would you like to know?"):
        # Immediately display the user's question in the UI
        st.session_state["messages"].append({"role": "user", "content": prompt, "avatar": user_avatar})
        for message in st.session_state["messages"]:
            with st.chat_message(message["role"], avatar=message["avatar"]):
                st.markdown(message["content"])

        # Clear previous messages to avoid redisplaying them after the loop
        temp_messages = st.session_state["messages"].copy()
        st.session_state["messages"].clear()
        
        # Add only the last user's message to ensure it's displayed properly without duplicates
        st.session_state["messages"].append(temp_messages[-1])
        
        # Show a spinner while processing the response
        with st.spinner('Thinking...'):
            result = pdf_qa.invoke(prompt) 
            result = result['result'] 
            
        # Display the assistant's response
        st.session_state["messages"].append({"role": "assistant", "content": result, "avatar": assistant_avatar})
        with st.chat_message("assistant", avatar=assistant_avatar):
            st.markdown(result)

elif page == "Role Similarity Tool":
    st.title("Role Similarity Tool")
    st.markdown("""
    Welcome to the Role Similarity Tool. This feature allows you to upload a PDF file of the job description or a LinkedIn link to the 
    job posting to explore how my qualifications may align with the requirements of a particular role. It's designed 
    to highlight aspects of my experience that might be relevant to your decision-making process.
    """)

    with st.expander(":red[Disclaimer]"):
        st.markdown("""
        Please note, the Role Similarity Tool is built on OpenAI ChatGPT models that, despite their 
        sophistication, cannot perfectly capture the nuances of every professional experience or job 
        description. Misinterpretations can occur, and the tool's assessment may not always reflect 
        the full spectrum of a an individuals capabilities or the intricacies of a job's requirements.

        It's a starting point for understanding potential alignments and should ideally complement, 
        not replace, comprehensive review processes, including direct discussions and interviews. 
                    
        Also, please note that the LinkedIn job posting pull is utilizing some fairly basic webscraping approaches. 
        This can result in some things being passed incorrectly to the model. If this happens the model may present an 
        odd answer. This is okay and is expected based on the simplicity of the approach taken. IF this challenge persists, 
        try passing the posting as a PDF instead. 
                    
        Lastly, please use this tool with caution. Any information shared here will be passed to ChatGPT models. 
        Therefore, please do not share any confidential or non-public information in this tool. And be advised that any use of 
        this tool is at your own risk and should be used with caution. 
                    
        Your understanding and consideration of these limitations are appreciated.
        """)

    with st.form('my_form'):
        job_pdf = st.file_uploader("Upload files", type=["pdf"], accept_multiple_files=False)
        job_text = st.text_area('Enter LinkedIn Job URL:')
        
        submitted = st.form_submit_button('Submit')

        if submitted:
            with st.spinner('Thinking...'):
                if job_pdf != None:
                    result = job_similarity_query(job_pdf)
                elif (job_text != '') and (job_pdf == None):
                    result = linkedin_similarity_query(job_text)
            if result == None:
                pass
            else:
                st.write(result)
        
