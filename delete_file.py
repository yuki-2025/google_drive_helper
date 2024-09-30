from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

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
        pageSize=page_size, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
    return items

def delete_files(service, file_ids):
    for file_id in file_ids:
        try:
            service.files().delete(fileId=file_id).execute()
            print(f"File with ID {file_id} deleted successfully.")
        except Exception as e:
            print(f"Failed to delete file with ID {file_id}: {e}")

if __name__ == '__main__':
    service = authenticate_with_credential('credential_old.json')
    items = list_files(service)

    if items:
        while True:
            action = input("Select an action: (1) Delete specific files, (2) Delete all files, (q) Quit: ")

            if action.lower() == 'q':
                break

            if action == '1':
                file_ids_to_delete = []
                while True:
                    file_index = input("Enter the index of the file to delete (or 'q' to quit): ")
                    if file_index.lower() == 'q':
                        break
                    try:
                        file_index = int(file_index)
                        if 0 <= file_index < len(items):
                            file_ids_to_delete.append(items[file_index]['id'])
                        else:
                            print("Invalid index. Please enter a valid index.")
                    except ValueError:
                        print("Invalid input. Please enter a number or 'q'.")

                if file_ids_to_delete:
                    confirm = input(f"Are you sure you want to delete these files: {', '.join([items[i]['name'] for i in range(len(items)) if items[i]['id'] in file_ids_to_delete])}? (y/n) ")
                    if confirm.lower() == 'y':
                        delete_files(service, file_ids_to_delete)
                    else:
                        print("Deletion cancelled.")

            elif action == '2':
                confirm = input(f"Are you sure you want to delete ALL files? (y/n) ")
                if confirm.lower() == 'y':
                    delete_files(service, [item['id'] for item in items])
                else:
                        print("Deletion cancelled.")

            else:
                print("Invalid action. Please select 1, 2, or q.")