#!/bin/bash

# Version 20191209
# Contact see README.md
#
# This script downloads all bib-files for all conferences/workshops collected on the ACL-Anthology website
# in bib-files for each decade.
# Use at least python3.6 !

#PYTHON=python3
PYTHON=python3.7

decades=( 1960 1970 1980 1990 2000 2010 )
#decades=( 1960 )

for i in "${decades[@]}"; do :
   j=$((i+9))
   echo "Downloading ACL-Anthology bibs for years $i - $j"
   cmd="$PYTHON ./aclanthology_bibfiles_downloader.py -o ../outputs/outputs_$i-$j/ -l download_$i-$j.log -Y $i-$j -f True -c all_$i-$j.bib"
   echo ${cmd} ;
   ${cmd}
done

echo "(done script)"