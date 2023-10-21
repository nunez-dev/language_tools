# language_tools

wiktionary_webscraper.py is a wiktionary web scraper script to download words, IPA, definitions, and audio from en.wiktionary.org.

It puts them into an unsorted text file with a '|' seperator named spanish_verbs_${time}.txt
Currently that is "word | ipa | def1 | def2 | def3 | \[sound:file.wav\]".
Audio is stored in a spanish_verbs_audio_${time} directory
A log file is produced as spanish_verbs_${time}_log.txt

The goal is then to manually import them into anki to make an anki dictionary.
After the dictionary is made you need to copy the audio to anki media directory, such as:
`~/.local/share/Anki2/User 1/collection.media`
And run tools->check media to make sure the files are found. It will tell you if they are missing.
May not generalise to all languages and parts of speech. Wiktionary is user edited after all, so it's impossible to account for all the possibilities.

```bash
# Requires https://pypi.org/project/beautifulsoup4/ and tqdm
./wiktionary_webscraper.py
```
