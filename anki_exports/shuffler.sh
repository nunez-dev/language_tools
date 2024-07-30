#!/bin/bash

# Usage ./shuffler.sh Everythingburger.txt viet
sep='"'

total_entries=0
chunk_size=0
current_entry_buffer=''
MONTHS=(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec)

current_entry=1
current_chunk=1

rm -r ./rand
mkdir -p ./rand/

# get metadata
grep '^#' $1 > ./rand/meta.txt
file=${1}_processed
sed -i '/^#.*/d' $file

# preprocessing, remove heading on each card
sed 's/\"<.*/\"<div><\/div>/g' $1 > $file

# 1st pass to find out how many entries
while IFS="" read -r p || [ -n "$p" ]
do
    if [ "$p" = "${sep}" ]; then
        # sep encountered, update
        total_entries=$((total_entries+1))
    fi
done < $file

# 2nd pass randomise in ./rand/
# Done by writing to 1 file per entry with filename equal to random number [0,total_entries-1]
# entries are multiline, distinguished by a single 5 space line
random_order=( $(shuf -i 1-"${total_entries}") )
while IFS="" read -r p || [ -n "$p" ]
do
    if [ "$p" = "${sep}" ]; then
        current_entry_buffer=$(echo -e "${current_entry_buffer}\n${p}")
        entry_filename=./rand/"${random_order[$current_entry-1]}"
        echo "${entry_filename}"
        echo "${current_entry_buffer}" > "${entry_filename}"
        current_entry_buffer=''
        current_entry=$(($current_entry+1))
    else
        # below command is extremely slow
        current_entry_buffer=$(echo -e "${current_entry_buffer}\n${p}")
    fi
done < $file

current_entry=1 # reset

# split into 12 files, read our randomised entries
# Once we hit the final multiple of 12, go back to the Jan file and deal out one by one
# We do this by making chunk size 1
echo "total_entries: $total_entries"
chunk_size=$((total_entries/12))
echo "chunk_size: $chunk_size"

rm -r ./${2}_output
mkdir -p ./${2}_output
while IFS="" read -r p || [ -n "$p" ]
do
    month_index=$(($current_chunk-1))
    echo "$p" >> "./${2}_output/${month_index}_${2}_${MONTHS[$month_index]}.txt"
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
done < <(cat ./rand/[0-9]*)

for local_file in ./${2}_output/*; do
    echo -e "$(cat ./rand/meta.txt)\n$(cat $local_file)" > $local_file
done

echo "Done in ./${2}_output"
rm $file
rm -r ./rand