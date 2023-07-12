# language_tools

wiktionary_webscraper.py is a quick and dirty wiktionary web scraper to download words, IPA, and their definitions from en.wiktionary.org.

It puts them into an unsorted text file with a '|' seperator by default named something like "kazakh_verbs_23:13:02.263280.txt".
Currently that is "word | ipa | def1 | def2 | def3".

The idea is then to manually import into anki to make an anki dictionary.
Testing has been minimal so it may or may not generalise to all languages and parts of speech.

```bash
# Requires https://pypi.org/project/beautifulsoup4/
python3 ./wiktionary_webscrape.py
```