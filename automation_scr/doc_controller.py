from google.oauth2.service_account import Credentials
import ipynp_to_doc_conv as converter
import warnings
# Path to your Google Cloud credentials JSON
SERVICE_ACCOUNT_FILE = '/home/huthayfa/Downloads/docs-auto-bzu-qc-00204c59092e.json'

from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/documents']


def authenticate():

    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    return creds


# Step 1: Create Google Doc
def create_google_doc(title):
    creds = authenticate()
    docs_service = build('docs', 'v1', credentials=creds)

    document = docs_service.documents().create(body={'title': title}).execute()
    print(f'Document created: {document.get("title")}, ID: {document.get("documentId")}')

    return document.get('documentId')


# Step 2: Write "Hello World" to Google Doc
def write_to_doc(doc_id, requests):
    creds = authenticate()
    docs_service = build('docs', 'v1', credentials=creds)

    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()
    print('Text written to document.')


# Step 3: Move File to Specific Folder
def move_to_folder(file_id, folder_id):
    creds = authenticate()
    drive_service = build('drive', 'v3', credentials=creds)

    file = drive_service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))

    drive_service.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()

    print(f'File {file_id} moved to folder {folder_id}')


# Main Execution
if __name__ == '__main__':

    translated_ipynb = '../translations/ar/ch-demos/hello-qiskit.ipynb'
    orig_ipynb = '../notebooks/ch-demos/hello-qiskit.ipynb'
    doc_name = orig_ipynb.replace('../', '').replace('/', ' - ').replace('.ipynb', '').replace('-', ' ').title()

    folder_id = '1rNGCufAP6mF9uUWxbPnMT2cm4UTme08q'  # Replace with your folder ID
    trans_cells=converter.read_ipynb(translated_ipynb)
    orig_cells=converter.read_ipynb(orig_ipynb)
    # Check if the number of cells in the original and translated notebooks are the same
    print(f'Number of cells in original notebook: {len(orig_cells)}')
    print(f'Number of cells in translated notebook: {len(trans_cells)}')
    if len(trans_cells) != len(orig_cells):
        # warn user
        warnings.warn(f'Number of cells in original and translated notebooks do not match. Skipping...')

    reqs = converter.ipynb_trans_orig_to_google_doc_req(orig_cells,trans_cells)
    # Create Doc and Write to it
    doc_id = create_google_doc(doc_name)
    move_to_folder(doc_id, folder_id)

    write_to_doc(doc_id, reqs)

