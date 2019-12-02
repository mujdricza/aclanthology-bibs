#!/usr/bin/env python3.6 or newer

"""

This script downloads the summarized bib files for all the ACL-anthology volumes available.
Entry points:
 - shared URL for the anthology:    https://www.aclweb.org/anthology/
 - URL to the list of volumes:      https://www.aclweb.org/anthology/volumes/

Aim:
The bib-files can be imported into a reference management software (e.g. JabRef).

Default behaviour:
Download all bib-entries for all volumes of all journals/proceedings in the ACL anthology as linked in the volumes overview table.

Options:
- Select a particular year (-y) or a year range (-Y).
- Select a particular journal/proceeding (-a, -i) or a list of journals/proceedings (-A, -I).
- Concatenate all bib-files into one file additionally (-c).
- Keep the overview files which will be temporarily downloaded during the extraction process (-f).
- Give another logging file name than 'download.log' (-l).


Author: emm (mujdricza@cl.uni-heidelberg.de)
Last Version: 20191201 (previous versions: 20190203, 20180921, 20180524, ...)

Licence: This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/.

TODO:
- post-processing: Reformat the bib-entries:
  * Generate a key more readable for me with pattern: <AUTHOR(S)>[Etal]_<YEAR>_<TITLEWORDS>-<ABBREV>_<ID>
  * Replace apostroph template with brace template, additionally, escape title information in doubled braces.
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
from lxml import etree, html
from shutil import copy as shutil_copy


    
# local imports
from utils import FORMAT
from utils import HTML
from utils import URL
from utils import LOCAL
from utils import RESTRICTIONS
from utils import ACRONYM2LETTER_DICT
from utils import BIB


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
    
    input_html: https://www.aclweb.org/anthology/volumes/
        (Note that all conferences are listed on one page)
    in the html file find parts like:
    <li><a href=/anthology/volumes/S12-1/>*SEM 2012: The First Joint Conference on Lexical and Computational Semantics – Volume 1: Proceedings of the main conference and the shared task, and Volume 2: Proceedings of the Sixth International Workshop on Semantic Evaluation (SemEval 2012)</a></li>
    then extract:
    https://www.aclweb.org/anthology/volumes/anthology/volumes/S12-1/
    
    The html file contains all conferences in a list within the tag main:
    ... <div id=main-container class=container><main aria-role=main><h2 id=title>List of all volumes</h2><hr><ul><li><a href=/anthology/volumes/S12-1/>*SEM 2012: The First Joint Conference on Lexical and Computational Semantics – Volume 1: Proceedings of the main conference and the shared task, and Volume 2: Proceedings of the Sixth International Workshop on Semantic Evaluation (SemEval 2012)</a></li><li><a href=/anthology/volumes/E03-1/>10th Conference of the European Chapter of the Association for Computational Linguistics</a></li><li> ... </main></div> ...
    """
    
    file = open(local_fn_volumeoverview_html) # one page of the volume overviews
    lines = file.readlines()
    file.close()
    
    #NOTE that the newer files are squeezed into a few lines --> break them up into multiple lines
    lines = prettify_lines(lines)
    
    # take the "main" part (assumption: there is only one tag with the name "main")
    mainlines = []
    is_relevant_part = False
    for line in lines:
        line = line.strip()
        if is_relevant_part is False:
            if line.startswith(HTML.MAIN_OPENING_BEGIN.value):
                is_relevant_part = True
        else:
            if line == HTML.MAIN_CLOSING.value:
                break  # break since no further info is relevant
            if line.startswith(HTML.A_HREF_STRING.value):
                mainlines.append(line)
    
    
    volume_urls = []
    pattern_volume = href_pattern
    
    #first, extract all possible volume URLs
    for line in mainlines:
        if href_string in line:
            match = pattern_volume.search(line)
            if match is not None:
                #value of the href attribute -- part of an url
                vol = match.group(href_group)
                
                # extend it to the whole target url with the volume
                vol = target_url_stem + vol
                
                volume_urls.append(vol)
            else:
                if "volumes" in line:
                    msg = f"Not extracted volume URL from '{href_string}' in line '{line}' by pattern '{pattern_volume}'."
                    raise ValueError(msg)
    
    #print(f">> all volume_urls: {len(volume_urls)}")
    
    # no restrictions --> simple extraction of all volumes
    relevant_volume_urls = []
    if restrictions is None or not restrictions:
        logger.log(logging.DEBUG, f"No restriction -- take all volumes.")
        relevant_volume_urls = volume_urls
    
    else:
        logger.log(logging.INFO, f"Restrict download to specific year and/or venue: {restrictions}")
    
        dropped_due_to_restrictions = False
        
        for tmp_vol in volume_urls:
            match = HTML.VENUEID_PATTERN.value.search(line)
            
            if match is not None:
                venue_id, venue_year = __extract_current_venue_and_year(tmp_vol)
            else:
                msg = f"Venue id and year could not be extracted from the URL '{tmp_vol}' by the pattern '{HTML.VENUEID_PATTERN.value}"
                raise ValueError(msg)
            
            if __has_year_restrictions(restrictions):
                if not __is_relevant_year(venue_year, restrictions):
                    dropped_due_to_restrictions = True
            if dropped_due_to_restrictions is False and __has_venue_restrictions(restrictions):
                if not __is_relevant_venue(venue_id, restrictions):
                    dropped_due_to_restrictions = True
            
            if dropped_due_to_restrictions is False:
                relevant_volume_urls.append(tmp_vol)
            
            # reset variable
            dropped_due_to_restrictions = False
            
    return relevant_volume_urls # filled with urls, or empty


