from __future__ import print_function
import os.path
import sys
import argparse
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate():
    """Authenticate the user and return the Drive service."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error creating Drive service: {e}")
        sys.exit(1)

def is_google_file(mime_type):
    """Determine if the file is a Google Workspace file."""
    return mime_type.startswith('application/vnd.google-apps.')

def transfer_ownership(service, file_id, new_owner_email):
    """Transfer ownership of a single file."""
    try:
        # First, add the new owner as an editor
        permission = {
            'type': 'user',
            'role': 'owner',
            'emailAddress': new_owner_email
        }
        service.permissions().create(
            fileId=file_id,
            body=permission,
            transferOwnership=True,
            fields='id',
            sendNotificationEmail=True  # Set to False to disable email
        ).execute()
        print(f"Ownership transferred successfully for file ID: {file_id}")
    except HttpError as error:
        print(f"An error occurred while transferring ownership for file ID {file_id}: {error}")
        return False
    return True

def list_files_in_folder(service, folder_id):
    """List all files in the specified folder."""
    query = f"'{folder_id}' in parents and trashed = false"
    try:
        results = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        items = results.get('files', [])
        return items
    except HttpError as error:
        print(f"An error occurred while listing files: {error}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Transfer ownership of Google Drive files in a folder.')
    parser.add_argument('folder_id', help='The ID of the Google Drive folder.')
    parser.add_argument('new_owner_email', help='The email address of the new owner.')
    args = parser.parse_args()

    service = authenticate()

    folder_id = args.folder_id
    new_owner_email = args.new_owner_email

    files = list_files_in_folder(service, folder_id)

    if not files:
        print('No files found in the specified folder.')
        return

    print(f"Found {len(files)} files in the folder. Processing...")

    failed_transfers = []

    for file in files:
        file_id = file['id']
        file_name = file['name']
        mime_type = file['mimeType']
        if is_google_file(mime_type):
            print(f"Transferring ownership for Google file: {file_name} (ID: {file_id})")
            success = transfer_ownership(service, file_id, new_owner_email)
            if not success:
                failed_transfers.append(file_name)
        else:
            print(f"Skipping non-Google file: {file_name} (ID: {file_id}) - Ownership transfer not supported.")

    if failed_transfers:
        print("\nThe following files could not have their ownership transferred:")
        for fname in failed_transfers:
            print(f"- {fname}")
    else:
        print("\nOwnership transfer completed successfully for all eligible files.")

if __name__ == '__main__':
    main()