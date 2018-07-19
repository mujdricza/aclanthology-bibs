# Overview

This mini project downloads bib files for ACL-anthology volumes.

The anthology is available here: [https://aclanthology.coli.uni-saarland.de/](https://aclanthology.coli.uni-saarland.de/)

The list of volumes is accessable from this URL: [https://aclanthology.coli.uni-saarland.de/volumes/](https://aclanthology.coli.uni-saarland.de/volumes/)

The downloaded files with the bib-entries can be imported into a reference management software (e.g. JabRef).

# Prerequisites

Use at least python 3.6.

# Use

e.g. 
> python3.6 aclantology_bibfiles_downloader.py ../outputs/data_acl_exp/ keep > ../outputs/data_acl_exp/out_downloadall_keep.txt

(Details see in code. If you only want to download the first _n_ pages, adjust the variable _last_page_ in the code.)

# Contact

Eva Mujdricza-Maydt (mujdricza@cl.uni-heidelberg.de)


# Licence

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit [http://creativecommons.org/licenses/by-sa/4.0/](http://creativecommons.org/licenses/by-sa/4.0/).