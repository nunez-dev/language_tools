# language_tools

wiktionary_webscraper.py is a quick and dirty wiktionary web scraper to download words, IPA, definitions, and audio from en.wiktionary.org.

It puts them into an unsorted text file with a '|' seperator by default named something like spanish_verbs_${time}
Currently that is "word | ipa | def1 | def2 | def3 | \[sound:file.wav\]".
Audio would be stored in spanish_verbs_audio_${time}

The hope is then to manually import them into anki to make an anki dictionary.
After the dictionary is made you need to copy the audio to anki media directory, such as:
`~/.local/share/Anki2/User 1/collection.media`
And run tools->check media to make sure the files are found. It will tell you if they are missing.
Testing has been minimal so it may or may not generalise to all languages and parts of speech. Expect breaks.

```bash
# Requires https://pypi.org/project/beautifulsoup4/
./wiktionary_webscraper.py
# Or if you want to log all the output, comment in the empty "class bcolors" first. Then I use:
{ time ./wiktionary_webscraper.py; } 2>&1 | tee log.txt
```
