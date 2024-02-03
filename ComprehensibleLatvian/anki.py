def to_anki_cards(key_words: list[tuple], lemma_container):
    """
    Converts key words and their translations into a dict ready to be consumed to Anki Cloze card format.

    Args:
        key_words (list[tuple]): List of tuples containing key words and their translations.
        lemma_container (LemmaContainer): LemmaContainer object containing lemma information.

    Returns:
        list[dict]: List of dictionaries representing Anki cards.

    Note:
        To limit the number of cards that can be produced cards are only the most frequent word form is selected and the shortest example sentence for each key word.
        Anki cards are represented as dictionaries with "header," "cloze_string," and "backside" (currently unused) keys.
    """

    # for every keyword we want
    # one form with one example sentence.
    # to find the form, select the form that has the most example sentences
    # select the sentence by shortest length

    anki_cards = []
    for kw, trans in key_words:
        forms = lemma_container.get_lemma(kw).forms
        if len(forms[kw]) == 0:
            continue

        # get the form that has the most example sentences
        form_most_sentences = max(forms, key=lambda k: len(forms[k]))
        shortest_example_sentence = min(forms[form_most_sentences], key=len)

        anki_header = f"{'_' if kw == form_most_sentences else kw } ({trans})"
        anki_string = shortest_example_sentence.text.replace(
            form_most_sentences, f"{{{{c1::{form_most_sentences}}}}}"
        )
        anki_extra = ""

        card = {
            "header": anki_header,
            "cloze_string": anki_string,
            "backside": anki_extra,
        }
        anki_cards.append(card)
    return anki_cards
