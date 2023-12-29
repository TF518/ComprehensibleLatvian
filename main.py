import argparse

from lvhelper.epub import *
from lvhelper.oop import *
from lvhelper.process_text import *
from lvhelper.process_text2 import *

__author__ = "Mit"
__version__ = "0.1.0"
__license__ = "MIT"


if __name__ == "__main__":
    epub_file_path = r"C:\Users\small\Calibre Library\Duglass Adamss\Galaktikas celvedis stopetajiem-1 (65)\Galaktikas celvedis stopetajiem - Duglass Adamss.epub"
    # epub_file_path = r"C:\Users\small\Calibre Library\K. Arons\Braucam tuvu. Braucam talu (70)\Braucam tuvu. Braucam talu - K. Arons.epub"

    # extracted_text = extract_text_from_epub(epub_file_path, page_chunk_size=12)

    # results = asyncio.run(request_nlp_api(extracted_text))

    results = []
    # "hitchhikers_01.json", , "hitchhikers_02.json", "hitchhikers_03.json", "hitchhikers_04.json"
    for file in [
        "hitchhikers_01.json",
        "hitchhikers_02.json",
    ]:
        with open(file, "r") as f:
            results.append(json.load(f))

    sentence_list = [
        Sentence(sentence) for result in results for sentence in result["sentences"]
    ]
    # todo investigate make_lemma_text that is input to key word extraction
    # todo chapter 2 has key eords missing
    pages = sentences_to_pages(sentence_list)

    # # reconstruct output
    construct_epub(epub_file_path, pages, "test2.epub")
