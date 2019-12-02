#!/bin/bash

# OLD Version 20190203
# This script downloads all bib-files for all conferences/workshops according to their identifying "letters" in the URL.
# E.g. the file name of a paper from the ACL-conference begins with a "P".
# The output path is specific to the given conference (or conference group) ../outputs/bibs/bibs_${letter}_${acronym}/
# Use at least python3.6 !

PYTHON=python3

LETTERS=(A C D E F I J L M N O P Q R S T U W X Y)
ACRONYMS=(anlp coling emnlp eacl jep-taln-recital ijcnlp cl lrec muc naacl_hlt rocling-ijclclp acl tacl ranlp semeval tinlap alta SIGs tipster paclic)

for i in "${!LETTERS[@]}"; do
  letter=${LETTERS[$i]}
  acronym=${ACRONYMS[$i]}
  
  echo "${letter} = ${acronym}"
  cmd="$PYTHON ./aclanthology_bibfiles_downloader.py -o ../outputs/bibs/bibs_${letter}_${acronym}/ -l ../outputs/bibs/bibs_${letter}_${acronym}/download.log -f False -i ${letter} -c all_${letter}_${acronym}.bib"
  echo $cmd
  $cmd
done
echo "(done)"