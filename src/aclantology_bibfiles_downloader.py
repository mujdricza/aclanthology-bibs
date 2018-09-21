#!/usr/bin/env python3.6

"""
This script downloads the summarized bib files for all the ACL-anthology volumes available.
 - shared URL for the anthology: https://aclanthology.coli.uni-saarland.de/
 - URL to the list of volumes: https://aclanthology.coli.uni-saarland.de/volumes/

Option: downloading only the volumes of a particular year (see load_argument_parser() below).
 
Aim: The bib-files can be imported into a reference management software (e.g. JabRef).

Author: emm (mujdricza@cl.uni-heidelberg.de)
Last Version: 20180921 (previous versions: 20180524, ...)

Licence: This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/.

Todo: options: a range of years, a list of journals

"""

import argparse
#from configparser import ConfigParser
from enum import Enum
import os
import re
import sys
import urllib.request


class FORMAT(Enum):
    """Some format constants."""
    SLASH = "/"

    
class HTML(Enum):
    """Constants for the target html pages (ACL Anthology)."""
    VOLUME_URL_STEM = "https://aclanthology.coli.uni-saarland.de/volumes"
    VOLUME_URL_STEM_CLOSED = VOLUME_URL_STEM + FORMAT.SLASH.value

    TBODY_OPENING = "<tbody>" # NOTE assumption: there is one and only one table with tbody
    TBODY_CLOSING = "</tbody>"
    HREF_VOLUMES_PATTERN = re.compile('<a href="/volumes/(?P<volume>[^"]+)"')
    HREF_VOLUME_GROUP = "volume"
    TR_OPENING = "<tr>"
    TR_CLOSING = "</tr>"
    TD_OPENING = "<td>"
    TD_PATTERN = re.compile('<td>(?P<info>[^<]+?)</td>')
    TD_INFO_GROUP = "info"
    
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


class RESTRICTIONS(Enum):
    YEARS = "years"
    JOURNALS = "journals"
    ALL = "all"
    

