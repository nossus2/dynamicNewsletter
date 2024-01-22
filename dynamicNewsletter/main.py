import os.path
import streamlit as st
import json

import calendar
from datetime import date

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

# The ID of a sample document.
DOCUMENT_ID = "1oEEf-uRK7eQyb6YL5_xNEXgKGKGOgMZlyXBLrBwhzlM"

def todaysDate():
    d = date.today()
    x = calendar.day_name[d.weekday()]
    return str(d) + " " + str(x)

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def read_paragraph_element(element):
    """Reads a ParagraphElement to return text with Markdown formatting."""
    text_content = ""
    text_run = element.get('textRun')
    if text_run:
        text = text_run.get('content')
        textStyle = text_run.get('textStyle', {})

        # Format text
        formatted_text = text.strip()
        if textStyle.get('bold'):
            formatted_text = f"**{formatted_text}**"
        if textStyle.get('italic'):
            formatted_text = f"*{formatted_text}*"

        # Handle links
        if 'link' in textStyle:
            url = textStyle['link'].get('url')
            formatted_text = f"[{formatted_text}]({url})"

        text_content += formatted_text

    return text_content

def process_structural_elements(elements):
    """Processes Structural Elements to return structured data for Streamlit display."""
    content_data = []
    current_section = {"heading": None, "content": ""}
    in_list = False
    list_type = None

    for element in elements:
        if 'paragraph' in element:
            paragraph = element['paragraph']
            paragraph_elements = paragraph['elements']
            paragraph_style = paragraph.get('paragraphStyle', {}).get('namedStyleType', 'NORMAL_TEXT')

            paragraph_text = ''.join([read_paragraph_element(elem) for elem in paragraph_elements])

            # Check for heading style
            if paragraph_style.startswith('HEADING'):
                # Save the current section and start a new one
                if current_section["content"].strip():
                    content_data.append(current_section)
                current_section = {"heading": paragraph_text.strip(), "content": ""}
            else:
                # Append paragraph text to the current section content
                current_section["content"] += paragraph_text + "\n"

    # Add the last section
    if current_section["content"].strip():
        content_data.append(current_section)

    return content_data

def display_content_in_streamlit(content_data):
    """Displays content in Streamlit with collapsible sections for headings."""
    local_css("style.css")
    for section in content_data:
        if section["heading"]:
            with st.expander(section["heading"]):
                st.markdown(section["content"])
        else:
            st.markdown(section["content"])


def main():
  """Shows basic usage of the Docs API.
  Prints the title of a sample document.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("docs", "v1", credentials=creds)

    # Retrieve the documents contents from the Docs service.
    document = service.documents().get(documentId=DOCUMENT_ID).execute()

    out_file = open("out_file.json", "w")
    json.dump(document, out_file, indent=4, sort_keys=True)
    out_file.close()

    # Assuming 'document' is your Google Docs JSON response
    with open("out_file.json") as json_file:
        json_data = json.load(json_file)
        body = json_data.get('body')
        if body:
            content = process_structural_elements(body.get('content'))
            st.set_page_config(page_title="Weekly Faculty Newsletter", layout="wide")
            st.title("IMS Faculty Newsletter: " + todaysDate())
            display_content_in_streamlit(content)
        else:
            print("No content found.")

  except HttpError as err:
    print(err)


if __name__ == "__main__":
  main()