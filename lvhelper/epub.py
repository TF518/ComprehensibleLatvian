from itertools import islice

from bs4 import BeautifulSoup
from ebooklib import epub

from lvhelper.oop import Page


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
    ids = []

    # original_epub.items[10].id
    # 'id328'

    # if len page text == 0, page text - empty paage.

    for batch in batched(book.items, page_chunk_size):
        chunk_text = ""
        for item in batch:
            if isinstance(item, epub.EpubHtml) and item.is_chapter():
                content = item.get_content()
                page_id: str = item.get_id().replace(
                    "_", ""
                )  # we split on _ later so dont want this in the id
                ids.append(page_id)
                soup = BeautifulSoup(content, "html.parser")
                page_text = soup.get_text()
                chunk_text += (
                    "page_start_"
                    + page_id
                    + " "
                    + page_text
                    + "\n. "
                    + "page_end_"
                    + page_id
                    + ". \n "
                )

        page_chunks.append(chunk_text)
    return page_chunks


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


def make_key_word_soup_tag(key_word: str, translation: str):
    soup = BeautifulSoup("", "html.parser")
    key_word_tag = soup.new_tag("div", attrs={"class": "paragraph"})
    key_word_tag.string = "\n".join([key_word, translation])

    return key_word_tag


def init_new_epub(original_epub: epub.EpubBook) -> epub.EpubBook:
    """Initalise new epub object by copying over contents from old book.

    Args:
        original_epub:(epub.EpubBook): Original epub

    Returns:
        epub.EpubBook: EpubBook object with meta data copied over
    """
    new_book = epub.EpubBook()
    new_book.metadata = original_epub.metadata
    new_book.toc = original_epub.toc

    cover_content = original_epub.items[0].get_content()
    new_book.set_cover("cover.jpeg", content=cover_content)
    return new_book


def construct_epub(epub_file_path: str, pages: list[Page], save_path: str):
    original_epub = epub.read_epub(epub_file_path)
    new_book = init_new_epub(original_epub=original_epub)

    new_spine = []
    page_map = {page.page_number: page for page in pages}

    for item in original_epub.items[
        1:
    ]:  # assuming the first item is the cover - will see if this is valid
        page_id = item.get_id()

        if page_id in page_map:
            soup = BeautifulSoup("<div></div>", "html.parser")

            page = page_map[page_id]

            key_word_tags = [make_key_word_soup_tag(*kw) for kw in page.key_words]
            # reverse so we add the most important words at the top
            for tag in reversed(key_word_tags):
                soup.div.insert_before(tag)

            key_word_page = epub.EpubHtml(
                title=f"{page_id}_keywords",
                file_name=f"{page_id}_keywords.xhtml",
                lang="lv",
            )
            key_word_page.content = soup.encode("utf-8")
            new_book.add_item(key_word_page)
            new_spine.append(key_word_page)

        # if isinstance(item, epub.EpubImage):
        #     # might have to revisit this
        #     # check if you need to add html <img src="path/img_file.jepg"/> somewhere
        #     content = item.get_content()
        #     id = item.get_id()
        #     media_type = item.media_type
        #     item = epub.EpubImage(uid=id, media_type=media_type, content=content)

        new_book.add_item(item)
        new_spine.append(item)

    new_book.spine = new_spine
    epub.write_epub(save_path, new_book)

    return None


if __name__ == "__main__":
    epub_file_path = r"C:\Users\small\Calibre Library\Duglass Adamss\Galaktikas celvedis stopetajiem-1 (65)\Galaktikas celvedis stopetajiem - Duglass Adamss.epub"
    extracted_text = extract_text_from_epub(epub_file_path, page_chunk_size=10)

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