def extract_volume_urls(
    local_fn_volumeoverview_html,
    target_url_stem=HTML.VOLUME_URL_STEM_CLOSED.value,
    href_string=HTML.A_HREF_STRING.value,
    href_pattern=HTML.HREF_VOLUMES_PATTERN.value,
    href_group=HTML.HREF_VOLUME_GROUP.value,
    restrictions=None # if None --> download all volume urls, else it is a dictionary with restrictive information like relevant year or years, relevant journal or journals
    ):
    """Extracts the list of websites with the volume overview.
    
    Example input and output:
    
    input_html: https://aclanthology.coli.uni-saarland.de/volumes?page=5
    in the html file find parts like: <td><a href="/volumes/computational-linguistics-formerly-the-american-journal-of-computational-linguistics-volume-12-number-1-january-march-1986">
    then extract: https://aclanthology.coli.uni-saarland.de/volumes/computational-linguistics-formerly-the-american-journal-of-computational-linguistics-volume-12-number-1-january-march-1986
    
    e.g. a whole line with all information about the given volume:
    <tbody>
      <tr>
        <td>J84-2</td>
        <td><a href="/volumes/computational-linguistics-formerly-the-american-journal-of-computational-linguistics-volume-10-number-2-april-june-1984">Computational Linguistics. Formerly the American Journal of Computational Linguistics, Volume 10, Number 2, April-June 1984</a></td>
        <td></td>
        <td>1984</td>
        <td></td>
        <td><a href="http://aclweb.org/anthology/J84-2">http://aclweb.org/anthology/J84-2</a></td>
<!-- , :target => "_blank" -->
        <!--  -->
        <!-- <td>
          <a class="btn btn-mini btn-primary" href="/volumes/computational-linguistics-formerly-the-american-journal-of-computational-linguistics-volume-10-number-2-april-june-1984"><span class="translation_missing" title="translation missing: en.helpers.links.view">View</span></a>
          <a class="btn btn-mini" href="/volumes/computational-linguistics-formerly-the-american-journal-of-computational-linguistics-volume-10-number-2-april-june-1984/edit">Edit</a>
          <a class="btn btn-mini btn-danger" data-confirm="Are you sure?" data-method="delete" href="/volumes/computational-linguistics-formerly-the-american-journal-of-computational-linguistics-volume-10-number-2-april-june-1984" rel="nofollow">Delete</a>
        </td> -->
      </tr>
      ...
      
    
    """
    
    
    file = open(local_fn_volumeoverview_html)
    lines = file.readlines()
    file.close()
    
    # take the tbody part (assumption: there is only one table with tbody
    tbodylines = []
    is_relevant_part = False
    for line in lines:
        line = line.strip()
        if not is_relevant_part:
            if line == HTML.TBODY_OPENING.value:
                is_relevant_part = True
        else:
            if line == HTML.TBODY_CLOSING.value:
                break  # break since no further info is relevant
            tbodylines.append(line)

    
    # if no content --> break the process
    if len(tbodylines) < 1:
        volume_urls = None
        print(f"Empty table in file '{local_fn_volumeoverview_html}'")
        return volume_urls
    
    volume_urls = []
    pattern_volume = href_pattern
    
    # no restrictions --> simple extraction of all volumes
    if restrictions is None:
        print(f"No restriction -- take all volumes.")
        for line in tbodylines:
            if href_string in line:
                match = pattern_volume.search(line)
                if match is not None:
                    #value of the href attribute -- part of an url
                    vol = match.group(href_group)
                    
                    # extend it to the whole target url with the volume
                    vol = target_url_stem + vol
                    
                    volume_urls.append(vol)
    
    else:
        print(f"Restrict download to specific year.")
    
        # take only the relevant part of the html site:
        is_tr = False
        td_counter = 0
        tmp_vol = None
        
        for line in tbodylines:
            #take the second td for volume url name, and the forth td for year information
            
            #print(line)
            if line == HTML.TR_OPENING.value:
                is_tr = True
                #print(f"--- TMP tr opening: {line}")
            elif line == HTML.TR_CLOSING.value:
                is_tr = False
                td_counter = 0
                if tmp_vol is not None:
                    volume_urls.append(tmp_vol)
                    #print(f"--- TMP tr closing, volume: {tmp_vol}")
                    tmp_vol = None
                #else:
                #    print(f"--- TMP tr closing, No volume found")
            
            elif is_tr:
                #print(f"--- TMP within tr: {line}")
                if line.startswith(HTML.TD_OPENING.value):
                    td_counter += 1
                    
                    #print(f"--- TMP td_counter={td_counter}")
                    
                    if td_counter == 2: # volume name
                        match = pattern_volume.search(line)
                        if match is not None:
                            # value of the href attribute -- part of an url
                            vol = match.group(href_group)
    
                            # extend it to the whole target url with the volume
                            tmp_vol = target_url_stem + vol
                            #print(f"--- TMP VOLUME: {tmp_vol}")
    
                    elif tmp_vol is not None and \
                        td_counter == 4 and \
                        __has_year_restrictions(restrictions): # volume year
                        
                        match = HTML.TD_PATTERN.value.search(line)
                        if match is not None:
                            year_str = match.group(HTML.TD_INFO_GROUP.value)
                            year = int(year_str)
                            
                            if not __is_relevant_year(year, restrictions):
                                tmp_vol = None
                                #print(f"--- TMP VOLUME: {tmp_vol} is not of the relevant year: {line}")
                            #else:
                            #    print(f"--- TMP VOLUME with year: {tmp_vol}")
                        else:
                            msg = f"Not recognized year information in line:\n{line}"
                            raise ValueError(msg)
                else:
                    pass # nothing to do
                    
    return volume_urls # filled with urls, or empty (or previously set to None and returned for the case the website is empty)