def prettify_lines(lines):
    """
    Break up html lines with multiple tags into multiple lines using the package etree.
    NOTE that the representation of the attribute values will be normalised, thus all values are quoted!
    
    E.g. ... <main aria-role=main><h2 id=title>List of all volumes</h2><hr><ul><li><a href=/anthology/volumes/S12-1/>*SEM 2012: The First Joint Conference on Lexical and Computational Semantics – Volume 1: Proceedings of the main conference and the shared task, and Volume 2: Proceedings of the Sixth International Workshop on Semantic Evaluation (SemEval 2012)</a></li><li> ...
    
    break into:
      <main aria-role="main">
        <h2 id="title">List of all volumes</h2>
        <hr/>
        <ul>
          <li>
            <a href="/anthology/volumes/S12-1/">*SEM 2012: The First Joint Conference on Lexical and Computational Semantics – Volume 1: Proceedings of the main conference and the shared task, and Volume 2: Proceedings of the Sixth International Workshop on Semantic Evaluation (SemEval 2012)</a>
          </li>
          <li>
    
    respective return list:
    [..., '      <main aria-role="main">', '        <h2 id="title">List of all volumes</h2>', '        <hr/>', '        <ul>', '          <li>', '            <a href="/anthology/volumes/S12-1/">*SEM 2012: The First Joint Conference on Lexical and Computational Semantics – Volume 1: Proceedings of the main conference and the shared task, and Volume 2: Proceedings of the Sixth International Workshop on Semantic Evaluation (SemEval 2012)</a>', '          </li>', '          <li>', ... ]

    :param lines: lines of a html file
    :return: lines of the html file with one tag per line
    """
    
    document_root = html.fromstring(FORMAT.NL.value.join(lines))
    pretty_document = etree.tostring(document_root, encoding='unicode', pretty_print=True)
    pretty_lines_notyetgood = pretty_document.split(FORMAT.NL.value)
    
    # data = "\n".join(lines)
    #
    # soup = bs(data,features="lxml")                #make BeautifulSoup
    # prettyHTML=soup.prettify()   #prettify the html
    #
    # print(prettyHTML)
    
    pretty_lines = []
    closed_tag = False
    idx_begin = 0
    idx_end = 0
    line = "".join(pretty_lines_notyetgood)
    #for line in lines:
    for idx, ch in enumerate(line):
        if (line[idx] == "<" and line[idx+1] != "/"):
            part = line[idx_begin:idx]
            if part.strip():
                pretty_lines.append(part)
                #print(f">>> part: {part}")
            idx_begin = idx
            idx_end = idx_begin
        elif idx > 0 and line[idx-1] == ">":
            next_not_space = None
            for nch in line[idx:]:
                if nch.strip():
                    next_not_space = nch
                    break
                    
            if next_not_space == "<":
                part = line[idx_begin:idx]
                if part.strip():
                    pretty_lines.append(part)
                    #print(f">>> part: {part}")
                idx_begin = idx
                idx_end = idx_begin
                
        
        idx_end = idx
        
    if idx_begin < len(line):
        part = line[idx_begin:]
        if part.strip():
            pretty_lines.append(part)
            #print(f">>> part: {part}")
    
    return pretty_lines


