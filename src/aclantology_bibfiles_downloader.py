#!/usr/bin/env python3.6

"""
This script downloads the summarized bib files for all the ACL-anthology volumes available.
 - shared URL for the anthology: https://aclanthology.coli.uni-saarland.de/
 - URL to the list of volumes: https://aclanthology.coli.uni-saarland.de/volumes/
 
Aim: The bib-files can be imported into a reference management software (e.g. JabRef).

Author: emm (mujdricza@cl.uni-heidelberg.de)
Last Version: 20180524

Licence: This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/.

"""

from enum import Enum
import os
import re
import sys
import urllib.request


class FORMAT(Enum):
    """Some format constants."""
    SLASH = "/"
    HELP_OPTION = ["-h", "h", "--help"]
    
    
class HTML(Enum):
    """Constants for the target html pages (ACL Anthology)."""
    VOLUME_URL_STEM = "https://aclanthology.coli.uni-saarland.de/volumes"
    VOLUME_URL_STEM_CLOSED = VOLUME_URL_STEM + FORMAT.SLASH.value

    HREF_VOLUMES_PATTERN = re.compile('<a href="/volumes/(?P<volume>[^"]+)"')
    HREF_VOLUME_GROUP = "volume"
    
    EXTENSION_HTML = ".html"
    EXTENSION_BIB = ".bib"
    A_HREF_STRING = "<a href="
    PAGINATION_STRING = "?page="
    LAST_PAGE = 32 # amount of pages available (to date), but this constraint is not necessarily used
    
    
class LOCAL(Enum):
    """Customizable constants for the downloaded data."""
    OUTPUT_PATH = "../outputs/data_acl/"
    OUTPUT_SUBFOLDER_VOLUMEOVERVIEWS = "volume-overviews" + FORMAT.SLASH.value
    TMP_FILENAME = "tmp.html"
    OUTPUT_SUBFOLDER_BIBS = "bibs" + FORMAT.SLASH.value
    PAGE = "page"
    KEEP_FILES_CMDL_OPTION = "keep"

def extract_volume_urls(
    local_fn_volumeoverview_html,
    target_url_stem=HTML.VOLUME_URL_STEM_CLOSED.value,
    href_string=HTML.A_HREF_STRING.value,
    href_pattern=HTML.HREF_VOLUMES_PATTERN.value,
    href_group=HTML.HREF_VOLUME_GROUP.value):
    """Extracts the list of websites with the volume overview.
    
    Example input and output:
    
    input_html: https://aclanthology.coli.uni-saarland.de/volumes?page=5
    in the html file find parts like: <td><a href="/volumes/computational-linguistics-formerly-the-american-journal-of-computational-linguistics-volume-12-number-1-january-march-1986">
    then extract: https://aclanthology.coli.uni-saarland.de/volumes/computational-linguistics-formerly-the-american-journal-of-computational-linguistics-volume-12-number-1-january-march-1986
    """
    volume_urls = []
    pattern_volume = href_pattern
    
    file = open(local_fn_volumeoverview_html)
    lines = file.readlines()
    file.close()
    
    for line in lines:
        if href_string in line:
            match = pattern_volume.search(line)
            if match is not None:
                #value of the href attribute -- part of an url
                vol = match.group(href_group)
                
                # extend it to the whole target url with the volume
                vol = target_url_stem + vol
                
                volume_urls.append(vol)
    return volume_urls

def extract_volume_overviews(
    output_path,
    output_temp_fn=None,
    url_stem=HTML.VOLUME_URL_STEM.value,
    pagination_mark=HTML.PAGINATION_STRING.value,
    last_page=None):
    """Extracts the urls for the ACL volumes from the ACL Anthology overview pages.
    
    The overview pages are downloaded in a temporary file which will be deleted as soon as not used any more.
    
    Example for the relevant html lines in one of the overview pages:
        <td><a href="/volumes/computational-linguistics-formerly-the-american-journal-of-computational-linguistics-volume-12-number-1-january-march-1986">
    From this line, the following url will be extracted:
        https://aclanthology.coli.uni-saarland.de/volumes/computational-linguistics-formerly-the-american-journal-of-computational-linguistics-volume-12-number-1-january-march-1986
    On this url, the whole volume is listed, and the bib file for the volume.
    """
    
    if last_page == 0:
        sys.exit("(No pages requested, done.)")
    
    local_fn = output_temp_fn # if filled: only a temporary file; if None: the file will be kept permanently
    
    if local_fn is None:
        os.makedirs(output_path, exist_ok=True)
        output_path = __normalize_path_end(output_path)
    
    list_of_volume_urls = []
    
    step = 1
    current_page_idx = 0
    #next_page = last_page if last_page is not None else current_page+1
    has_next_page = __has_next_page(last_page, current_page_idx)
    pn = last_page if last_page is not None else "all"
    s = "" if last_page == 1 else "s"
    print(f"download bib files for {pn} page{s} of the URL={url_stem}")
    
    while has_next_page:
        if output_temp_fn is None:
            local_fn = output_path + LOCAL.PAGE.value + str(current_page_idx) + HTML.EXTENSION_HTML.value
            
        download_url = url_stem + pagination_mark + str(current_page_idx)
        local_fn_ov_retrieved, headers = urllib.request.urlretrieve(download_url, filename=local_fn)
        print(f"downloaded url: {download_url}")
    
        volume_urls = extract_volume_urls(local_fn_ov_retrieved)
        if volume_urls:
            print(f"--> extracted {len(volume_urls)} volume_urls")
            list_of_volume_urls.extend(volume_urls)
            #next_page += step
        else:
            print(f"(No more volumes detected, break searching process.)")
            has_next_page = False
            break
        current_page_idx += step
        has_next_page = __has_next_page(last_page, current_page_idx)
    
    if output_temp_fn is not None:
        os.remove(local_fn)
        print(f"(Local file {local_fn} removed.)")
    
    return list_of_volume_urls


