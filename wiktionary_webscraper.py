#!/usr/bin/python3 -u

import requests
from bs4 import BeautifulSoup
import re
import time
import concurrent.futures
import threading
import math
import traceback
import os, errno
import datetime
import sys
from tqdm import tqdm

# Get language and part of speech we want from the user
# Look under the ' Pages in category "Spanish verbs" '
# in https://en.wiktionary.org/wiki/Category:Spanish_verbs
# (if the user wanted spanish verbs)
# Get the total words for progress bar
# Look only within a specific div which contains the dot point word list
# Only pick headings with single characters (and not *), get words (ul dot point list)
# Once we have all the words, nagivate to the word and get ipa and top 3 defintions
# by constructing the url of where the definition resides and accessing it.
# This step is multithreaded, the words list is split into number_of_threads equal parts
# and each thread gets to process one section.
# Save to file using mutex.

class bcolors:
    pass

class bcolors_real:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class bcolors_stub:
    HEADER = ''
    OKBLUE = ''
    OKCYAN = ''
    OKGREEN = ''
    WARNING = ''
    FAIL = ''
    ENDC = ''
    BOLD = ''
    UNDERLINE = ''

# Globals
default_number_of_threads = 10
number_of_threads = 0
seperator = ' | '
def_url = "https://en.wiktionary.org/wiki/"
text_div = '-'*60
words = []
number_of_defs = 3
ipa_pattern = ""
headers = {'User-Agent': 'Wiktionary_webscraper_bot/0.0 (https://github.com/nunez-dev/language_tools)'}
colored_log = 0
language = ""
pos = ""

mutex = threading.Lock() # For writing to wordlist
log_mutex = threading.Lock() # For writing to log
max_pages = 5 # used for testing, lower if you only want first x pages of words

def time_str():
    return datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def download_page(url):
    response = requests.get(url, headers=headers)
    return response

def log(color, thread_prefix, item):
    with log_mutex:
        with open(log_filename, 'a', encoding='utf-8') as file:
            if(colored_log):
                string = thread_prefix + color + item + bcolors.ENDC
            else:
                string = thread_prefix + item
            file.write(string + '\n')

def startup():
    words_url = "https://en.wiktionary.org/w/index.php?title=Category:"
    final_words_url = ""
    url_params = ""
    current_letter = ''
    words_on_current_page = 0
    total_words = 0
    done = 0
    count = 0
    global number_of_threads, language, pos, words, ipa_pattern
    while(True):
        try:
            raw_in = input("How many threads (default:10)? ")
            num = int(raw_in)
        except ValueError as e:
            if(raw_in == ''):
                number_of_threads = default_number_of_threads
                break
            else: 
                print(e)
            continue
        number_of_threads = num
        break

    ipa_pattern = input("\
    What matching pattern should be used with IPA descriptions to prioritise an IPA if there are multiple?\n\
    This was implemented to be able to prioritise certain geographies.\n\
    Some IPAs have for example (Spain) or (Latin America) before them.\n\
    L+ or \"Latin America\" would match the latter (it's regex).\n\
    Default will prioritise the first encountered phonetic IPA\n\
    (default:\"\")? ")

    # Make sure page exists
    page = False
    while(not page):
        
        language = str.capitalize(input("What language? "))
        pos = str.lower(input("What part of speech/lemma?\n(See %s_lemmas) " % (words_url + language)))

        final_words_url = words_url + language + '_' + pos
        print(final_words_url + '\n')

        response = download_page(final_words_url)
        if (response.status_code != 200):
            print(bcolors.FAIL + "ERROR:: " + bcolors.ENDC, end="")
        else:
            print(bcolors.OKGREEN + "SUCCESS:: " + bcolors.ENDC, end="")
            page=True
        
        print("Url returned " + str(response.status_code))
        print(text_div)

    audio_dir = str.lower(language) + '_' + str.lower(pos) + "_audio_" + time_str()
    # Now we know this works we can keep using this url
    while(not done):

        words_on_current_page = 0 # reset this

        url = final_words_url + url_params
        response = download_page(url)

        # Beautiful soup for parsing the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try find the sub heading of interest ' Pages in category "Spanish verbs" '
        h2 = soup.find('h2', string=f"Pages in category \"{language} {pos}\"")

        # Find total words (if we haven't already)
        if(not total_words):
            p = h2.find_next('p', string = re.compile(r"The following [,\d]+ pages are in this category, out of [,\d]+ total."))
            total_str = p.string.split()[-2]
            total_words = int(total_str.replace(",", ""))

        # Find the content div after heading 2
        # This hold all the words, it's a div with class="mw-category mw-category-columns"
        # Can help us oversearching for h3 headers
        div = h2.find_next('div', class_="mw-category mw-category-columns")
            
        # Find all h3s in this div and go through them (letters)
        for h3 in div.find_all('h3'):

            # If we reached a new letter, print it (because fun :)
            if ( current_letter != h3.string ):
                current_letter = h3.string
                print("New letter is " + current_letter)

            # Sometimes they are unicode (cyrilic, like Б)
            # So just see if it is length 1 (as oppossed to A-Z)
            if(len(h3.string) != 1 or h3.string == '*' ):
                print("Found this heading, but not parsing because it didn't look like a letter: ", h3.string)
                # Okay, we will skip to next heading
            else:
                # Actually process
                # Then the unordered list
                ul = h3.find_next('ul')
                # And every entry (list entry)
                for li in ul.find_all('li'):
                    words_on_current_page += 1
                    words.append(li.string)


        cumulative = len(words)
        percent = round(cumulative/total_words * 100)
        print(str(percent) + "% : Found " + str(words_on_current_page) + ", we have " + str(cumulative) + " out of " + str(total_words) + " words.")
        # Get link to the next page
        np = ul.find_next('a', string = "next page")
        if (not np):
            done = 1
        else:
            url_params = '&' + np['href'].split("&", 1)[1] # we are only interested in after the &
        # Example : href="/w/index.php?title=Category:Spanish_verbs&pagefrom=ACITRONAR%0Aacitronar#mw-pages"
        #time.sleep(1)
        if ( count == max_pages ):
            done = 1
        count += 1

    print(text_div)

