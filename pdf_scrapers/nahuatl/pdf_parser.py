from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTChar
from pdfminer.pdfpage import PDFPage

def parse_obj(lt_objs):
    for obj in lt_objs:
        if isinstance(obj, LTTextBox):
            for text_line in obj:
                if isinstance(text_line, LTTextLine):
                    for character in text_line:
                        if isinstance(character, LTChar):
                            print ("%s FONT SIZE: %s, fontname: %s" % (character.get_text(), character.size, character.fontname))
        elif hasattr(obj, '_objs'):
            parse_obj(obj._objs)


def parse_pdf(path):
    # Open a PDF file.
    with open(path, 'rb') as fp:
        # Create a PDF resource manager object that stores shared resources.
        rsrcmgr = PDFResourceManager()
        # Set parameters for analysis.
        laparams = LAParams()
        # Create a PDF page aggregator object.
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.get_pages(fp):
            interpreter.process_page(page)
            # receive the LTPage object for the page.
            layout = device.get_result()
            parse_obj(layout._objs)

parse_pdf('Abbreviated Náhuatl Dictionary.pdf')