__HAS_YEAR_RESTRICTIONS = None
def __has_year_restrictions(restriction_dict=None):
    
    global __HAS_YEAR_RESTRICTIONS
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

__HAS_VENUE_RESTRICTIONS = None
def __has_venue_restrictions(restriction_dict=None):
    
    global __HAS_VENUE_RESTRICTIONS
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
    """input e.g. A00-1"""
    
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
    url_stem=HTML.VOLUME_URL_STEM_CLOSED.value,
    restrictions=None):
    """Extracts the urls for the ACL volumes from the ACL Anthology volume website.
    
    The overview pages are downloaded in a temporary file which will be deleted as soon as not used any more.
    
    Example for the relevant html lines in one of the overview pages:
        <a href="/anthology/volumes/S12-1/">*SEM 2012: The First Joint Conference on Lexical and Computational Semantics – Volume 1: Proceedings of the main conference and the shared task, and Volume 2: Proceedings of the Sixth International Workshop on Semantic Evaluation (SemEval 2012)</a>'
    From this line, the following url will be extracted:
        https://www.aclweb.org/anthology/volumes/S12-1/index.html
    
    On this url, the whole volume is listed, and the bib file for the volume.
    """
    
    local_fn = output_temp_fn # if filled: only a temporary file; if None: the file will be kept permanently
    
    if local_fn is None:
        os.makedirs(output_path, exist_ok=True)
        output_path = __normalize_path_end(output_path)
    
    
    if output_temp_fn is None:
        local_fn = output_path + "volumes" + HTML.EXTENSION_HTML.value
        
    download_url = url_stem + HTML.INDEXHTML.value
    local_fn_ov_retrieved, headers = urllib.request.urlretrieve(download_url, filename=local_fn)
    logger.log(logging.INFO, f"Downloaded url: '{download_url}' into '{local_fn_ov_retrieved}'.")
    
    volume_urls = extract_volume_urls(local_fn_ov_retrieved, restrictions=restrictions)
    logger.log(logging.INFO, f"-> Found {len(volume_urls)} relevant volume URLs.")
    
    
    if output_temp_fn is not None:
        os.remove(local_fn)
        logger.log(logging.INFO, f"(Local file {local_fn} removed.)")
    
    return volume_urls

    
def __normalize_path_end(path):
    return path if path.endswith(FORMAT.SLASH.value) else path + FORMAT.SLASH.value


def download_volume_bib(volume_url, bib_extension=".bib", output_folder="./"):
    os.makedirs(output_folder, exist_ok=True)
    
    volume_url = volume_url[:-1] if volume_url.endswith(FORMAT.SLASH.value) else volume_url
    
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


