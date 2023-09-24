# language_tools

wiktionary_webscraper.py is a quick and dirty wiktionary web scraper to download words, IPA, definitions, and audio from en.wiktionary.org.

It puts them into an unsorted text file with a '|' seperator by default named something like "spanish_verbs_time.
Currently that is "word | ipa | def1 | def2 | def3 | relative_audio_path".
Audio would be stored in "spanish_audio_time"

The hope is then to manually import them into anki to make an anki dictionary.
Testing has been minimal so it may or may not generalise to all languages and parts of speech. Expect breaks.

```bash
# Requires https://pypi.org/project/beautifulsoup4/
python3 ./wiktionary_webscraper.py
```
