#!/usr/bin/env python3.6 or newer

"""
This script downloads the summarized bib files for all the ACL-anthology volumes available.
Entry points:
 - shared URL for the anthology:    https://aclanthology.info/
 - URL to the list of volumes:      https://aclanthology.info/volumes/

Aim:
The bib-files can be imported into a reference management software (e.g. JabRef).

Default behaviour:
Download all bib-entries for all volumes of all journals/proceedings in the ACL anthology as linked in the volumes overview table.

Options:
- Select a particular year (-y) or a year range (-Y).
- Select a particular journal/proceeding (-a, -i) or a list of journals/proceedings (-A, -I).
- Concatenate all bib-files into one file additionally (-c).
- Keep the overview files temporarily downloaded (-f).
- Give another logging file name than 'download.log' (-l).
- (Search for only some of the volume-pages (-p).)
- TODO: Post-processing option: Reformat the bib-entries:
  * Generate a key more readable for me with pattern: <AUTHOR(S)>[Etal]_<YEAR>_<TITLEWORDS>-<ABBREV>_<ID>
  * Replace apostroph template with brace template, additionally, escape title information in doubled braces.


Author: emm (mujdricza@cl.uni-heidelberg.de)
Last Version: 20190203 (previous versions: 20180921, 20180524, ...)

Licence: This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/.

TODO:
- post-processing
- update some of the DocStrings with new examples

FIXME:
- The conferences with url-identifying letter "W" are not differenciable! -- concerning all SIGs! (See utils.py / LETTER2ACRONYM_DICT and ACRONYM2LETTER_DICT)

"""

