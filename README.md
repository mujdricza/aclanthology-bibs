# Overview

This mini project downloads bib files for ACL-anthology volumes.

The anthology is available here: [https://aclanthology.coli.uni-saarland.de/](https://aclanthology.coli.uni-saarland.de/)

The list of volumes is accessable from this URL: [https://aclanthology.coli.uni-saarland.de/volumes/](https://aclanthology.coli.uni-saarland.de/volumes/)

The downloaded files with the bib-entries can be imported into a reference management software (e.g. JabRef).

# Prerequisites

Use at least python 3.6.

# Use

e.g. 
```
$ python aclantology_bibfiles_downloader.py 

usage: aclantology_bibfiles_downloader.py [-h] -o OUTPUT_PATH
                                             [-f DO_KEEP_OVERVIEW_FILES]
                                             [-y YEAR]

downloads bib files for the journals of ACL anthology

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_PATH        path for the downloaded bib files -- it will be reused
                        if already existing
  -f DO_KEEP_OVERVIEW_FILES
                        whether to keep intermediate overview files (if True:
                        keep them in a subfolder, else they will be deleted at
                        the end of the process)
  -y YEAR               optional argument for downloading bibfiles for one
                        particular year; format: yyyy

```

(Details see in code. If you only want to download the first _n_ pages, adjust the variable _last_page_ in the code.)

# Contact

Eva Mujdricza-Maydt (mujdricza@cl.uni-heidelberg.de)


# Licence

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit [http://creativecommons.org/licenses/by-sa/4.0/](http://creativecommons.org/licenses/by-sa/4.0/).