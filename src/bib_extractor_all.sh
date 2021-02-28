#!/bin/bash

# Version 20210228; 20191201
# Contact see README.md
#
# This script downloads all bib-files for all conferences/workshops collected on the ACL-Anthology website.
# Use at least python3.6 !

PYTHON=python3

cmd="$PYTHON ./aclanthology_bibfiles_downloader.py -o ../outputs/ -l download_allbib.log -f -c all.bib"
echo $cmd
$cmd

echo "(done script)"
