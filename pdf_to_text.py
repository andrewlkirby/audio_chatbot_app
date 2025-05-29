import fitz
from pathlib import Path
import re

def from_pdf(path: Path) -> str:
    doc = fitz.open(path)
    page_list = []
    for page in doc:
        page_block = page.get_text("blocks")
        page_list.append(page_block)

    page_tuple_list = [item for sublist in page_list for item in sublist]
    text_list = [item[4] for item in page_tuple_list]

    clean_text_list = []
    for text_item in text_list:
        clean_text1 = re.sub('\n', '', text_item)
        clean_text2 = re.sub('\s*$', '', clean_text1)
        clean_text_list.append(clean_text2)

    cleaner_text_list = [text for text in clean_text_list if len(text) > 0]
    text = "\n\n".join(cleaner_text_list)
    return text