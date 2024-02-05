from ComprehensibleLatvian.anki import *
from ComprehensibleLatvian.epub import *
from ComprehensibleLatvian.page_objects import *

if __name__ == "__main__":
    epub_file_path = r"C:\Users\small\Calibre Library\Duglass Adamss\Galaktikas celvedis stopetajiem-1 (65)\Galaktikas celvedis stopetajiem - Duglass Adamss.epub"
    # epub_file_path = r"c:\Users\small\Calibre Library\Dzoanna Ketlina Roulinga\Harijs Poters un filozofu akmens (38)\Harijs Poters un filozofu akmen - Dzoanna Ketlina Roulinga.epub"

    extracted_text = extract_text_from_epub(epub_file_path, page_chunk_size=12)

    results = asyncio.run(request_nlp_api(extracted_text))

    results = []
    # "hitchhikers_01.json", , "hitchhikers_02.json", "hitchhikers_03.json", "hitchhikers_04.json"
    # for file in [
    #     "hitchhikers_01.json",
    #     "hitchhikers_02.json",
    # ]:
    #     with open(file, "r") as f:
    #         results.append(json.load(f))

    sentence_list = [
        Sentence(sentence) for result in results for sentence in result["sentences"]
    ]

    container = LemmaContainer()
    for sentence in sentence_list:
        for lemma, form in sentence.lemma_form:
            container.add_lemma(lemma, form, sentence)

    pages = sentences_to_pages(sentence_list)

    anki_cards = [
        card
        for page in pages
        for card in to_anki_cards(key_words=page.key_words, lemma_container=container)
    ]

    # with open("hp_anki_cards.json", "w", encoding='utf8') as f:
    #     json.dump({"deck_id": 123124235242, "anki_cards": anki_cards}, f, indent=2)

    # # reconstruct output
    construct_epub(epub_file_path, pages, "test2.epub")

# todo  Complete sentences_to_lemmas
# todo  add deck id to to_anki_cards output
# todo  add create_anki_pkg function
# todo  Give option to use all files in dir or independant
# todo make objects serializable and save lemma container as output
