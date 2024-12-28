import nbformat


# Path to your Google Cloud credentials JSON


# Path to Jupyter Notebook (.ipynb) file
# Google Docs formatting constants
def get_code_format():
    return {
        'backgroundColor': {
            'color': {
                'rgbColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            }
        },
        'bold': True,
        'weightedFontFamily': {
            'fontFamily': 'Courier New'
        }
    }

def get_text_format():
    return {
        'weightedFontFamily': {
            'fontFamily': 'Arial'
        },
        'fontSize': {'magnitude': 12, 'unit': 'PT'}
    }

# Read content from .ipynb file
def read_ipynb(ipynb_file):
    with open(ipynb_file, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)
    return notebook['cells']
def markdown_to_google_doc_req(cell,index):
    requests = []
    # Add markdown text as paragraphs
    for line in cell['source'].split('\n'):
        requests.append({
            'insertText': {
                'location': {'index': index},
                'text': line + '\n'
            }
        })
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': index, 'endIndex': index + len(line) + 1},
                'textStyle': get_text_format(),
                'fields': 'weightedFontFamily.fontFamily,fontSize'
            }
        })
        index += len(line) + 1
    return requests, index

def code_to_google_doc_req(cell,index):
    requests = []
    # Add code cells as formatted code blocks
    for line in cell['source'].split('\n'):
        requests.append({
            'insertText': {
                'location': {'index': index},
                'text': line + '\n'
            }
        })
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': index, 'endIndex': index + len(line) + 1},
                'textStyle': get_code_format(),
                'fields': 'backgroundColor,bold,weightedFontFamily.fontFamily'
            }
        })
        index += len(line) + 1
    return requests, index
# Write to Google Doc
def ipynb_to_google_doc_req(cells):
    requests = []
    index = 1

    for cell in cells:
        if cell['cell_type'] == 'markdown':
            # Add markdown text as paragraphs
            reqs, index = markdown_to_google_doc_req(cell, index)
            requests.extend(reqs)
        elif cell['cell_type'] == 'code':
            # Add code cells as formatted code blocks
            reqs, index = code_to_google_doc_req(cell, index)
            requests.extend(reqs)
    return requests

