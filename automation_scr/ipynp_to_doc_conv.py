import nbformat
from bs4 import BeautifulSoup

# Path to your Google Cloud credentials JSON
formats = {
    'code': {
                'backgroundColor': {
                    'color': {
                        'rgbColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                    }
                },
                'bold': True,
                'weightedFontFamily': {
                    'fontFamily': 'Courier New'
                }
            },
    'text': {
                'weightedFontFamily': {
                    'fontFamily': 'Arial'
                },
                'fontSize': {'magnitude': 12, 'unit': 'PT'}
            },
    'flag': {
                'foregroundColor': {
                    'color': {
                        'rgbColor': {'red': 0.6, 'green': 0.6, 'blue': 0.6}  # Light gray
                    }
                },
                'italic': True,
                'fontSize': {
                    'magnitude': 10,
                    'unit': 'PT'
                }
            },
    'heading': lambda level: {
            'bold': True,
            'fontSize': {
                'magnitude': {1: 24, 2: 20, 3: 18, 4: 16}.get(level, 14),  # Default to 14 if level > 4
                'unit': 'PT'
            }
        }
    }

# Read content from .ipynb file
def read_ipynb(ipynb_file):
    with open(ipynb_file, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)
    return notebook['cells']

def add_flag_to_google_doc_req(flag_name,index):
    requests = [{
        'insertText': {
            'location': {'index': index},
            'text': f'[{flag_name}]\n'
        }
    }, {
        'updateTextStyle': {
            'range': {
                'startIndex': index,
                'endIndex': index + len(flag_name) + 2 + 1
            },
            'textStyle': formats['flag'],
            'fields': 'foregroundColor,italic,fontSize'
        }

    },{
        'updateParagraphStyle': {
            'range': {
                'startIndex': index,
                'endIndex': index + len(flag_name) + 2 + 1
            },
            'paragraphStyle': {
                'alignment': 'CENTER'
            },
            'fields': 'alignment'
        }
    }]

    # Add the flag for cell type
    # Style the flag
    index += len(flag_name) + 2 + 1  # Move index after flag

    return requests, index

def markdown_to_google_doc_req(cell,index):
    requests = []
    # Add markdown text as paragraphs
    rtl = False
    for line in cell['source'].split('\n'):
        if line == '<div dir="rtl">':
            rtl = True
            continue

        __format= formats['text']
        __fields='weightedFontFamily.fontFamily,fontSize'
        # check if html
        if line.strip().startswith('<'):
            soup = BeautifulSoup(line, 'html.parser').find()
            if soup:
                heading_levels = {'h1': 1, 'h2': 2, 'h3': 3, 'h4': 4}
                level = heading_levels.get(str(soup.name), 4)
                line = soup.text.strip()
                __format = formats['heading'](level)
                __fields = 'fontSize,bold'
        if line.strip().startswith('#'):
            level = len(line) - len(line.lstrip('#'))  # Count the number of #
            line = line.lstrip('#').strip()  # Remove # and leading spaces
            __format = formats['heading'](level)
            __fields='fontSize,bold'
        requests.append({
            'insertText': {
                'location': {'index': index},
                'text': line + '\n'
            }
        })
        # Apply heading style
        requests.append({
            'updateTextStyle': {
                'range': {
                    'startIndex': index,
                    'endIndex': index + len(line) + 1
                },
                'textStyle': __format,
                'fields': __fields
            }
        })
        if rtl :
            requests.append({
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': index,
                        'endIndex': index + len(line) + 1  # Adjust based on text length
                    },
                    'paragraphStyle': {
                        'direction': 'RIGHT_TO_LEFT'
                    },
                    'fields': 'direction'
                }
            })

        index += len(line) + 1
    return requests, index

def add_code_line_to_google_doc_req(line,index):
    requests = [{
        'insertText': {
            'location': {'index': index},
            'text': line + '\n'
        }
    }, {
        'updateTextStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(line) + 1},
            'textStyle': formats['code'],
            'fields': 'backgroundColor,bold,weightedFontFamily.fontFamily'
        }
    }]
    index += len(line) + 1
    return requests, index


def compare_code_to_google_doc_req(cell_o,cell_t,index):
    requests = []
    o_lines = cell_o['source'].split('\n')
    t_lines = cell_t['source'].split('\n')
    start_index = index
    for line_idx in range(len(o_lines)):
        if o_lines[line_idx] == t_lines[line_idx]:
            reqs, index = add_code_line_to_google_doc_req(o_lines[line_idx],index)
            requests.extend(reqs)
        else:
            reqs, index = add_code_line_to_google_doc_req(o_lines[line_idx],index)
            requests.extend(reqs)
            reqs, index = add_flag_to_google_doc_req('Updated line',index)
            requests.extend(reqs)
            reqs, index = add_code_line_to_google_doc_req(t_lines[line_idx],index)
            requests.extend(reqs)
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': start_index, 'endIndex': index-1},
            'paragraphStyle': {
                'indentStart': {
                    'magnitude': 20,  # Indent size in points
                    'unit': 'PT'
                },
                'spaceAbove': {
                    'magnitude': 10,  # Space before the code block
                    'unit': 'PT'
                },
                'spaceBelow': {
                    'magnitude': 10,  # Space after the code block
                    'unit': 'PT'
                }
            },
            'fields': 'indentStart,spaceAbove,spaceBelow'
        }
    })
    return requests, index

# Write to Google Doc
def ipynb_trans_orig_to_google_doc_req(o_cells,t_cells):
    requests = []
    index = 1

    for cell_idx in range(len(o_cells)):
        if o_cells[cell_idx]['cell_type'] == 'markdown':
            for lang in ['Original','Translated']:
                cell = o_cells[cell_idx] if lang == 'Original' else t_cells[cell_idx]
                # Add flag for cell type
                reqs, index = add_flag_to_google_doc_req(lang, index)
                requests.extend(reqs)
                reqs, index = markdown_to_google_doc_req(cell, index)
                requests.extend(reqs)

        elif o_cells[cell_idx]['cell_type'] == 'code':
            # Add code cells as formatted code blocks
            reqs, index = compare_code_to_google_doc_req(o_cells[cell_idx],t_cells[cell_idx], index)
            requests.extend(reqs)
        else:
            print(f'Cell type {o_cells[cell_idx]["cell_type"]} not supported. Skipping...')
    return requests


