from pdfquery import PDFQuery
pdf = PDFQuery("creeverbs.pdf")
pdf.load()

# Locate the elements.
text_elements = pdf.pq("LTTextLineHorizontal")

# Extract the text from the elements.
text = [t.text for t in text_elements]

print(text)