def reformat_bib(bib_filename, overwrite=False):
    """
    Simple reformatting of the bib entries in the input file.
    The function overwrites the file with the reformatted content.
    
    Currently, the following changes are made:
    - quoted values will be replaced with curly bracketed ones
    - title values will be additionally enclosed in double curly brackets
    TODO:
    - Generate keys like Author_year_Title_Id
    
    :param bibfile: file with bib entries
    :return: None
    """
    
    with open(bib_filename) as f:
        lines = f.readlines()
        
    if overwrite is False:
        path, name = FORMAT.SLASH.value.join(bib_filename.split(FORMAT.SLASH.value)[:-1]), bib_filename.split(FORMAT.SLASH.value)[-1]
        orig_bib_filename = path + FORMAT.SLASH.value + FORMAT.UNDERSCORE.value + name
        copied_filename = shutil_copy(bib_filename, orig_bib_filename)
        
    reformatted_lines = []
    prev_attribute = None
    for line in lines:
        line = line.rstrip()
        #print("LINE: " + line)
        
        matched = False
        
        #matching a line with the whole attribute-value pair
        match = BIB.ATTRIBUTEVALUE_PATTERN.value.match(line)
        if match is not None:
            attribute = match.group(BIB.ATTRIBUTE_GROUP.value)
            value = match.group(BIB.VALUE_GROUP.value)
            value_with_quotes = match.group(BIB.VALUE_WITH_QUOTES.value)
            #print(f"\tattribute:   '{attribute}'")
            #print(f"\tvalue:       '{value}'")
            #print(f"\tvalue wq:    '{value_with_quotes}'")
            value_with_braces = BIB.BRACE_OPENING.value + value + BIB.BRACE_CLOSING.value
            if attribute == BIB.TITLE.value:
                value_with_braces = BIB.BRACE_OPENING.value + value_with_braces + BIB.BRACE_CLOSING.value
            reformatted_line = line.replace(value_with_quotes, value_with_braces)
            reformatted_lines.append(reformatted_line)
            #print(f"\treform (all): '{reformatted_line}'")
            matched = True
        
        if matched is False:
            
            # is it a line starting with an attribute-value pattern?
            match = BIB.ATTRIBUTEVALUE_BEGIN_PATTERN.value.match(line)
            if match is not None:
                attribute = match.group(BIB.ATTRIBUTE_GROUP.value)
                prev_attribute = attribute
                value = match.group(BIB.VALUE_GROUP.value)
                value_with_quotes = match.group(BIB.VALUE_WITH_QUOTES.value)
                #print(f"\tattribute:   '{attribute}'")
                #print(f"\tvalue:       '{value}'")
                #print(f"\tvalue wq:    '{value_with_quotes}'")
                value_with_braces = BIB.BRACE_OPENING.value + value
                if attribute == BIB.TITLE.value:
                    value_with_braces = BIB.BRACE_OPENING.value + value_with_braces
                reformatted_line = line.replace(value_with_quotes, value_with_braces)
                reformatted_lines.append(reformatted_line)
                #print(f"\treform (beg): '{reformatted_line}'")
                matched = True
            
            
        if matched is False:
            # is it a line ending with a value pattern?
            match = BIB.ATTRIBUTEVALUE_END_PATTERN.value.match(line)
            if match is not None:
                value = match.group(BIB.VALUE_GROUP.value)
                value_with_quotes = match.group(BIB.VALUE_WITH_QUOTES.value)
                #print(f"\tattribute:   '{prev_attribute}'")
                #print(f"\tvalue:       '{value}'")
                #print(f"\tvalue wq:    '{value_with_quotes}'")
                value_with_braces = value + BIB.BRACE_CLOSING.value
                if attribute == BIB.TITLE.value:
                    value_with_braces = value_with_braces + BIB.BRACE_CLOSING.value
                reformatted_line = line.replace(value_with_quotes, value_with_braces)
                reformatted_lines.append(reformatted_line)
                #print(f"\treform (end): '{reformatted_line}'")
                matched = True
                prev_attribute = None
                
        if matched is False:
            # all other lines
            reformatted_lines.append(line)
            #print(f"\toriginal:    '{line}'")
    
    with open(bib_filename, "w") as f:
        for line in reformatted_lines:
            f.write(line + FORMAT.NL.value)
     