# Problems:
# Multiple languages sometimes appear here
# Multiple IPA pronunciations, sometimes only one in a different language but id is still Pronunciation
# (so for example if we just grabbed pronunciation, it would be the one from the other language)
# Multiple definitions for a given pos. Iterate through them, but sometimes they contain synonyms or quotes
# That will be part of the list item, so we can't just grab that.
# Multiple pos.
# Sometimes multiple etymologies, https://en.wiktionary.org/wiki/%D0%B0%D0%B7%D1%83
# It's a mess :) https://en.wiktionary.org/wiki/abandonar#Pronunciation_2
# Goal:
# Only look under the language we are interested in
# Ignore etymology
# Grab first IPA phonetic pronunciation or a later one if it matches
# Look for the definitions (only for the pos specified)
# Since there are multiple, try get top 3.

def check_language(node, permissable):
    if(permissable):
        return 0
    previous_h2 = node.find_previous('h2')
    previous_heading = previous_h2.find_next('span', class_="mw-headline")
    if(previous_heading["id"] != language):
        return 1
    return 0

def get_definition(num, words, pbar, mutex):
    with mutex:
        print(bcolors.OKCYAN + "DEBUG:: Starting thread " + str(num) + " for words from " + words[0] + " to " + words[len(words)-1] + bcolors.ENDC)
    slowdown = 0 # in ms, each thread has its own instance
    good_response = 0
    thread_prefix = str(num) + ': '

    for word in words:
        url = def_url + word.replace(" ", "_")

        while(not good_response):
            time.sleep(slowdown)
            response = download_page(url)
            if response.status_code == 200:
                good_response = 1
            elif response.status_code == 429:
                slowdown += 50/1000
            else:
                debug_filename = "wiktionary_webscraper_" + time_str() + ".html"
                log(bcolors.FAIL, thread_prefix, "ERROR:: See " + debug_filename + ". No good response from url? " + url + bcolors.ENDC)
                with open(debug_filename, 'w', encoding='utf-8') as file:
                    file.write(response.text)
                break
        
        if(not good_response):
            continue # try next word

        soup = BeautifulSoup(response.text, 'html.parser')
        language_id = soup.find('span', class_="mw-headline", id=language) # Language heading we search under
        # If we can't find anything then just accept the first heading, sometimes the headings are wrong. eg https://en.wiktionary.org/w/index.php?title=torcer_las_palabras&oldid=73513100
        other_language = 0
        if(not language_id):
            language_id = soup.find('span', class_="mw-page-title-main") # search from top heading, not language heading
            other_language = 1
            # HANDLE THIS PROPERLY

        # We will do the IPA first
        # https://en.wiktionary.org/wiki/abalanzar#Spanish
        # Example of multiple ipas
        # This is another example but of a dropdown. Not considered:
        # https://en.wiktionary.org/wiki/ababillarse

        pronunciation_id = language_id.find_next('span', id=re.compile("Pronunciation" + r".*"))

        ipa_phonemic = 0
        ipa_phonetic = 0
        ipa_geo_match = 0
        ipa = ""
        audio_path = ""
        if(pronunciation_id):
            if(check_language(pronunciation_id, other_language)):
                log(bcolors.OKCYAN, thread_prefix, "DEBUG:: We found a pronunciation, but not under our language, so ignore")
            else:
                pronunciation_ul = pronunciation_id.find_next('ul')

                # We get the first IPA we can and store it
                # Then if there is a square bracket one, store that instead,
                # Just sit with the first IPA until we encounter something better, so if we encounter nothing better we have the top of the list
                # If geos are enabled, add the correct geo one. After, we get from the "ipa" variable, which represents our best find
                for pronunciation_item in pronunciation_ul.find_all('li'):

                    # Just get the first one so we have something
                    ipa_span = pronunciation_item.find('span', class_="IPA", string=re.compile(r"\/.*\/"))
                    if(ipa_span and not ipa_phonemic):
                        ipa = ipa_span.text
                        ipa_phonemic = 1 # So we don't override on later ones

                    # Now we are only matching IPAs with square brackets because of string param
                    ipa_span = pronunciation_item.find('span', class_="IPA", string=re.compile(r"\[.*\]"))
                    if(ipa_span and not ipa_phonetic):
                        ipa = ipa_span.text
                        ipa_phonetic = 1

                    # For each IPA list item
                    # See if it has brackets at the front with the geography, like (Latin America)
                    
                    geo = pronunciation_item.find('span', class_="ib-content qualifier-content")
                    if(geo):
                        # See if it matches our pattern if we have one
                        if (ipa_pattern != ""):
                            match = re.search(ipa_pattern, geo.text)
                            if(match):
                                log(bcolors.OKCYAN, thread_prefix, "DEBUG:: IPA Match for " + word + ": " + geo.text)
                                # Great, use this line
                                ipa_span = pronunciation_item.find('span', class_="IPA", string=re.compile(r"\/.*\/"))
                                if(ipa_span):
                                    ipa = ipa_span.text

                                ipa_span = pronunciation_item.find('span', class_="IPA", string=re.compile(r"\[.*\]"))
                                if(ipa_span):
                                    ipa = ipa_span.text
                            
                            # If there is no match, we will end up trying again on the next line (line as in line on the webpage)

                    # Now the audio, still under the Pronunciation header
                    audio = pronunciation_item.find('audio')
                    if(audio):
                        audio_filename = audio["data-mwtitle"]
                        audio_path = audio_dir + '/' + audio_filename
                        # examples of src attribute
                        # //upload.wikimedia.org/wikipedia/commons/transcoded/a/ad/LL-Q1321_%28spa%29-Millars-perra.wav/LL-Q1321_%28spa%29-Millars-perra.wav.mp3
                        # or
                        # //upload.wikimedia.org/wikipedia/commons/a/ad/LL-Q1321_%28spa%29-Millars-perra.wav
                        # You can see the transcoded version as well, which we aren't considering
                        # src attribute from last source tag, looked like it was the original source not transcoded
                        audio_url = "http://" + audio.find_all('source')[-1]["src"][2:]
                        audio_received = download_page(audio_url)
                        if (audio_received.status_code != 200):
                            log(bcolors.FAIL, thread_prefix, "ERROR:: " + audio_url + '\n' + str(audio_received.status_code))
                        if not os.path.exists(audio_dir):
                            os.makedirs(audio_dir)
                        with open(audio_path, 'wb') as f:
                            f.write(audio_received.content)

        # Now the definition
        pos_without_s = str.capitalize(pos[:-1]) # This just strips last letter e.g: Verbs to Verb
        pos_id = language_id.find_next('span', id=re.compile(pos_without_s + r".*")) # Sometimes it is Verb_3
        if not(pos_id):
            log(bcolors.FAIL, thread_prefix, "ERROR:: No definition found for " + word + " looking under " + pos_without_s)
            continue # Go onto next word
        # Again make sure it's under our language
        if(check_language(pos_id, other_language)):
            log(bcolors.OKCYAN, thread_prefix, "DEBUG:: We found a definition, but not under our language, so ignore")
            # Idk when this would ever happen, would require there to be no definition for our language (but still a language header)
        else:
            # Find the next ordered list
            pos_def = pos_id.find_next('ol')
            defs=[]
            i = 0
            for definition in pos_def.find_all('li'):
                # I'd like to loop until I hit something which doesn't look like a definition
                # but find_all wasn't returning the text which is sitting there not part of a tag (#text)
                # There is an arbitrary length of *stuff* optionally followed by synonyms or quotations which starts with a span tag for the toggle thing
                # https://en.wiktionary.org/wiki/abacorar
                # https://en.wiktionary.org/wiki/abanderar
                # If something gets included which shouldn't it's probably a new thing being encountered and needs to somehow be excluded from the list item

                # Look one tag up to check if it is an unordered list, if so it is a quotation and not a definition
                if (definition.find_parent().name == "ul"):
                    continue
                
                # get only the first line. This is a cheap way to avoid synonyms since they appear on the second line
                defs.append(definition.text.partition('\n')[0])

                # only get number_of_defs
                i += 1
                if(i >= number_of_defs):
                    break


        word = str.capitalize(word)

        # Done, now create line with desired format
        line = word + seperator + ipa

        for def_number in range(number_of_defs):
            # Empty def if we don't have one to use
            definition = " "
            if(def_number < len(defs)):
                definition = defs[def_number]
            line = line + seperator + definition

        # add audio
        if(audio_path != ""):
            line = line + seperator + "[sound:" + audio_filename + "]"
        else:
            line = line + " " + seperator

        # write to file (thread safe)
        # can monitor with something like
        # watch -n0.5 'tail spanish_verbs.txt && wc -l spanish_verbs.txt'
        with mutex:
            with open(filename, 'a', encoding='utf-8') as file:
                file.write(line + '\n')
        pbar.update(1)
        #time.sleep(1)
    return 0


