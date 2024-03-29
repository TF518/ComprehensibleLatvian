# Comprehensible Latvian

Comprehensible Latvian is a python library that aims to make Latvian texts more comprehensible.

Currently it offers two main features.

Given an EPUB of a Latvian text return an EPUB containing the same text, but at the start of every chapter a page will be added containing the n (default 20) most relevant words in that chapter with a translation to English.

Given an EPUB of a Latvian text generate an Anki .pkg file of cloze type cards using the n most relevant words from each chapter.

An example usage can be found in `../main.py`

# To dos 
I am slowly adding to the project when I find time. Things I plan to do:

* Create a CLI for the package  
* Add sentence mining features  
* Expand number of supported text types 