def main_download_acl_bibs(output_path, delete_overviews, reformat_bibs, concatenated_filename=None, restrictions=None, input_url_stem=HTML.VOLUME_URL_STEM_CLOSED.value):
    """Main function."""
    
    logger.log(logging.INFO,  f"Extract names of volume urls from {input_url_stem}.")
    
    os.makedirs(output_path, exist_ok=True)
    
    temp_ovfn = output_path + LOCAL.TMP_FILENAME.value if delete_overviews is True else None
    
    if not restrictions:
        logger.log(logging.INFO, f"No restrictions")
    else:
        logger.log(logging.INFO, f"Restriction dict: {restrictions}")
    
    
    list_of_volume_urls = extract_volume_overviews(
        output_path = output_path + LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEW.value,
        output_temp_fn = temp_ovfn, #if None: all the files will be  kept after download
        url_stem = input_url_stem,
        restrictions = restrictions
    )
    
    urllen = len(list_of_volume_urls)
    logger.log(logging.INFO, f"\n=> Extracted {urllen} volume urls.")
    
    logger.log(logging.INFO, f"\nDownload the bib file for volumes.")
    problematic_bibs = []
    downloaded_bibs = []
    for idx, volume_url in enumerate(list_of_volume_urls):
        logger.log(logging.INFO, f"- export volume bib for {volume_url} ({idx+1}/{urllen})")
        
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
    
    if reformat_bibs is True:
        for bibfile in downloaded_bibs:
            print("bib: " + bibfile)
            
            reformat_bib(bibfile, overwrite=False)
    
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
        description=f'downloads bib files for the journals/proceedings of ACL anthology from {URL.ROOT.value}.',
        epilog=f'Minimal use: python3.6 aclanthology_bibfiles_downloader.py -o <output_path>\n--> Extract all bib files into <output_path>/bibs/.')
        
    if print_help:
        parser.print_help()
    else:
    
        parser.add_argument(
            '-o', dest="output_path", type=str, required=True,
            help='required argument: path for the downloaded bib files -- it will be reused if already existing; The individual bib-files will be saved in a subfolder of the given output_path called bibs/.')
        parser.add_argument(
            '-d', dest="delete_overview_files", type=str, default="False",
            help='whether to keep the intermediate overview file (if False (default): keep it in a subfolder called "' + LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEW.value + '", else they will be deleted as soon as possible)')
        parser.add_argument(
            '-l', dest="log_file", type=str, default="download.log",
            help='name for the log-file; default: download.log; The file will be saved in the current output_path, thus, give only the pure file name for the log-file.')
        
        parser.add_argument('-c', dest="concatenated_file", type=str, default=None,
            help='name for an (optional) output file concatenating all the downloaded bib-files into a common one; the file will be saved into the output_path')
        
        parser.add_argument('-y', dest="year", type=int, default=None,
            help="optional argument for downloading bibfiles for one particular year; format: yyyy")
        parser.add_argument('-Y', dest="years", default=None,
            help="optional argument for downloading bibfiles for a range of years; format: yyyy-yyyy")
        
        parser.add_argument('-a', dest="venue_acronym", type=str, default=None,
            help="optional argument for downloading bibfiles for one particular venue; use the acronym, e.g. acl or ACL (case-insensitive)")
        parser.add_argument('-A', dest="venue_acronyms", default=None,
            help="optional argument for downloading bibfiles for more than one venues, format: list the acronyms separated by space within apostrophs, e.g. 'acl cl tacl'")
        
        parser.add_argument('-i', dest="venue_idletter", type=str, default=None,
            help="optional argument for downloading bibfiles for one particular venue; use the letter identifying the venue, e.g. P for ACL")
        parser.add_argument('-I', dest="venue_idletters", default=None,
            help="optional argument for downloading bibfiles for more than one venues, format: list the letters separated by space within apostrophs, e.g. 'P J Q'")
        
        parser.add_argument('-f', dest="reformat_bibs", type=str, default="False",
            help="optional argument for additional formatting of the bib-entries. If False (default), no reformatting is done. Otherwise, the quoted values will be replaced with curly braces, the title with doubled curly braces. See code for more details.")
        
    return parser

logger = logging.getLogger("biblogger")

if __name__ == "__main__":
    
    assert sys.version_info >= (3, 6), "Use Python 3.6 or later"
    
    #LOG
    #logger = logging.getLogger("biblogger")
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
    
    delete_overview_files = args.delete_overview_files
    delete_overview_files = False if delete_overview_files == "False" else True
    
    concatenated_filename = args.concatenated_file
    reformat_bibs = args.reformat_bibs
    reformat_bibs = False if reformat_bibs == "False" else True
    
    logfile = args.log_file
    logpath = output_path
    os.makedirs(os.path.realpath(logpath), exist_ok=True)
    logger.addHandler(logging.FileHandler(logpath+logfile, "w"))
    
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
    
    msg_reformat = "Reformatting bib entries." if reformat_bibs is True else "Keeping bib entries as downloaded."
    msg_concat = f"Output bib-files will be concatenated and saved in '{output_path}{concatenated_filename}' additionally to the files in subfolder '{LOCAL.OUTPUT_SUBFOLDER_BIBS.value}'." if concatenated_filename else f"Output bib-files are saved in subfolder '{LOCAL.OUTPUT_SUBFOLDER_BIBS.value}'."
    msg_keepov = f"Temporary files will be removed at the end of the downloading process." if delete_overview_files else f"The overview files will be saved in subfolder '{LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEW.value}'"
    msg = f"{msg_output}\n- {msg_restriction_years}\n- {msg_restriction_venues}\n- {msg_reformat}\n- {msg_concat}\n- {msg_keepov}\n\n"
    
    logger.log(logging.INFO, msg)
    
    #RUN DOWNLOAD PROCESS
    main_download_acl_bibs(output_path, delete_overviews=delete_overview_files, reformat_bibs=reformat_bibs, concatenated_filename=concatenated_filename, restrictions=restrictions_dict)
    
    logger.log(logging.INFO, "(DONE)")


    