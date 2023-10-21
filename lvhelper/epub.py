from itertools import islice

from bs4 import BeautifulSoup
from ebooklib import epub


def batched(iterable, n):
    # from itertools but later python version
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


def extract_text_from_epub(epub_file_path, page_chunk_size=10) -> list[str]:
    """Extract text from an epub into chunks of

    Args:
        epub_file_path (_type_): _description_
        page_chunk_size (int, optional): _description_. Defaults to 10.

    Returns:
        list[str]: _description_
    """
    book = epub.read_epub(epub_file_path)
    page_chunks = []
    page_no = 1
    for batch in batched(book.items, page_chunk_size):
        chunk_text = ""
        for item in batch:
            if isinstance(item, epub.EpubHtml):
                content = item.get_content()
                soup = BeautifulSoup(content, "html.parser")
                page_text = soup.get_text()
                chunk_text += (
                    "page_start_"
                    + str(page_no)
                    + " "
                    + page_text
                    + " "
                    + "page_end_"
                    + str(page_no)
                    + ". \n"
                )
                page_no += 1
        page_chunks.append(chunk_text)
    return page_chunks


# Replace 'your_epub_file.epub' with the path to your EPUB file
# epub_file_path = r"C:\Users\small\Calibre Library\Duglass Adamss\Galaktikas celvedis stopetajiem-1 (65)\Galaktikas celvedis stopetajiem - Duglass Adamss.epub"
# extracted_text = extract_text_from_epub(epub_file_path)
# # Specify the path for the output text file
# output_txt_file = "./output_text.txt"

# # Write the extracted text to the text file
# with open(output_txt_file, "w", encoding="utf-8") as file:
#     file.write(extracted_text)


import asyncio
import json

import aiohttp


def make_nlp_post_body(text: str, steps: list[str] = ["tokenizer", "morpho", "ner"]):
    # full steps available: ["tokenizer", "morpho", "parser", "ner"]

    end_point = "https://nlp.ailab.lv/api/nlp"
    headers = {"Content-Type": "application/json"}

    data = {
        "steps": steps,  # maybe add ner to remove names
        "data": text,
    }

    return {"url": end_point, "headers": headers, "data": json.dumps(data)}


async def fetch_data(post_body):
    async with aiohttp.ClientSession() as session:
        async with session.post(**post_body) as response:
            data = await response.json()
            return data["data"]


async def request_nlp_api(text_list: list[str]):
    request_bodies = [make_nlp_post_body(text) for text in text_list]

    tasks = [fetch_data(body) for body in request_bodies]
    results = await asyncio.gather(*tasks)
    return results


if __name__ == "__main__":
    pass
    # epub_file_path = r"Duglass Adamss\Galaktikas celvedis stopetajiem-1 (65)\Galaktikas celvedis stopetajiem - Duglass Adamss.epub"
    # extracted_text = extract_text_from_epub(epub_file_path, page_chunk_size=10)

    # extracted_text = [extracted_text[0]]
    # # want to make a list where each item is the text from 10 pages
    # results = asyncio.run(request_nlp_api(extracted_text))
    # # flatten results so that it's only a dictionary of sentences
    # # check this extends the list rather than just replaces it with the last result
    # # sentences = {'sentences': result['sentences'] for result in results}
    # # join together broken down by page

    # mapping = make_page_sentence_map(results)
    # page = results[0]["sentences"][1:38]
    # text, lemma_text, stop_words = make_page_lemma_text(page)

    # top_words = extract_words(lemma_text, stop_words, "debugging.txt")
