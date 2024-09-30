from __future__ import print_function
import pickle
import os.path
import io
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate_with_credential(credential_path):
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credential_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)
    return service

def list_files(service, page_size=1000):
    results = service.files().list(
        pageSize=page_size, fields="nextPageToken, files(id, name, mimeType)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for i, item in enumerate(items):
            print(f"{i}. {item['name']} ({item['id']}) (MimeType: {item['mimeType']})")
    return items

def download_file(service, file_id, output_path):
    # Check if the file is a Google Doc, Sheet, Slides, etc.
    file_metadata = service.files().get(fileId=file_id, fields='mimeType').execute()
    mime_type = file_metadata['mimeType']

    if mime_type in ['application/vnd.google-apps.document', 'application/vnd.google-apps.spreadsheet',
                     'application/vnd.google-apps.presentation']:
        # Export Google Docs, Sheets, Slides to a downloadable format
        if mime_type == 'application/vnd.google-apps.document':
            export_mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            extension = '.docx'
        elif mime_type == 'application/vnd.google-apps.spreadsheet':
            export_mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            extension = '.xlsx'
        elif mime_type == 'application/vnd.google-apps.presentation':
            export_mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            extension = '.pptx'

        request = service.files().export_media(fileId=file_id, mimeType=export_mime_type)
        output_path += extension  # Add the appropriate extension
    else:
        # Download regular files
        request = service.files().get_media(fileId=file_id)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))

    with open(output_path, 'wb') as f:
        f.write(fh.getvalue())
    print(f"File with ID {file_id} downloaded to {output_path} successfully.")

if __name__ == '__main__':
    service = authenticate_with_credential('credential_old.json')
    items = list_files(service)

    if items:
        while True:
            file_index = input("Enter the index of the file to download (or 'q' to quit): ")
            if file_index.lower() == 'q':
                break

            try:
                file_index = int(file_index)
                if 0 <= file_index < len(items):
                    file_id = items[file_index]['id']
                    file_name = items[file_index]['name']
                    output_path = f"{file_name}"  # Use the original file name
                    download_file(service, file_id, output_path)
                else:
                    print("Invalid index. Please enter a valid index.")
            except ValueError:
                print("Invalid input. Please enter a number or 'q'.")