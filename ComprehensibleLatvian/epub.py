import asyncio
import json
from itertools import islice

import aiohttp
from bs4 import BeautifulSoup
from ebooklib import epub


def batched(iterable, n):
    """
    Groups elements of an iterable into batches of size 'n'.

    Args:
        iterable: The input iterable.
        n (int): Batch size.

    Returns:
        Generator: A generator yielding batches of elements.
    """
    # from itertools but later python version
    # batched('ABCDEFG', 3) --> ABC DEF G

    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


def extract_text_from_epub(epub_file_path, page_chunk_size=10) -> list[str]:
    """
    Extracts text from an EPUB file into chunks.

    Args:
        epub_file_path (str): Path to the EPUB file.
        page_chunk_size (int, optional): Number of pages in each chunk. Defaults to 10.

    Returns:
        List[str]: List of text chunks.

    Note:
        This function extracts text content from EPUB pages, groups it into chunks, and adds page identifiers for context.

    Example:
        ```python
        text_chunks = extract_text_from_epub("sample.epub", page_chunk_size=5)
        print(text_chunks)
        ```
    """
    book = epub.read_epub(epub_file_path)
    page_chunks = []
    ids = []

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


def make_nlp_post_body(text: str, steps: list[str] = ["tokenizer", "morpho", "ner"]):
    """
    Creates a POST request body for the ailab NLP API.

    Args:
        text (str): Input text to be processed.
        steps (List[str], optional): NLP processing steps (tokenizer, morpho, parser, ner). Default is ["tokenizer", "morpho", "ner"].

    Returns:
        dict: A dictionary of url, headers and data

    Example:
        ```python
        post_body = make_nlp_post_body("Sample text for NLP processing")
        print(post_body)
        ```
    """

    end_point = "https://nlp.ailab.lv/api/nlp"
    headers = {"Content-Type": "application/json"}

    data = {
        "steps": steps,
        "data": text,
    }

    return {"url": end_point, "headers": headers, "data": json.dumps(data)}


async def fetch_data(post_body):
    """
    Asynchronously fetches data from a specified endpoint using a POST request.

    Args:
        post_body (dict): Dictionary containing information for the POST request, including URL, headers, and data.

    Returns:
        dict: Data received from the API response.
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(**post_body) as response:
            data = await response.json()
            return data["data"]


async def request_nlp_api(text_list: list[str]):
    """
    Asynchronously makes NLP API requests for a list of texts.

    Args:
        text_list (List[str]): List of texts to be processed by the NLP API.

    Returns:
        List[dict]: List of results received from the NLP API responses.
    """
    request_bodies = [make_nlp_post_body(text) for text in text_list]

    tasks = [fetch_data(body) for body in request_bodies]
    results = await asyncio.gather(*tasks)
    return results


def make_key_word_soup_tag(key_word: str, translation: str):
    """
    Creates a BeautifulSoup tag for a key word and its translation.

    Args:
        key_word (str): The key word.
        translation (str): The translation of the key word.

    Returns:
        Tag: A BeautifulSoup tag representing the key word and its translation.

    Example:
        ```python
        key_word_tag = make_key_word_soup_tag("apple", "ābols")
        print(key_word_tag)
        ```
    """

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


def construct_epub(epub_file_path: str, pages: list, save_path: str):
    """
    Constructs a new EPUB file with additional pages containing key word tags.

    Args:
        epub_file_path (str): Path to the original EPUB file.
        pages (List[Page]): List of Page objects containing key words.
        save_path (str): Path to save the new EPUB file.

    Returns:
        None. Writes an epub to save_path
    """
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