# Process command-line arguments
if(len(sys.argv) == 1):
    sys.argv.append("--color=auto") # Default

for i in range(1, len(sys.argv)):
    if(sys.argv[i][0:8] == "--color="):
        val = sys.argv[i][8:]
        if(val == "always"):
            bcolors = bcolors_real
            colored_log = 1
        elif(val == "auto"):
            if sys.stdout.isatty():
                bcolors = bcolors_real
            else:
                bcolors = bcolors_stub
        elif(val == "never"):
            bcolors = bcolors_stub
        else:
            print("Unrecognised value: " + val)
            exit(1)            
    else:
        print("Unrecognised option: " + sys.argv[i])
        exit(1)


startup()

# Open our file to append to
filename = str.lower(language) + '_' + str.lower(pos) + '_' + time_str()
log_filename = filename + "_log.txt"
filename = filename + ".txt"
# split words into equal chunks
chunk_size = math.ceil(len(words) / number_of_threads)
words_chunks = []
progress_bars = []

# Construct progress bars and create words chunks
for i in range(0, len(words), chunk_size):
    words_chunks.append(words[i:i+chunk_size])
    if i+chunk_size > len(words):
        chunk_size -= ((i+chunk_size)-len(words))
    progress_bars.append(tqdm(desc=str(int(i/chunk_size)+1)+": ", total=chunk_size, unit='w', delay=1))

with concurrent.futures.ThreadPoolExecutor(max_workers=number_of_threads) as executor:
    futures = {executor.submit(get_definition, i+1, words_chunk, progress_bars[i], mutex) for i, words_chunk in enumerate(words_chunks)}
    for future in concurrent.futures.as_completed(futures):
        try:
            log(bcolors.OKCYAN, "0: " , f"DEBUG:: Task returned: {future.result()} for thread{i+1}")
        except Exception as e:
            log(bcolors.FAIL, "0: ", f"ERROR:: An error occurred in the future: {e}")
            traceback.print_exc()