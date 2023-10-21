import argparse

from lvhelper.epub import *
from lvhelper.oop import *
from lvhelper.process_text import *
from lvhelper.process_text2 import *

__author__ = "Mit"
__version__ = "0.1.0"
__license__ = "MIT"


def main(args):
    """Main entry point of the app"""
    print("hello world")
    print(args)


if __name__ == "__main__":
    epub_file_path = r"C:\Users\small\Calibre Library\Duglass Adamss\Galaktikas celvedis stopetajiem-1 (65)\Galaktikas celvedis stopetajiem - Duglass Adamss.epub"
    extracted_text = extract_text_from_epub(epub_file_path, page_chunk_size=10)

    extracted_text = [extracted_text[0]]
    # want to make a list where each item is the text from 10 pages
    results = asyncio.run(request_nlp_api(extracted_text))
    # flatten results so that it's only a dictionary of sentences
    # check this extends the list rather than just replaces it with the last result
    sentence_dict = {"sentences": result["sentences"] for result in results}
    # join together broken down by page

    # todo: shoud we process results into Sentence objects first then run key word extraction for each
    # page

    # mapping = make_page_sentence_map(sentences)
    # page = results[0]["sentences"][39:388]
    pages = sentences_to_pages(sentence_dict)
    text, lemma_text, stop_words, lemma_sentence_map = make_page_lemma_text(page)

    top_words = extract_words(lemma_text, stop_words, "debugging.txt")
