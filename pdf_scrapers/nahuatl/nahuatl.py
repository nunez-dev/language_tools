from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTChar, LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
import re

def parse_obj(lt_objs):
    entries = []
    current_entry = None

    for obj in lt_objs:
        if isinstance(obj, LTTextBoxHorizontal):
            for text_line in obj:
                text = text_line.get_text().strip()
                if text:
                    first_char = text_line._objs[0]
                    is_bold = 'Bold' in first_char.fontname
                    contains_dot = '.' in text

                    if is_bold and contains_dot:
                        if current_entry is not None:
                            entries.append(current_entry)
                        current_entry = text
                    elif current_entry is not None and not text.isnumeric():
                        current_entry += ' ' + text

    # append the last entry
    if current_entry is not None:
        entries.append(current_entry)

    return entries

def parse_pdf(path):
    lines = []
    with open(path, 'rb') as fp:
        parser = PDFParser(fp)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        pages = PDFPage.create_pages(doc)
        for page in pages:
            interpreter.process_page(page)
            layout = device.get_result()
            lines.extend(parse_obj(layout._objs))  # extend the list with the lines from each page
    return lines

path = 'Abbreviated Náhuatl Dictionary.pdf'
dlim = '|'

lines = parse_pdf(path)

# Pattern to match
pattern = re.compile(r"""\ (
                            adj\.|
                            adv\.|
                            af\.|
                            conj\.|
                            der\.|
                            dim\.|
                            expr\.|
                            loc\.\ adv\.|
                            loc\.\ conjunt\.\ condic\.|
                            loc\.\ prep\.|
                            onomat\.|
                            [p|P]ref\.|
                            pref\.\ aux\.|
                            prep\.|
                            pron\.|
                            s\.|
                            vb\.
                          )\ """,
                     re.VERBOSE)  # re.VERBOSE allows multi-line pattern with comments

for line in lines:

    pos_definition = line
    # Find the part of speech
    # match = re.search(pattern, pos_definition)
    match = re.split(pattern, line)
    if len(match) == 1:
        # it's a letter we don't care
        continue

    word = match[0]
    pos = match[1]
    definition = match[2]

    # Remove double spaces, cause they are annoying
    pos_definition = pos_definition.replace("  ", ' ')

    dlim = '|'
    print(word + dlim + pos + dlim + definition)
