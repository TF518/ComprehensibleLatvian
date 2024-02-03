import itertools
import logging
import os
from collections import defaultdict
from datetime import datetime
from functools import partial

# import deepl
import yake
from googletrans import Translator

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("lvLogger")

# this is the string that is used when processing the input text to delimt start and end of a page
PAGE_DELIMITER = "page_"
PAGE_START_DELIMITER = PAGE_DELIMITER + "start_"
PAGE_END_DELIMITER = PAGE_DELIMITER + "end_"


def generate_stopwords_filename():
    # Get the current local time
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Generate the filename with the current local time
    filename = f"stopwords_{current_time}.txt"

    return filename


# path to where the books stop words will be saved
# will probs be set in the script later
stopword_save_path = generate_stopwords_filename()
STOPWORD_SAVE_PATH = stopword_save_path


def make_page_sentence_map(all_sentence_dict: dict[str, list]):
    """
    Creates a mapping of sentences to their respective pages based on delimiters.

    Args:
        all_sentence_dict (dict[str, list]): Dictionary containing information about sentences.

    Returns:
        dict: A mapping of sentences to their respective pages. e.g {pages: [{page: 1, start_idx:0, end_idx:19}, {...}] }
    """
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


def load_local_stopwords(
    file_name=generate_stopwords_filename(), load_all_in_dir=False
):
    """
    Loads stop words saved in the local working directory.

    Args:
        file_name (str, optional): Name of the stopwords file. Defaults to generated filename.
        load_all_in_dir (bool, optional): Whether to load stopwords from all files in the directory. Defaults to False.

    Returns:
        set: Set of stop words.
    """
    # load stop words saved in local working directory

    # Create a directory for stopwords in the local working directory
    specific_stopwords_dir = os.path.join(os.getcwd(), "stopwords")
    os.makedirs(specific_stopwords_dir, exist_ok=True)

    # Define the path for the specific stopwords file based on the working directory
    specific_stopwords_path = os.path.join(specific_stopwords_dir, file_name)

    # Check if the specific stopwords file exists in the working directory
    if os.path.exists(specific_stopwords_path):
        with open(specific_stopwords_path, encoding="utf-8") as specific_stopwords_file:
            specific_stopword_set = set(
                specific_stopwords_file.read().lower().split("\n")
            )
    else:
        specific_stopword_set = set()

    if load_all_in_dir:
        # Get a list of all files in the directory
        all_files = os.listdir(specific_stopwords_dir)

        # Iterate through all files and merge their stopwords into the set
        for filename in all_files:
            specific_stopword_set.update(load_local_stopwords(file_name=filename))

    return specific_stopword_set


