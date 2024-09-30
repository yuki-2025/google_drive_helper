import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_gdrive_service(credentials_file, token_file):
    creds = None
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def list_files_in_folder(service, folder_id):
    results = service.files().list(
        q=f"'{folder_id}' in parents",
        fields="nextPageToken, files(id, name, owners, permissions)"
    ).execute()
    return results.get('files', [])


def accept_permissions(service, file_id):
    try:
        # List the permissions for the file
        permissions = service.permissions().list(fileId=file_id).execute()

        for permission in permissions.get('permissions', []):
            if permission['role'] == 'owner' and permission['type'] == 'user':
                if 'pendingOwner' in permission and permission['pendingOwner']:
                    # Accept ownership transfer (rest of the code remains the same)
                    if permission['role'] == 'owner' and permission['type'] == 'user' and permission['pendingOwner']: 
                        # Accept ownership transfer 
                        service.permissions().update(
                            fileId=file_id,
                            permissionId=permission['id'],
                            body={'role': 'owner'},  # Set the role to owner explicitly
                            transferOwnership=True   # Important: Include transferOwnership
                        ).execute()
                        print(f"Ownership transfer accepted for file ID: {file_id}")
                        return True
                    else:
                        print(f"No pending ownership transfer found for permission ID: {permission['id']}")

        print(f"No pending ownership transfers found for file ID: {file_id}")
        return False
    except Exception as e:
        print(f"An error occurred while accepting permissions for file ID {file_id}: {str(e)}")
        return False

def main():
    print("Authenticating new account (yukileong001@gmail.com)...")
    service_new = get_gdrive_service('credential_new.json', 'token_new.pickle')
    
    folder_id = input("Enter the Google Drive folder ID: ")
    
    print("\nListing shared files and accepting permissions:")
    shared_files = list_files_in_folder(service_new, folder_id)
    
    if not shared_files:
        print(f"No files found for the new account in the folder: {folder_id}")
    else:
        print(f"Files shared with 'yukileong001@gmail.com':")
        for file in shared_files:
            print(f"\nFile: {file['name']} ({file['id']})")
            if accept_permissions(service_new, file['id']):
                print("Permissions accepted.")
            else:
                print("No pending permissions or failed to accept.")

if __name__ == '__main__':
    main()