import argparse
from enum import Enum
import os
import re
import sys
import urllib.request
import logging

    
# local imports
from utils import FORMAT
from utils import HTML
from utils import URL
from utils import LOCAL
from utils import RESTRICTIONS
from utils import ACRONYM2LETTER_DICT


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
        ...
      </tr>
      ...
     </tbody>
    
    """
    
    file = open(local_fn_volumeoverview_html) # one page of the volume overviews
    lines = file.readlines()
    file.close()
    
    # take the tbody part (assumption: there is only one table with tbody)
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
        logger.log(logging.DEBUG, f"Empty table in file '{local_fn_volumeoverview_html}'")
        return volume_urls
    
    volume_urls = []
    pattern_volume = href_pattern
    
    # no restrictions --> simple extraction of all volumes
    if restrictions is None:
        logger.log(logging.DEBUG, f"No restriction -- take all volumes.")
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
        logger.log(logging.INFO, f"Restrict download to specific year and/or venue: {restrictions}")
    
        # take only the relevant part of the html site:
        is_tr = False
        td_counter = 0
        tmp_vol = None
        dropped_due_to_restrictions = False
        
        for line in tbodylines:
            #take the second td for volume url name, and the forth td for year information
            
            if line == HTML.TR_OPENING.value:
                is_tr = True
                td_counter = 0
                dropped_due_to_restrictions = False
                tmp_vol = None
            elif line == HTML.TR_CLOSING.value:
                is_tr = False
                if tmp_vol is not None and not dropped_due_to_restrictions:
                    volume_urls.append(tmp_vol)
                    tmp_vol = None
            
            elif is_tr:
                if line.startswith(HTML.TD_OPENING.value):
                    td_counter += 1
                    
                    if td_counter == 2 and not dropped_due_to_restrictions: # volume name
                    
                        match = pattern_volume.search(line)
                        if match is not None:
                            # value of the href attribute -- part of an url
                            vol = match.group(href_group)
    
                            # extend it to the whole target url with the volume
                            tmp_vol = target_url_stem + vol
    
                    elif tmp_vol is not None and \
                        td_counter == 4 and \
                        __has_year_restrictions(restrictions): # volume year
                        
                        match = HTML.TD_PATTERN.value.search(line)
                        if match is not None:
                            year_str = match.group(HTML.TD_INFO_GROUP.value)
                            year = int(year_str)
                            
                            if not __is_relevant_year(year, restrictions):
                                tmp_vol = None
                        else:
                            msg = f"Not recognized year information in line:\n{line}"
                            raise ValueError(msg)
                    
                    elif td_counter == 1 and \
                        __has_venue_restrictions(restrictions):
                        
                        match = HTML.TD_PATTERN.value.search(line)
                        if match is not None:
                            venue_id, venue_year = __extract_current_venue_and_year(match.group(HTML.TD_INFO_GROUP.value))
                            if not __is_relevant_venue(venue_id, restrictions):
                                tmp_vol = None
                                dropped_due_to_restrictions = True
                            elif not __is_relevant_year(venue_year, restrictions):
                                tmp_vol = None
                                dropped_due_to_restrictions = True

                            else:
                                dropped_due_to_restrictions = False
                        else:
                            msg = f"Not recognized venue information in line:\n{line}"
                            raise ValueError(msg)
                else:
                    pass # nothing to do
                    
    return volume_urls # filled with urls, or empty (or previously set to None and returned for the case the website is empty)



def __has_year_restrictions(restriction_dict=None):
    
    __HAS_YEAR_RESTRICTIONS = None
    if __HAS_YEAR_RESTRICTIONS is None:
        
        if restriction_dict is None:
            __HAS_YEAR_RESTRICTIONS = False
        else:
            years = restriction_dict.get(RESTRICTIONS.YEARS.value, RESTRICTIONS.ALL.value)
            
            if years == RESTRICTIONS.ALL.value:
                __HAS_YEAR_RESTRICTIONS = False
            else:
                __HAS_YEAR_RESTRICTIONS = True
    
    return __HAS_YEAR_RESTRICTIONS

def __is_relevant_year(current_year, restriction_dict=None):
    
    if restriction_dict is None:
        return True

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


def __has_venue_restrictions(restriction_dict=None): #TODO
    __HAS_VENUE_RESTRICTIONS = None
    if __HAS_VENUE_RESTRICTIONS is None:
        if restriction_dict is None:
            __HAS_VENUE_RESTRICTIONS = False
        else:
            venues = restriction_dict.get(RESTRICTIONS.VENUES.value, RESTRICTIONS.ALL.value)
        
            if venues == RESTRICTIONS.ALL.value:
                __HAS_VENUE_RESTRICTIONS = False
            else:
                __HAS_VENUE_RESTRICTIONS = True
    
    return __HAS_VENUE_RESTRICTIONS
    
    
def __is_relevant_venue(current_venue_id, restriction_dict=None):
    if restriction_dict is None:
        return False
    
    venues = restriction_dict.get(RESTRICTIONS.VENUES.value, RESTRICTIONS.ALL.value)
    
    if venues == RESTRICTIONS.ALL.value:
        return True
    
    elif isinstance(venues, str):
        return current_venue_id == venues
    elif isinstance(venues, list):
        return current_venue_id in venues
    else:
        msg = f"Not handled venue restrictions: {venues}"
        raise NotImplementedError(msg)


def __extract_current_venue_and_year(raw_volume_string):
    """e.g. A00-1"""
    
    id = None
    year = None
    
    match = HTML.VENUEID_PATTERN.value.search(raw_volume_string)
    if match is not None:
        id = match.group(HTML.VENUEID_ID_GROUP.value)
        year = __extract_year_from_shortyear(match.group(HTML.VENUEID_SHORTYEAR_GROUP.value))
    
    if id is None or year is None:
        msg = f"Not recognized venue information in raw volume string:\n{raw_volume_string}"
        raise ValueError(msg)
        
    return id, year


def __extract_year_from_shortyear(shortyear_str):
    """Extracts the yy-formatted year information to a yyyy-formatted year information.
    Range of years correctly handled: 1960-2059
    """
    
    y1y2 = "19"
    y3, y4 = [int(y) for y in shortyear_str]
    
    if y3 < 6:  # OBSERVATION: first conference from the 60's
        y1y2 = "20"  # ASSUMPTION: no conferences yet after 2059
    else:
        pass
    
    yyyy = int(y1y2 + str(y3) + str(y4))
    
    return yyyy


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
    has_next_page = __has_next_page(last_page, current_page_idx)
    pn = last_page if last_page is not None else "all"
    s = "" if last_page == 1 else "s"
    logger.log(logging.INFO, f"Download bib files for {pn} page{s} of the URL={url_stem}")
    
    while has_next_page:
        if output_temp_fn is None:
            local_fn = output_path + LOCAL.PAGE.value + str(current_page_idx) + HTML.EXTENSION_HTML.value
            
        download_url = url_stem + pagination_mark + str(current_page_idx)
        local_fn_ov_retrieved, headers = urllib.request.urlretrieve(download_url, filename=local_fn)
        logger.log(logging.INFO, f"Downloaded url: {download_url}")
        
        volume_urls = extract_volume_urls(local_fn_ov_retrieved, restrictions=restrictions)
        if volume_urls is None:
            logger.log(logging.INFO, f"(No more volumes detected, break searching process.)")
            has_next_page = False
            break
        else:
            logger.log(logging.INFO, f"--> extracted {len(volume_urls)} volume_urls")
            list_of_volume_urls.extend(volume_urls)
        
            
        current_page_idx += step
        has_next_page = __has_next_page(last_page, current_page_idx)
    
    if output_temp_fn is not None:
        os.remove(local_fn)
        logger.log(logging.INFO, f"(Local file {local_fn} removed.)")
    
    return list_of_volume_urls


def __has_next_page(last_nr, current_idx):
    
    if last_nr is None:
        return True
    if last_nr > current_idx: #Note that we use last page number, but current page index
        return True
    return False
    
    
def __normalize_path_end(path):
    return path if path.endswith(FORMAT.SLASH.value) else path + FORMAT.SLASH.value


def download_volume_bib(volume_url, bib_extension=".bib", output_folder="./"):
    os.makedirs(output_folder, exist_ok=True)
    
    bib_url = volume_url + bib_extension
    bib_fn = bib_url.split("/")[-1] #get the last splitpart=filename
    local_bib_fn = output_folder + bib_fn
    
    local_bib_retrieved, headers = urllib.request.urlretrieve(bib_url, local_bib_fn)
    
    return local_bib_retrieved



def __extract_restrictions(parsed_arguments):
    
    if parsed_arguments is None:
        return None
    
    # note that list arguments are prioritized over single-valued ones
    restrictions_dict = {}
    
    #YEARS
    year = parsed_arguments.year
    years = parsed_arguments.years
    
    if years:
        try:
            from_year, to_year = years.split(FORMAT.HYPHEN.value)
            if len(from_year) != 4 or len(to_year) != 4:
                msg = f"NOT ASSUMED YEAR RANGE: {years}"
                raise ValueError(msg)
            from_year = int(from_year)
            to_year = int(to_year)
        except ValueError as ve:
            msg = f"NOT ASSUMED YEAR RANGE: {years}"
            raise ValueError(msg)
        restrictions_dict[RESTRICTIONS.YEARS.value] = [int(y) for y in range(from_year, to_year+1, 1)]
    elif year:
        if len(str(year)) != 4:
            msg = f"NOT ASSUMED YEAR FORMAT: {year}"
            raise ValueError(msg)
        try:
            year = int(year)
        except ValueError as ve:
            msg = f"NOT RECOGNIZED AS YEAR: {year}"
            raise ValueError(msg)
        restrictions_dict[RESTRICTIONS.YEARS.value] = int(year)
    
    #VENUES -- NOTE that all options will be normalized to one venue restriction based on the given letter identifying the venue in the paper url
    letter = parsed_arguments.venue_idletter
    letters = parsed_arguments.venue_idletters
    venue = parsed_arguments.venue_acronym
    venues = parsed_arguments.venue_acronyms
    if letters:
        restrictions_dict[RESTRICTIONS.VENUES.value] = [v.upper() for v in letters.strip().split(FORMAT.SPACE.value)]
    elif venues:
        restrictions_dict[RESTRICTIONS.VENUES.value] = [
            ACRONYM2LETTER_DICT[v.lower()]
            if v.lower() in ACRONYM2LETTER_DICT else __raiseKeyError(f"NOT FOUND VENUE: '{v}'")
            for v in venues.strip().split(FORMAT.SPACE.value)]
    elif letter:
        restrictions_dict[RESTRICTIONS.VENUES.value] = letter.upper()
    elif venue:
        restrictions_dict[RESTRICTIONS.VENUES.value] = ACRONYM2LETTER_DICT[venue.lower()] if venue.lower() in ACRONYM2LETTER_DICT else __raiseKeyError(f"NOT FOUND VENUE: '{venue}'")
    
    return restrictions_dict


def __raiseKeyError(msg):
    raise KeyError(msg)


def main_download_acl_bibs(output_path, keep_overviews, concatenated_filename=None, restrictions=None, input_url_stem=HTML.VOLUME_URL_STEM.value, last_page=None):
    """Main function."""
    
    logger.log(logging.INFO,  f"Extract names of volume urls from {input_url_stem}.")
    
    os.makedirs(output_path, exist_ok=True)
    
    temp_ovfn = output_path + LOCAL.TMP_FILENAME.value if keep_overviews == False else None
    
    if not restrictions:
        logger.log(logging.INFO, f"no restrictions")
    else:
        logger.log(logging.INFO, f"restriction dict: {restrictions}")
    
    
    list_of_volume_urls = extract_volume_overviews(
        output_path = output_path + LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEWS.value,
        output_temp_fn = temp_ovfn, #if None: all the files will be downloaded and kept
        url_stem = input_url_stem,
        pagination_mark = HTML.PAGINATION_STRING.value,
        last_page = last_page, # None for automatic detection; HTML.LAST_PAGE.value or a custom number for a given amount of pages to download
        restrictions = restrictions
    )
    
    urllen = len(list_of_volume_urls)
    logger.log(logging.INFO, f"\n=> Extracted {urllen} volume urls.")
    
    logger.log(logging.INFO, f"\nDownload the bib file for volumes.")
    problematic_bibs = []
    downloaded_bibs = []
    for idx, volume_url in enumerate(list_of_volume_urls):
        logger.log(logging.INFO, f"- export bib from {volume_url} ({idx+1}/{urllen})")
        
        try:
            local_bib_filename = download_volume_bib(
                volume_url = volume_url,
                bib_extension = HTML.EXTENSION_BIB.value,
                output_folder = output_path + LOCAL.OUTPUT_SUBFOLDER_BIBS.value
            )
            downloaded_bibs.append(local_bib_filename)
        except:
            logger.log(logging.INFO, f"\tError -> skip")
            problematic_bibs.append(volume_url)
    
    if problematic_bibs:
        logger.log(logging.INFO, f"\n!!! There are {len(problematic_bibs)} not downloaded bib files:")
        for problematic_bib in problematic_bibs:
            logger.log(logging.INFO, f"- {problematic_bib}")
    
    if concatenated_filename is not None:
        allbib = output_path + concatenated_filename
        logger.log(logging.INFO, f"\nConcatenate {len(downloaded_bibs)} bib-files into '{allbib}'.")
        with open(allbib, "w") as fout:
            for local_bib_fn in downloaded_bibs:
                #print(local_bib_fn)
                with open(local_bib_fn) as fin:
                    text = fin.read()
                    
                    fout.write(f"\n\n@comment{{BIB-entries from '{local_bib_fn}'.}}\n\n")
                    fout.write(text)
                    fout.write("\n")
    
    
    
def load_argument_parser(print_help=False):
    """Loads the command line arguments, or print the help message.
    
    :param print_help: whether to print the help message
    :return: ArgumentParser according to the command line arguments
    """
    
    parser = argparse.ArgumentParser(
        description=f'downloads bib files for the journals/proceedings of ACL anthology from {URL.ROOT.value}')
    
    if print_help:
        parser.print_help()
    else:
    
        parser.add_argument(
            '-o', dest="output_path", type=str, required=True,
            help='required argument: path for the downloaded bib files -- it will be reused if already existing')
        parser.add_argument(
            '-f', dest="do_keep_overview_files", type=str, default="True",
            help='whether to keep intermediate overview files (if True (default): keep them in a subfolder, else they will be deleted at the end of the process)')
        parser.add_argument(
            '-l', dest="log_file", type=str, default="download.log",
            help='name for the log-file; default: download.log')
        
        parser.add_argument('-c', dest="concatenated_file", type=str, default=None,
            help='name for an (optional) output file concatenating all the downloaded bib-files into a common one; the file will be saved into the path given by the positional argument -o --output_path')
        parser.add_argument('-p', dest="last_venue_page", default=None,
            help='optional argument (use only if needed, e.g. debugging): it gives the last relevant page of the venue overview -- if not set (default), just all pages listing venues will be read')
        
        parser.add_argument('-y', dest="year", type=int, default=None,
            help="optional argument for downloading bibfiles for one particular year; format: yyyy")
        parser.add_argument('-Y', dest="years", default=None,
            help="optional argument for downloading bibfiles for a range of years; format: 'yyyy-yyyy'")
        
        parser.add_argument('-a', dest="venue_acronym", type=str, default=None,
            help="optional argument for downloading bibfiles for one particular venue; use the acronym, e.g. acl or ACL (case-insensitive)")
        parser.add_argument('-A', dest="venue_acronyms", default=None,
            help="optional argument for downloading bibfiles for more than one venues, format: list the acronyms separated by space within apostrophs, e.g. 'acl cl tacl'")
        
        parser.add_argument('-i', dest="venue_idletter", type=str, default=None,
            help="optional argument for downloading bibfiles for one particular venue; use the letter identifying the venue, e.g. 'P' for ACL")
        parser.add_argument('-I', dest="venue_idletters", default=None,
            help="optional argument for downloading bibfiles for more than one venues, format: list the letters separated by space within apostrophs, e.g. 'P J Q'")
        
    return parser


if __name__ == "__main__":

    
    #LOG
    logger = logging.getLogger("biblogger")
    #logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    
    args_raw = sys.argv
    
    if len(args_raw) < 2:
        load_argument_parser(print_help=True)
        sys.exit(1)
    
    argparser = load_argument_parser()
    args = argparser.parse_args()
    
    output_path = args.output_path  # new files
    output_path = __normalize_path_end(output_path)
    
    do_keep_overview_files = args.do_keep_overview_files
    do_keep_overview_files = False if do_keep_overview_files == "False" else True
    
    concatenated_filename = args.concatenated_file
    
    last_page = args.last_venue_page
    
    logfile = args.log_file
    logpath = output_path
    os.makedirs(os.path.realpath(logpath), exist_ok=True)
    logger.addHandler(logging.FileHandler(logfile, "w"))
    
    logger.log(logging.DEBUG, f"Recognized command line arguments: {args}")
    
    #EXTRACT RESTRICTIONS
    restrictions_dict = __extract_restrictions(args)
    
    logger.log(logging.DEBUG, f"Extracted restrictions: {restrictions_dict}.")
    
    logger.log(logging.INFO, f"RUN: {' '.join(args_raw)}\n")
    
    msg_output = f"Downloading bib files into '{output_path}'."
    msg_logfile = f"Log will be written into '{logfile}'."
    
    msg_restriction_years = "Downloading bibs across all years."
    msg_restriction_venues = "Downloading bibs from all conferences/journals."
    
    if restrictions_dict:
        logger.log(logging.DEBUG, f"Restrictions for the download: {restrictions_dict}.")
        if RESTRICTIONS.YEARS.value in restrictions_dict:
            msg_restriction_years = f"Downloading bibs from the following year(s): {restrictions_dict[RESTRICTIONS.YEARS.value]}"
        if RESTRICTIONS.VENUES.value in restrictions_dict:
            msg_restriction_venues = f"Downloading bibs from the venue(s) with url-letter(s): {restrictions_dict[RESTRICTIONS.VENUES.value]}"

    msg_keepov = f"The overview files will be saved in subfolder '{LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEWS.value}'" if do_keep_overview_files else f"Temporary files will be removed at the end of the downloading process."
    msg_concat = f"Output bib-files will be concatenated and saved in '{output_path}{LOCAL.OUTPUT_CONCATENATED_FILENAME.value}' additionally to the files in subfolder '{LOCAL.OUTPUT_SUBFOLDER_BIBS.value}'." if concatenated_filename else f"Output bib-files are saved in subfolder '{LOCAL.OUTPUT_SUBFOLDER_BIBS.value}'."
    msg_lastpage = f"Searching for relevant bibs on all venue-pages." if last_page is None else  f"Searching for relevant bibs on the first venue-page only." if last_page == '1' else f"Searching for relevant bibs on the first {last_page} venue-pages."
    msg = f"{msg_output}\n- {msg_restriction_years}\n- {msg_restriction_venues}\n- {msg_concat}\n- {msg_lastpage}\n- {msg_keepov}\n\n"
    
    logger.log(logging.INFO, msg)
    
    #RUN DOWNLOAD PROCESS
    main_download_acl_bibs(output_path, keep_overviews=do_keep_overview_files, concatenated_filename=concatenated_filename, restrictions=restrictions_dict, last_page=last_page)
    
    logger.log(logging.INFO, "(DONE)")


    