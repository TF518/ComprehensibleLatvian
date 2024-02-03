import itertools
import os

import yake

# def make_page_sentence_map(all_sentence_dict: dict[str, list]):
#     # returns dict of form{pages: [{page: 1, start_idx:0, end_idx:19}, {...}] }
#     page_sentence_mapping = {"pages": []}
#     for index, sentence_dict in enumerate(all_sentence_dict["sentences"]):
#         delimiter = sentence_dict["tokens"][0]["form"]
#         if delimiter.startswith("page_start_"):
#             page_number = delimiter.split("_")[-1]
#             start_idx = index
#         if delimiter.startswith("page_end_"):
#             end_idx = index
#             page_sentence_mapping["pages"].append(
#                 {"page": page_number, "start_idx": start_idx, "end_idx": end_idx}
#             )

#     return page_sentence_mapping


# mapping = make_page_sentence_map(results)
# reconsturct page from tokens
# tokens_to_text
# page = results[0]["sentences"][1:38]


# def make_page_lemma_text(sentences: list[dict]):
#     text = ""
#     lemma_text = ""
#     stop_words = set()
#     # this will be {lemma: [ idx of sentence it occurs]}
#     # only the last sentence of the page is recorded this way so will be a list of len 1
#     # but making it a list in case later want to record multiple indicies
#     lemma_sentence_map = {}

#     for idx, ner_token_dict in enumerate(sentences):
#         ner = ner_token_dict["ner"]
#         tokens = ner_token_dict["tokens"]
#         text += " ".join(
#             [token["form"] for token in tokens if not token["form"].startswith("page_")]
#         )

#         lemma_text += " ".join(
#             [
#                 token["lemma"].lower()
#                 for token in tokens
#                 if not token["lemma"].startswith("page_")
#             ]
#         )

#         lemma_sentence_map.update(
#             {
#                 token["lemma"]: [idx]
#                 for token in tokens
#                 if not token["lemma"].startswith("page_")
#             }
#         )

#         # split named entities into single words then flatten into list
#         stop_word_list = itertools.chain.from_iterable(
#             [ne["text"].lower().split(" ") for ne in ner]
#         )
#         stop_words.update(stop_word_list)

#     return text, lemma_text, stop_words, lemma_sentence_map


def load_stopwords(file_name="stopwords.txt"):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    local_path = os.path.join("resources", file_name)
    resource_path = os.path.join(dir_path, local_path)

    try:
        with open(resource_path, encoding="utf-8") as stop_fil:
            stopword_set = set(stop_fil.read().lower().split("\n"))
    except FileNotFoundError:
        stopword_set = set()

    return stopword_set


def write_stopwords(file_name="temp.txt", stop_words=set()):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    local_path = os.path.join("resources", file_name)
    resource_path = os.path.join(dir_path, local_path)

    with open(resource_path, "w+", encoding="utf-8") as file:
        for item in stop_words:
            file.write(str(item) + "\n")


def extract_words(text: str, stop_words: set, save_path: str, no_key_words=10):
    language = "lv"
    max_ngram_size = 1
    deduplication_threshold = 0.9
    deduplication_algo = "seqm"
    windowSize = 1
    numOfKeywords = no_key_words

    default_stopwords = load_stopwords()
    # global stop words - load all previous stop words, add new ones in and save again
    book_stopwords = load_stopwords(save_path)
    book_stopwords.update(stop_words)

    all_stopwords = default_stopwords | book_stopwords

    custom_kw_extractor = yake.KeywordExtractor(
        lan=language,
        n=max_ngram_size,
        dedupLim=deduplication_threshold,
        dedupFunc=deduplication_algo,
        windowsSize=windowSize,
        top=numOfKeywords,
        features=None,
        stopwords=all_stopwords,
    )
    keyword_importance = custom_kw_extractor.extract_keywords(text)
    keywords = [word for word, _ in keyword_importance]

    # add new key words to set of book stopwords so later pages don't show words that have already been shown
    book_stopwords.update(set(keywords))
    write_stopwords(file_name=save_path, stop_words=book_stopwords)

    return keywords


# main thing is that a page has key words
# reconstruct by taking orginal pages and inserting new pages