def __has_year_restrictions(restriction_dict=None):
    
    if restriction_dict is None:
        return False
    
    years = restriction_dict.get(RESTRICTIONS.YEARS.value, RESTRICTIONS.ALL.value)
    
    if years == RESTRICTIONS.ALL.value:
        return False
    else:
        return True


def __is_relevant_year(current_year, restriction_dict=None):
    
    if restriction_dict is None:
        return False

    years = restriction_dict.get(RESTRICTIONS.YEARS.value, RESTRICTIONS.ALL.value)

    if years == RESTRICTIONS.ALL.value:
        return True
    elif isinstance(years, int):
        return current_year == years
    elif isinstance(years, list):
        return current_year in years
    else:
        msg = f"Not handled year restrictions: {years}"
        raise NotImplementedError(msg)
    


def extract_volume_overviews(
    output_path,
    output_temp_fn=None,
    url_stem=HTML.VOLUME_URL_STEM.value,
    pagination_mark=HTML.PAGINATION_STRING.value,
    last_page=None,
    restrictions=None):
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
        
        volume_urls = extract_volume_urls(local_fn_ov_retrieved, restrictions=restrictions)
        if volume_urls is None:
            print(f"(No more volumes detected, break searching process.)")
            has_next_page = False
            break
        else:
            print(f"--> extracted {len(volume_urls)} volume_urls")
            list_of_volume_urls.extend(volume_urls)
            #next_page += step
        
            
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


def main_download_acl_bibs(output_path, keep_overviews=True, years=None, input_url_stem=HTML.VOLUME_URL_STEM.value, last_page=None):
    
    print(f"Extract names of volume urls from {input_url_stem}.")
    
    os.makedirs(output_path, exist_ok=True)
    
    temp_ovfn = output_path + LOCAL.TMP_FILENAME.value if keep_overviews == False else None
    
    restrictions = None
    if years is not None:
        restrictions = {}
        restrictions[RESTRICTIONS.YEARS.value] = years
        print(f"restriction dict: {restrictions}")
    else:
        print(f"no restrictions")
    
    
    
    list_of_volume_urls = extract_volume_overviews(
        output_path = output_path + LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEWS.value,
        output_temp_fn = temp_ovfn, #if None: all the files will be downloaded and kept
        url_stem = input_url_stem,
        pagination_mark = HTML.PAGINATION_STRING.value,
        last_page = last_page, # None for automatic detection; HTML.LAST_PAGE.value or a custom number for a given amount of pages to download
        restrictions = restrictions
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



def load_argument_parser(print_help=False):
    """
    Loads the command line arguments, or print the help message.
    
    :param print_help: whether to print the help message
    :return: ArgumentParser according to the command line arguments
    """
    
    parser = argparse.ArgumentParser(
        description='downloads bib files for the journals of ACL anthology')
    
    if print_help:
        parser.print_help()
    else:
    
        parser.add_argument(
            '-o', dest="output_path", type=str, required=True,
            help='path for the downloaded bib files -- it will be reused if already existing')
        parser.add_argument(
            '-f', dest="do_keep_overview_files", type=bool, default=True,
            help='whether to keep intermediate overview files (if True: keep them in a subfolder, else they will be deleted at the end of the process)')
        parser.add_argument('-y', dest="year", type=int, default=None,
            help="optional argument for downloading bibfiles for one particular year; format: yyyy")
    
    return parser

if __name__ == "__main__":
    
    args_raw = sys.argv
    
    output_path = None # all outputs will be written into this folder -- reused if already existing
    do_keep_overview_files = None # keep or delete overview files
    last_page = None

    if len(args_raw) < 2:
        load_argument_parser(print_help=True)
        sys.exit(1)
    
    argparser = load_argument_parser()
    args = argparser.parse_args()
    output_path = args.output_path  # new files
    do_keep_overview_files = args.do_keep_overview_files
    year = args.year
    
    main_download_acl_bibs(output_path, keep_overviews=do_keep_overview_files, years=year, last_page=last_page)
    
    print("(DONE)")

