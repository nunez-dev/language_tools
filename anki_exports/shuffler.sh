#!/bin/bash

# Usage ./shuffler.sh Everythingburger.txt viet
# seperator is 5 spaces, dodgy
sep=$(perl -e 'print " " x 5')

total_entries=0
chunk_size=0
current_entry_buffer=""
MONTHS=(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec)

current_entry=1
current_chunk=1
# 1st pass to find out how many entries 
while IFS="" read -r p || [ -n "$p" ]
do
    if [ "$p" = "${sep}" ]; then
        # tab encountered, update
        total_entries=$((total_entries+1))
    fi
done < $1

# 2nd pass randomise in ./rand/
# Done by writing to 1 file per entry with filename equal to random number [1,total_entries]
# entries are multiline, distinguished by a single 5 space line
mkdir -p ./rand/
random_order=( $(shuf -i 1-"${total_entries}") )
while IFS="" read -r p || [ -n "$p" ]
do
    if [ "$p" = "${sep}" ]; then
        entry_filename=./rand/"${random_order[$current_entry]}"
        echo "${entry_filename}"
        echo "${current_entry_buffer}" > "${entry_filename}"
        current_entry_buffer=""
        current_entry=$(($current_entry+1))
    fi
    # below command is extremely slow
    current_entry_buffer=$(echo -e "${current_entry_buffer}\n${p}")
done < $1

current_entry=1 # reset

# split into 12 files, read our randomised entries
# Once we hit the final multiple of 12, go back to the Jan file and deal out one by one
# We do this by making chunk size 1
echo "total_entries: $total_entries"
chunk_size=$((total_entries/12))
echo "chunk_size: $chunk_size"

while IFS="" read -r p || [ -n "$p" ]
do
    month_index=$(($current_chunk-1))
    echo "$p" >> "./${2}_${MONTHS[$month_index]}.txt"
    if [ "$p" = "${sep}" ]; then
        # tab encountered, update
        if [ $(($current_entry % $chunk_size)) == 0 ]; then
            current_chunk=$(($current_chunk+1))
            # recalibrate for remainders
            if [ $((current_chunk)) == 13 ]; then
                current_chunk=1
                current_entry=1
                chunk_size=1
            fi
        fi
        current_entry=$(($current_entry+1))
    fi
done < <(cat ./rand/*)

echo "Done"
rm -r ./rand