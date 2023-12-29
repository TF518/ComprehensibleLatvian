import itertools
import os
from functools import partial

import yake
from googletrans import Translator

# this is the string that is used when processing the input text to delimt start and end of a page
PAGE_DELIMITER = "page_"
PAGE_START_DELIMITER = PAGE_DELIMITER + "start_"
PAGE_END_DELIMITER = PAGE_DELIMITER + "end_"

# path to where the books stop words will be saved
# will probs be set in the script later
STOPWORD_SAVE_PATH = "./book_stopwords.txt"


def make_page_sentence_map(all_sentence_dict: dict[str, list]):
    # returns dict of form{pages: [{page: 1, start_idx:0, end_idx:19}, {...}] }
    page_sentence_mapping = {"pages": []}
    for index, sentence_dict in enumerate(all_sentence_dict["sentences"]):
        delimiter = sentence_dict["tokens"][0]["form"]
        if delimiter.startswith(PAGE_START_DELIMITER):
            page_number = delimiter.split("_")[-1]
            start_idx = index
        if delimiter.startswith(PAGE_END_DELIMITER):
            end_idx = index
            page_sentence_mapping["pages"].append(
                {"page": page_number, "start_idx": start_idx, "end_idx": end_idx}
            )

    return page_sentence_mapping


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


def extract_key_words(text: str, stop_words: set, save_path: str, no_key_words=20):
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


class Sentence:
    def __init__(self, sentence: dict):
        self.word_forms = []
        self.sentence = sentence
        self.ner = sentence["ner"]
        self.tokens = sentence["tokens"]

        # self.lemmas: list[Lemma] = self.make_lemmas(sentence["tokens"])

        self.text: str = self.make_text(sentence["tokens"])
        self.lemma_text: str = self.make_lemma_text(sentence["tokens"])
        self.stop_words: set = self.make_stop_words(sentence["ner"])

    def add_word_form(self, form):
        self.word_forms.append(form)

    # def make_lemmas(self, tokens):
    #     [
    #         Lemma(token["lemma"].lower())
    #         for token in tokens
    #         if not token["lemma"].startswith(PAGE_DELIMITER)
    #     ]

    def make_text(self, tokens):
        return " ".join(
            [
                token["form"]
                for token in tokens
                if not token["form"].startswith(PAGE_DELIMITER)
            ]
        )

    def make_lemma_text(self, tokens):
        return " ".join(
            [
                token["lemma"].lower()
                for token in tokens
                if not token["lemma"].startswith(PAGE_DELIMITER)
            ]
        )

    def make_stop_words(self, ner):
        # split named entities into single words then flatten into list
        stop_word_list = itertools.chain.from_iterable(
            [ne["text"].lower().split(" ") for ne in ner]
        )
        return set(stop_word_list)


translator = Translator()
translator_fn = partial(translator.translate, src="lv")


class Page:
    def __init__(
        self,
        page_number: int,
        start_end_slice: slice,
        sentences: list[Sentence],
        translator=translator_fn,
    ):
        self.page_number = page_number
        self.start_end_slice = start_end_slice
        self.sentences = sentences
        self.translator = translator

        self.text: str = " ".join([sentence.text for sentence in sentences])
        self.lemma_text: str = " ".join([sentence.lemma_text for sentence in sentences])
        self.stop_words: set = set().union(
            *[sentence.stop_words for sentence in sentences]
        )

        self._key_words: list[str] = extract_key_words(
            text=self.lemma_text,
            stop_words=self.stop_words,
            save_path=STOPWORD_SAVE_PATH,
        )

        self.translated_kws: list[str] = [
            translation.text for translation in self.translator(self._key_words)
        ]
        self.key_words: list[tuple[str, str]] = list(
            zip(self._key_words, self.translated_kws)
        )


class WordForm:
    def __init__(self, form, sentence):
        self.form = form
        self.sentence = sentence
        sentence.add_word_form(self)


class Lemma:
    def __init__(self, lemma):
        self.lemma: str = lemma
        # todo: make this a dict where key is form.form and value is Form obj
        self.forms = []

    def add_word_form(self, form):
        self.forms.append(form)


def sentences_to_pages(sentences: list[Sentence]):
    page_list = []
    for index, sentence_dict in enumerate(sentences):
        delimiter = sentence_dict.tokens[0]["form"]
        if delimiter.startswith(PAGE_START_DELIMITER):
            page_number = delimiter.split("_")[-1]
            start_idx = index
        if delimiter.startswith(PAGE_END_DELIMITER):
            end_idx = index
            sentence_slice = slice(start_idx, end_idx)
            page_sentences = sentences[sentence_slice]

            page_list.append(
                Page(
                    page_number=page_number,
                    start_end_slice=sentence_slice,
                    sentences=page_sentences,
                )
            )

    return page_list
