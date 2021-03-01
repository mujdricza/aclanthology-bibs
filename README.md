
# ACL-ANTHOLOGY BIB-DOWNLOADER

[https://gitlab.cl.uni-heidelberg.de/mujdricza/aclanthology-bibs.git](https://gitlab.cl.uni-heidelberg.de/mujdricza/aclanthology-bibs.git)

## Overview

This mini project downloads bib files for ACL-anthology volumes.

The anthology is available here: <https://www.aclweb.org/anthology>

The list of volumes is accessable from this URL: <https://www.aclweb.org/anthology/volumes/>

The downloaded files with the bib-entries for each volume can be imported into a reference management software (e.g. JabRef).

## Prerequisites

Use at least **python 3.6** .

## Use downloader

Navigate to the python script `aclanthology_bibfiles_downloader.py`.
```
$ cd /path/to_the/aclanthology-bibs/src/
```

Usage message:
```
$ python src/aclanthology_bibfiles_downloader.py -h
usage: aclanthology_bibfiles_downloader.py [-h] -o OUTPUT_PATH [-f] [-k] [-l LOG_FILE] [-c CONCATENATED_FILE]
                                           [-y YEAR] [-Y YEARS] [-a VENUE_ACRONYM] [-A VENUE_ACRONYMS]
                                           [-i VENUE_IDLETTER] [-I VENUE_IDLETTERS]

downloads bib files for the journals/proceedings of ACL anthology from https://www.aclweb.org/anthology/.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_PATH        required argument: path for the downloaded bib files -- it will be reused if already existing;
                        The individual bib-files will be saved in a subfolder of the given output_path called bibs/.
  -f                    optional argument for additional formatting of the bib-entries. If set, reformatting is done:
                        the quoted values will be replaced with curly braces, the title with doubled curly braces. See
                        code for more details.
  -k                    optional argument; if set, the intermediate overview files will be kept in a subfolder called
                        "volume-overview/"; otherwise they will be deleted as soon as possible.
  -l LOG_FILE           name for the log-file; default: download.log; The file will be saved in the current
                        output_path, thus, give only the pure file name for the log-file.
  -c CONCATENATED_FILE  name for an (optional) output file concatenating all the downloaded bib-files into a common
                        one; the file will be saved into the output_path
  -y YEAR               optional argument for downloading bibfiles for one particular year; format: yyyy
  -Y YEARS              optional argument for downloading bibfiles for a range of years; format: yyyy-yyyy
  -a VENUE_ACRONYM      optional argument for downloading bibfiles for one particular venue; use the acronym, e.g. acl
                        or ACL (case-insensitive)
  -A VENUE_ACRONYMS     optional argument for downloading bibfiles for more than one venues, format: list the acronyms
                        separated by space within apostrophs, e.g. 'acl cl tacl'
  -i VENUE_IDLETTER     optional argument for downloading bibfiles for one particular venue; use the letter
                        identifying the venue, e.g. P for ACL
  -I VENUE_IDLETTERS    optional argument for downloading bibfiles for more than one venues, format: list the letters
                        separated by space within apostrophs, e.g. 'P J Q'

Minimal use: python3 aclanthology_bibfiles_downloader.py -o <output_path> --> Extracts all bib files into <output_path>/bibs/.

```

E.g.

```
$python3.6 aclanthology_bibfiles_downloader.py -o ../outputs/bibs_all_acl/ -f -k -c all_acl.bib -a acl
```
Extracts the bib files for all ACL conferences (with url starting letter 'P') into the output subfolder `../outputs/bibs_all_acl/bibs/` keeping also the overview files for each volume, and saving an additional bib-file `../outputs/bibs_all_acl/all_acl.bib` containing all the downloaded bib-entries. The bib-entries will be reformatted with curly brackets instead of quotation marks for the values.


```
$python3.6 aclanthology_bibfiles_downloader.py -o ../outputs/bibs_acl+tacl_2010-2018/  -I 'P Q' -Y 2010-2018 -l acl+tacl_2010-2018.log 
```
Extracts the bib files for ACL and TACL conferences (with url starting letter 'P' and 'Q') from the years 2010 to 2018 (inclusive) into the output subfolder `../outputs/bibs_acl+tacl_2010-2018/bibs/`, the log file will be written into `../outputs/bibs_acl+tacl_2010-2018/acl+tacl_2010-2018.log`. The folder for the volume overview will be deleted.

## Use reformatter

For reformatting an already downloaded bib-file, use 
`$ python aclanthology_bibfiles_reformatter.py <input_bib> <output_reformatted_bib>`


## Contact

Eva Mujdricza-Maydt (mujdricza@cl.uni-heidelberg.de, me.levelek@gmx.de)

## Verions

- V20210228
  * boolean arguments:
     * argument for keeping overview files 
     * reformatting bib
  * also adapt volumes with pattern `yyyy.name-subcat`, e.g.: `2020.coling-main`
  * separate script for reformatting bib-files

- V20191209
  * augmenting the reformatter
  * explicit reformatter (see main-part, not yet documented)
  
- V20191201
  * renewing code for current ACL-Anthology website
  * small bugfixes
  * reformatting bib entries: replace qutation marks with curly brackets
  * extracting all "letter IDs" and acronyms" -- but without long conference names (see utils.py)

- V20190203
  * all or restricted downloads
  * concatenating bib files

## Licence

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit [http://creativecommons.org/licenses/by-sa/4.0/](http://creativecommons.org/licenses/by-sa/4.0/).