def load_common_stopwords(file_name="stopwords.txt"):
    """
    Loads common stop words saved in the package resources.

    Args:
        file_name (str, optional): Name of the stopwords file. Defaults to "stopwords.txt".

    Returns:
        set: Set of common stop words.

    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    local_path = os.path.join("resources", file_name)
    resource_path = os.path.join(dir_path, local_path)

    try:
        with open(resource_path, encoding="utf-8") as stop_fil:
            stopword_set = set(stop_fil.read().lower().split("\n"))
    except FileNotFoundError:
        stopword_set = set()

    return stopword_set


def write_stopwords(file_name="stopwords.txt", stop_words=set()):
    """
    Writes a stopword file to the local working directory.

    Args:
        file_name (str, optional): Name of the stopwords file. Defaults to "stopwords.txt".
        stop_words (set, optional): Set of stop words to be written to the file. Defaults to an empty set.

    Returns:
        None. Creates a 'stopwords' directory in the working directory and writes file_name to it.

    """
    # write stopword file to local working directory
    # Create a directory for stopwords in the local working directory
    local_stopwords_dir = os.path.join(os.getcwd(), "stopwords")
    os.makedirs(local_stopwords_dir, exist_ok=True)

    # Define the path for the specific stopwords file based on the working directory
    specific_stopwords_path = os.path.join(local_stopwords_dir, file_name)

    with open(specific_stopwords_path, "w+", encoding="utf-8") as file:
        for item in stop_words:
            file.write(str(item) + "\n")


def extract_key_words(text: str, stop_words: set, save_path: str, no_key_words=20):
    """
    Extracts key words from the given text and updates the stop words.

    Args:
        text (str): The input text from which key words are to be extracted.
        stop_words (set): Set of stop words.
        save_path (str): Path to the stop words file to be updated.
        no_key_words (int, optional): Number of key words to extract. Defaults to 20.

    Returns:
        List[str]: List of extracted key words.

    Note:
        This function uses the YAKE keyword extraction algorithm to extract key words from the input text.
        Writes new keywords to stop_words file so that the same key word is not returned more than once
    """

    language = "lv"
    max_ngram_size = 1
    deduplication_threshold = 0.9
    deduplication_algo = "seqm"
    windowSize = 1
    numOfKeywords = no_key_words

    default_stopwords = load_common_stopwords()
    # global stop words - load all previous stop words, add new ones in and save again
    book_stopwords = load_local_stopwords(save_path)
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
        """
        Initializes a Sentence object.

        Args:
            sentence (dict): Dictionary representing the sentence as returned from nlp.ailab.lv/api/nlp.

        Attributes:
            sentence (dict): The original sentence dictionary.
            ner (list): List of named entities in the sentence.
            tokens (list): List of tokens in the sentence.
            lemma_form (list): List of tuples containing token lemma and lowercase form.
            text (str): The text of the sentence.
            lemma_text (str): The text of the sentence with lemmatized tokens.
            stop_words (set): Set of stop words in the sentence.

        """
        # self.word_forms = []
        self.sentence = sentence
        self.ner = sentence["ner"]
        self.tokens = sentence["tokens"]

        self.lemma_form = [
            (token["lemma"], token["form"].lower()) for token in self.tokens
        ]

        self.text: str = self.make_text(sentence["tokens"])
        self.lemma_text: str = self.make_lemma_text(sentence["tokens"])
        self.stop_words: set = self.make_stop_words(sentence["ner"])

    # def add_word_form(self, form):
    #     self.word_forms.append(form)

    def make_text(self, tokens):
        """
        Creates the text of the sentence from its tokens.

        Args:
            tokens (list): List of tokens in the sentence.

        Returns:
            str: The text of the sentence.
        """
        text = ""
        for i, token in enumerate(tokens):
            form = token["form"]
            if form.startswith(PAGE_DELIMITER):
                continue
            # Look forward, if next is a punctuation dont add a trailing space
            if i + 1 < len(tokens) and tokens[i + 1]["form"] in [
                ".",
                ";",
                ":",
                ",",
                "!",
                "?",
            ]:
                text = text + form
            else:
                text = text + f"{form} "
        return text

    # def make_text(self, tokens):
    #     return " ".join(
    #         [
    #             token["form"]
    #             for token in tokens
    #             if not token["form"].startswith(PAGE_DELIMITER)
    #         ]
    #     )

    def make_lemma_text(self, tokens):
        """
        Creates the lemmatized text of the sentence from its tokens.

        Args:
            tokens (list): List of tokens in the sentence.

        Returns:
            str: The lemmatized text of the sentence.
        """
        return " ".join(
            [
                token["lemma"].lower()
                for token in tokens
                if not token["lemma"].startswith(PAGE_DELIMITER)
            ]
        )

    def make_stop_words(self, ner):
        """
        Creates a set of stop words from the named entities in the sentence.

        Args:
            ner (list): List of named entities in the sentence.

        Returns:
            set: Set of stop words.
        """
        # split named entities into single words then flatten into list
        stop_word_list = itertools.chain.from_iterable(
            [ne["text"].lower().split(" ") for ne in ner]
        )
        return set(stop_word_list)

    def __len__(self):
        # len will be the number of words in the sentence
        return len(self.tokens)


# google translate isn't very good
translator = Translator()
translator_fn = partial(translator.translate, src="lv")

# deepl also is not very good :(
# translator = deepl.Translator(os.environ.get("deepl_auth_key"))
# translator_fn = partial(
#     translator.translate_text, source_lang="LV", target_lang="EN-GB", preserve_formatting=True
# )


class Page:
    def __init__(
        self,
        page_number: int,
        start_end_slice: slice,
        sentences: list[Sentence],
        translator=translator_fn,
    ):
        """
        Initializes a Page object.

        Args:
            page_number (int): The page number.
            start_end_slice (slice): Slice indicating the start and end indices of the page in the document.
            sentences (list[Sentence]): List of Sentence objects representing the sentences on the page.
            translator (callable, optional): Translator function to translate key words. Defaults to translator_fn.

        Attributes:
            page_number (int): The page number.
            start_end_slice (slice): Slice indicating the start and end indices of the page in the document.
            sentences (list[Sentence]): List of Sentence objects representing the sentences on the page.
            translator (callable): Translator function to translate key words.
            text (str): The text of the page.
            lemma_text (str): The lemmatized text of the page.
            stop_words (set): Set of stop words on the page.
            _key_words (list[str]): List of extracted key words.
            translated_kws (list[str]): List of translated key words.
            key_words (list[tuple[str, str]]): List of tuples containing original and translated key words.

        """
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


class Lemma:
    def __init__(self, lemma):
        """
        Initializes a Lemma object.

        Args:
            lemma (str): The lemma.

        Attributes:
            lemma (str): The lemma.
            forms (dict): Dictionary where key is each form of the lemma and the value is a list of scentences where that form occurs.
        """
        self.lemma: str = lemma
        self.forms: dict[str, list[str]] = defaultdict(list)

    # add methods to show all forms for a lemma (self.forms.keys())
    # add methods to show all sentences for all wordforms of lemma

    def add_word_form(self, form: str, sentence: str):
        """
        Adds a word form to the lemma's forms dictionary.

        Args:
            form (str): The word form.
            sentence (str): The sentence containing the word form.
        """
        self.forms[form].append(sentence)

    def get_wordform(self, form: str):
        """
        Retrieves the sentences containing a specific word form.

        Args:
            form (str): The word form.

        Returns:
            list[str]: List of sentences containing the specified word form.

        """
        if form in self.forms:
            return self.forms[form]

        return []

    def __hash__(self):
        return hash((self.lemma))

    def __eq__(self, other):
        return isinstance(other, Lemma) and self.lemma == other.lemma


class LemmaContainer:
    def __init__(self):
        """
        Initializes a LemmaContainer object.

        Attributes:
            lemmas (dict): Dictionary mapping lemmas to corresponding Lemma objects.

        Note:
            This class is designed to store and manage Lemma objects.

        Example:
            ```python
            lemma_container = LemmaContainer()
            ```
        """
        self.lemmas: dict[str, Lemma] = {}

    def add_lemma(self, lemma: str, form: str, sentence: str) -> None:
        """
        Adds a word form to the lemma's forms dictionary in the LemmaContainer.

        Args:
            lemma (str): The lemma.
            form (str): The word form.
            sentence (str): The sentence containing the word form.

        Example:
            ```python
            lemma_container.add_lemma(lemma="example", form="example_form", sentence="This is an example sentence.")
            ```
        """
        updated_lemma = self.get_lemma(lemma)
        updated_lemma.add_word_form(form, sentence)

        self.lemmas[lemma] = updated_lemma

    def get_lemma(self, lemma: str) -> Lemma:
        """
        Retrieves the Lemma object for a specific lemma.

        Args:
            lemma (str): The lemma.

        Returns:
            Lemma: The Lemma object for the specified lemma.

        Example:
            ```python
            existing_lemma = lemma_container.get_lemma(lemma="existing_example")
            ```

        Note:
            This method returns the existing Lemma object if present, otherwise creates a new Lemma object.
        """
        if lemma in self.lemmas:
            return self.lemmas[lemma]

        return Lemma(lemma)

    def get_all_lemmas(self):
        return list(self.lemmas.values())


def sentences_to_lemmas(sentences: list[Sentence], lemma_container: LemmaContainer):
    for sentence in sentences:
        pass


def sentences_to_pages(sentences: list[Sentence]):
    """
    Converts a list of Sentence objects into a list of Page objects.

    Args:
        sentences (list[Sentence]): List of Sentence objects.

    Returns:
        list[Page]: List of Page objects.

    """
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