def __has_next_page(last_nr, current_idx):
    
    if last_nr is None:
        return True
    if last_nr > current_idx: #Note that we use last page number, but current page index
        return True
    return False
    


def download_volume_bib(volume_url, bib_extension=".bib", output_folder="./"):
    os.makedirs(output_folder, exist_ok=True)
    
    bib_url = volume_url + bib_extension
    bib_fn = bib_url.split("/")[-1] #get the last splitpart=filename
    local_bib_fn = output_folder + bib_fn
    
    local_bib_retrieved, headers = urllib.request.urlretrieve(bib_url, local_bib_fn)


def __normalize_path_end(path):
    return path if path.endswith(FORMAT.SLASH.value) else path + FORMAT.SLASH.value


def __interpret_cleaning_requirements(string):
    return False if string.lower() == LOCAL.KEEP_FILES_CMDL_OPTION.value else True


def main_download_acl_bibs(output_path, delete_overviews=True, input_url_stem=HTML.VOLUME_URL_STEM.value, last_page=None):
    
    print(f"Extract names of volume urls from {input_url_stem}.")
    
    os.makedirs(output_path, exist_ok=True)
    
    temp_ovfn = None if delete_overviews == False else output_path + LOCAL.TMP_FILENAME.value
    
    list_of_volume_urls = extract_volume_overviews(
        output_path = output_path + LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEWS.value,
        output_temp_fn = temp_ovfn, #if None: all the files will be downloaded and kept
        url_stem = input_url_stem,
        pagination_mark = HTML.PAGINATION_STRING.value,
        last_page = last_page # None for automatic detection; HTML.LAST_PAGE.value or a custom number for a given amount of pages to download
    )
    
    urllen = len(list_of_volume_urls)
    print(f"\n=> Extracted {urllen} volume urls.")
    
    print(f"\nDownload the bib file for volumes.")
    problematic_bibs = []
    for idx, volume_url in enumerate(list_of_volume_urls):
        print(f"- export bib from {volume_url} ({idx+1}/{urllen})")
        try:
            download_volume_bib(
                volume_url = volume_url,
                bib_extension = HTML.EXTENSION_BIB.value,
                output_folder = output_path + LOCAL.OUTPUT_SUBFOLDER_BIBS.value
            )
        except:
            print(f"\tError -> skip")
            problematic_bibs.append(volume_url)
    
    if problematic_bibs:
        print(f"\n!!! There are {len(problematic_bibs)} not downloaded bib entries:")
        for problematic_bib in problematic_bibs:
            print(f"- {problematic_bib}")

    
def __usage(args):
    msg = f"Usage: python3.6 {args[0]} [output_path] [(clean|keep)]\n" \
          f"\n" \
          f"e.g. python {args[0]} ../outputs/acl_data keep > ../outputs/out_acl_bib.txt\n" \
          f"\n" \
          f"Notes:\n" \
          f"- use >= python 3.6\n" \
          f"- output path is optional, it will be created if needed\n" \
          f"- if the last option is given, and it is set to 'keep' then temporary files will be kept; otherwise, those files will be removed\n" \
          f"  (last option is currently recognized only if the output_path is also given)" #TODO
    
    sys.exit(msg)

if __name__ == "__main__":
    
    # usage e.g.:
    # $ python download_bibfiles_aclantology.py acl_data keep > out_acl_bib.txt
    args = sys.argv

    output_path = LOCAL.OUTPUT_PATH.value #default
    delete_overviews = True
    if len(args) > 1:
        if args[1] in FORMAT.HELP_OPTION.value:
            __usage(args)
        
        output_path = __normalize_path_end(args[1])
        
    if len(args) > 2:
        delete_overviews = __interpret_cleaning_requirements(args[2])
    
    
    print(f"OUTPUT PATH: {output_path}")
    
    if delete_overviews:
        print(f"- OVERVIEW PAGES will be removed automatically.")
    else:
        print(f"- TARGET PATH FOR OVERVIEW PAGES: {output_path + LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEWS.value}")
    
    print(f"- TARGET PATH FOR BIB FILES: {output_path + LOCAL.OUTPUT_SUBFOLDER_BIBS.value}")
    
    ## download bib files for all pages and volumes available
    main_download_acl_bibs(output_path, delete_overviews=delete_overviews, last_page=None)
    
    print("(DONE)")

