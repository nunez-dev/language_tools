import requests
from bs4 import BeautifulSoup
import re
import time
import concurrent.futures
import threading
import math
import traceback
import os, errno
from datetime import datetime

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
# File ends up unsorted but gnu sort fixes that (would have to be done manually).

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Globals
# Takes about 13 minutes on 40 threads (one second delay per word) to get ~10k words
# which is all spanish verbs
default_number_of_threads = 10
number_of_threads = 0
seperator = ' | '
words_url = "https://en.wiktionary.org/w/index.php?title=Category:"
def_url = "https://en.wiktionary.org/wiki/"
global_words_url = ""
url_params = ""
text_div = '-'*60
current_letter = ''
words = []
total_words = 0
words_on_current_page = 0
number_of_defs = 3
done = 0
count = 0
mutex = threading.Lock() # For writing to file
max_pages = 1000000 # used for testing, lower if you only want first x pages of words
debug_filename = "wiktionary_webscraper_" + str(datetime.now().time()) + ".dump"

def download_page(url):
    response = requests.get(url)
    return response

print(bcolors.HEADER + __file__ + bcolors.ENDC)

# These should all be functions but aren't, main starts here basically

while(True):
    try:
        raw_in = input("How many threads (default:10)? ")
        number_of_threads = int(raw_in)
    except ValueError as e:
        if(raw_in == ''):
            number_of_threads = default_number_of_threads
            break
        else: 
            print(e)
        continue
    number_of_threads = default_number_of_threads
    break
        

# Make sure page exists
page = False
while(not page):
    
    language = str.capitalize(input("What language? "))
    pos = str.lower(input("What part of speech/lemma?\n(see %s_lemmas ) " % (words_url + language)))

    global_words_url = words_url + language + '_' + pos
    print(global_words_url + '\n')

    response = download_page(global_words_url)

    if (response.status_code != 200):
        print("Error: ", end="")
    else:
        print("Success: ", end="")
        page = True
    
    print("Url returned " + str(response.status_code))
    print(text_div)

# Now we know this works we can keep using this url
while(not done):

    words_on_current_page = 0 # reset this

    url = global_words_url + url_params
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
# Grab first IPA pronunciation or none at all
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

# Open our file to append to
filename = str.lower(language) + '_' + str.lower(pos) + '_' + str(datetime.now().time()) + ".txt"

def get_definition(num, words, mutex):
    print(bcolors.OKCYAN + "DEBUG:: Starting thread " + str(num) + " for words from " + words[0] + " to " + words[len(words)-1] + bcolors.ENDC)
    for word in words:
        url = def_url + word.replace(" ", "_")
        response = download_page(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        language_id = soup.find('span', class_="mw-headline", id=language) # Language heading we search under
        # If we can't find anything then just accept the first heading. eg https://en.wiktionary.org/wiki/torcer las palabras
        # Spanish word but has english heading
        other_language = 0
        if(not language_id):
            # If there are other problems we log it anyway but assuming it is just heading issue
            print(bcolors.FAIL + "See " + debug_filename + ". No good response from url? " + url + bcolors.ENDC)
            with open(debug_filename, 'w', encoding='utf-8') as file:
                file.write(response.text)
            language_id = soup.find('span', class_="mw-page-title-main") # search from top heading, not language heading
            other_language = 1

        # We will do the IPA first
        pronunciation_id = language_id.find_next('span', id=re.compile("Pronunciation" + r".*"))

        ipas = []
        if(pronunciation_id):
            if(check_language(pronunciation_id, other_language)):
                print(bcolors.OKCYAN + "DEBUG:: We found a pronunciation, but not under our language, so ignore" + bcolors.ENDC)
            else:
                pronunciation_ul = pronunciation_id.find_next('ul')
                for pronunciation_item in pronunciation_ul.find_all('li'):
                    try:
                        for ipa_span in pronunciation_item.find_all('span', class_="IPA"):
                            ipas.append(ipa_span.string)
                            break # If you wanted to do more ipas remove this
                    except TypeError as e:
                        print("No IPA")

        # Now the definition
        pos_without_s = str.capitalize(pos[:-1]) # This just strips last letter e.g: Verbs to Verb
        pos_id = language_id.find_next('span', id=re.compile(pos_without_s + r".*")) # Sometimes it is Verb_3
        # Again make sure it's under our language
        if(check_language(pos_id, other_language)):
            print(bcolors.OKCYAN + "DEBUG:: We found a definition, but not under our language, so ignore" + bcolors.ENDC)
            # Idk when this would ever happen, would require there to be no definition for our language
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
                    continue;
                
                # get only the first line. This is a cheap way to avoid synonyms since they appear on the second line
                defs.append(definition.text.partition('\n')[0])

                # only get number_of_defs
                i += 1
                if(i >= number_of_defs):
                    break
        
        # Some post processing, turn [ipa] into /ipa/
        i = 0
        for single_ipa in ipas:
            ipas[i] = '/' + single_ipa[1:-1] + '/'
            i += 1

        if len(ipas) == 0:
            final_ipa = ''
        else:
            final_ipa = ipas[0]

        word = str.capitalize(word)

        # Done, now create line with desired format
        line = word + seperator + final_ipa

        for def_number in range(number_of_defs):
            # Empty def if we don't have one to use
            definition = " "
            if(def_number < len(defs)):
                definition = defs[def_number]
            line = line + seperator + definition

        #print(bcolors.OKBLUE + url + bcolors.ENDC)
        print("THREAD " + str(num) + '\n' + bcolors.OKBLUE + url + bcolors.ENDC + '\n' + bcolors.OKGREEN + line + bcolors.ENDC)

        # write to file (thread safe)
        # can monitor with something like
        # watch -n0.5 'tail spanish_verbs.txt && wc -l spanish_verbs.txt'
        with mutex:
            with open(filename, 'a', encoding='utf-8') as file:
                file.write(line + '\n')
        #time.sleep(1)
    print(bcolors.OKCYAN + "DEBUG:: Closing thread " + str(num) + bcolors.ENDC)


# The following is mostly from chatgpt for how to split up the list and call ThreadPoolExecutor
# split words into equal chunks
chunk_size = math.ceil(len(words) / number_of_threads)
words_chunks = [words[i:i+chunk_size] for i in range(0, len(words), chunk_size)]
with concurrent.futures.ThreadPoolExecutor(max_workers=number_of_threads) as executor:
    futures = {executor.submit(get_definition, i, words_chunk, mutex) for i, words_chunk in enumerate(words_chunks)}
    for future in concurrent.futures.as_completed(futures):
        try:
            print(f"Task completed: {future.result()}")
        except Exception as e:
            print(f"An error occurred in the future: {e}")
            traceback.print_exc()