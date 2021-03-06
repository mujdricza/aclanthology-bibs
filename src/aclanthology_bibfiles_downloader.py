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
Last Version: 20210406 (previous versions: 20210228, 20191209, 20191201, 20190203, 20180921, 20180524, ...)

Licence: This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/.

TODO:
- update some of the DocStrings with new examples

NOTE:
- The conferences with url-identifying letter "W" are not differenciable! -- concerning all SIGs! (See utils.py / LETTER2ACRONYM_DICT and ACRONYM2LETTER_DICT)

"""

import argparse
import os
import sys
import urllib.request
import logging
from lxml import etree, html
import shutil
from typing import List

    
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
    restrictions=None  # if None --> download all volume urls, else it is a dictionary with restrictive information like relevant year or years, relevant journal or journals
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
    
    file = open(local_fn_volumeoverview_html)  # one page of the volume overviews
    lines = file.readlines()
    file.close()
    
    # NOTE that the files are squeezed into a few lines --> break them up into multiple lines
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
    
    # first, extract all possible volume URLs
    for line in mainlines:
        if href_string in line:
            match = pattern_volume.search(line)
            if match is not None:
                # value of the href attribute -- part of an url
                vol = match.group(href_group)
                
                # extend it to the whole target url with the volume
                vol = target_url_stem + vol
                
                volume_urls.append(vol)
            else:
                if "volumes" in line:
                    msg = f"Not extracted volume URL from '{href_string}' in line '{line}' by pattern '{pattern_volume}'."
                    raise ValueError(msg)
    
    # no restrictions --> simple extraction of all volumes
    relevant_volume_urls = []
    if restrictions is None or not restrictions:
        logger.log(logging.DEBUG, f"No restriction -- take all volumes.")
        relevant_volume_urls = volume_urls
    
    else:
        logger.log(logging.INFO, f"Restrict download to specific year and/or venue: {restrictions}")
    
        dropped_due_to_restrictions = False
        
        for tmp_vol in volume_urls:
            venue_id, venue_year = __extract_current_venue_and_year(tmp_vol)
            
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
    
    pretty_lines = []
    idx_begin = 0
    idx_end = 0
    line = "".join(pretty_lines_notyetgood)
    for idx, ch in enumerate(line):
        if (line[idx] == "<" and line[idx+1] != "/"):
            part = line[idx_begin:idx]
            if part.strip():
                pretty_lines.append(part)
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
                idx_begin = idx
                idx_end = idx_begin
        idx_end = idx
        
    if idx_begin < len(line):
        part = line[idx_begin:]
        if part.strip():
            pretty_lines.append(part)
    
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
    
    match = HTML.VENUEID_PATTERN1.value.search(raw_volume_string)
    if match is not None:
        id = match.group(HTML.VENUEID_ID_GROUP.value)
        year = __extract_year_from_shortyear(match.group(HTML.VENUEID_SHORTYEAR_GROUP.value))
    else:
        match = HTML.VENUEID_PATTERN2.value.search(raw_volume_string)
        if match is not None:
            id = match.group(HTML.VENUEID_ID_GROUP.value)
            year = __extract_year(match.group(HTML.VENUEID_YEAR_GROUP.value))
        else:
            id = None
            year = None
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


def __extract_year(year_str):
    return int(year_str)


def extract_volume_overviews(
    output_path,
    keep_output_fn,
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
    
    os.makedirs(output_path, exist_ok=True)
    output_path = __normalize_path_end(output_path)
    local_fn = output_path + "volumes" + HTML.EXTENSION_HTML.value
    
    download_url = url_stem + HTML.INDEXHTML.value
    local_fn_ov_retrieved, headers = urllib.request.urlretrieve(download_url, filename=local_fn)
    logger.log(logging.INFO, f"Downloaded url: '{download_url}' into '{local_fn_ov_retrieved}'.")
    
    volume_urls = extract_volume_urls(local_fn_ov_retrieved, restrictions=restrictions)
    logger.log(logging.INFO, f"-> Found {len(volume_urls)} relevant volume URLs.")
    
    if not keep_output_fn:
        output_dir = os.path.dirname(local_fn)
        shutil.rmtree(output_dir)
        logger.log(logging.INFO, f"(Local file(s) in {output_dir} removed.)")
    
    return volume_urls

    
def __normalize_path_end(path):
    return path if path.endswith(FORMAT.SLASH.value) else path + FORMAT.SLASH.value


def download_volume_bib(volume_url, bib_extension=".bib", output_folder="./"):
    os.makedirs(output_folder, exist_ok=True)
    
    volume_url = volume_url[:-1] if volume_url.endswith(FORMAT.SLASH.value) else volume_url
    
    bib_url = volume_url + bib_extension
    bib_fn = bib_url.split("/")[-1]  # get the last splitpart=filename
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


def reformat_bib(bib_filename, output_bib_filename, reformat_entry_key_emm=True):
    """
    Simple reformatting of the bib entries in the input file.
    The function overwrites the file with the reformatted content.
    
    Currently, the following changes are made:
    - quoted values will be replaced with curly bracketed ones
    - title values will be additionally enclosed in double curly brackets
    If reformat_entry_key_emm is set to True:
    - Reformat keys like Author_year_Title_Id
      Original --> Target
      nurminen-2019-decision --> Nurminen_2019_Decision_W19-7204
      pezzelle-fernandez-2019-big --> PezzelleFernandez_2019_Big_D19-6403
      ono-etal-2019-hybrid --> OnoEtal_2019_Hybrid_W19-7201
      emnlp-2019-beyond --> EMNLP_2019_beyond_D19-6400 (@proceedings)
    
    :param bibfile: file with bib entries
    :return: None
    """
    
    with open(bib_filename) as f:
        lines = f.readlines()
        
    # list of list for list of entry-lines
    entries_for_reformat = __get_entries(lines)
    
    reformatted_lines = []  # flat list of lines
    
    for entry_lines in entries_for_reformat:
        reformatted_entry_lines = __reformat_entry(entry_lines, reformat_entry_key_emm=reformat_entry_key_emm)
        
        reformatted_lines.extend(reformatted_entry_lines)
        reformatted_lines.append("")  # separator line between two entries
    
    with open(output_bib_filename, "w") as f:
        for line in reformatted_lines:
            f.write(line + FORMAT.NL.value)


def __get_entries(lines_of_bib_file):
    entries = []
    
    current_entry = []
    for line in lines_of_bib_file:
        line = line.rstrip()
        
        if not line:  # empty line
            continue
        
        # take all the entries, also comment entries
        if line.startswith("@"):
            if len(current_entry) > 0:
                entries.append(current_entry)
                current_entry = []
            
        current_entry.append(line)
    
    #last entry
    if len(current_entry) > 0:
        entries.append(current_entry)
    return entries


def __reformat_entry(lines_of_entry, reformat_entry_key_emm):
    
    reformatted_lines = []
    
    prev_attribute = None
    
    for line in lines_of_entry:  # lines are rstripped already
        matched = False
        
        # handle month information explicitely: take it as it is
        if line.strip().startswith("month"):
            reformatted_lines.append(line)
            matched = True
        
        #matching a line with the whole attribute-value pair
        match = BIB.ATTRIBUTEVALUE_PATTERN.value.match(line)
        if match is not None:
            attribute = match.group(BIB.ATTRIBUTE_GROUP.value)
            value = match.group(BIB.VALUE_GROUP.value)
            value_with_quotes = match.group(BIB.VALUE_WITH_QUOTES.value)
            value_with_braces = BIB.BRACE_OPENING.value + value + BIB.BRACE_CLOSING.value
            if attribute == BIB.TITLE.value:
                value_with_braces = BIB.BRACE_OPENING.value + value_with_braces + BIB.BRACE_CLOSING.value
            reformatted_line = line.replace(value_with_quotes, value_with_braces)
            reformatted_lines.append(reformatted_line)
            matched = True
            
        if matched is False:
            
            # is it a line starting with an attribute-value pattern?
            match = BIB.ATTRIBUTEVALUE_BEGIN_PATTERN.value.match(line)
            if match is not None:
                attribute = match.group(BIB.ATTRIBUTE_GROUP.value)
                prev_attribute = attribute
                value = match.group(BIB.VALUE_GROUP.value)
                value_with_quotes = match.group(BIB.VALUE_WITH_QUOTES.value)
                value_with_braces = BIB.BRACE_OPENING.value + value
                if attribute == BIB.TITLE.value:
                    value_with_braces = BIB.BRACE_OPENING.value + value_with_braces
                reformatted_line = line.replace(value_with_quotes, value_with_braces)
                reformatted_lines.append(reformatted_line)
                matched = True
                
        if matched is False:
            # is it a line ending with a value pattern?
            match = BIB.ATTRIBUTEVALUE_END_PATTERN.value.match(line)
            if match is not None:
                value = match.group(BIB.VALUE_GROUP.value)
                value_with_quotes = match.group(BIB.VALUE_WITH_QUOTES.value)
                value_with_braces = value + BIB.BRACE_CLOSING.value
                if attribute == BIB.TITLE.value:
                    value_with_braces = value_with_braces + BIB.BRACE_CLOSING.value
                reformatted_line = line.replace(value_with_quotes, value_with_braces)
                reformatted_lines.append(reformatted_line)
                matched = True
                prev_attribute = None
        
        if matched is False:
            # insert an empty line between two entries
            match = BIB.ENTRY_BEGIN_PATTERN.value.match(line)
            if match is not None:
                reformatted_line = line
                if reformat_entry_key_emm is True:
                    # My personal preference
                    match = BIB.ENTRY_KEY_PATTERN.value.match(line)
                    if match is not None:
                        type = match.group(BIB.TYPE_GROUP.value)
                        key = match.group(BIB.KEY_GROUP.value)
                        
                        key_parts = key.split("-")
                        if len(key_parts) < 3:
                            msg = f"KEY parts should contain at least 3 elements. It contains {len(key_parts)}: {key_parts}"
                            raise ValueError(msg)
                        key_parts = [part.title() for part in key_parts]
                        if type == "proceedings":
                            key_parts[0] = key_parts[0].upper()
                            
                        if len(key_parts) > 3:
                            names = "".join(key_parts[:-2])
                            year = key_parts[-2]
                            title = key_parts[-1]
                            
                            key_parts = [names, year, title]
                        
                        reformatted_key = "_".join(key_parts)
                        reformatted_line = "@" + type + "{" + reformatted_key + ","
                        
                    else:  # not expected...
                        raise ValueError
                
                reformatted_lines.append(reformatted_line)
                matched = True
               
        if matched is False:
            # all other lines
            reformatted_lines.append(line)
    
    if reformat_entry_key_emm is True:
        # append the id to the key
        current_url = __extract_url_from_reformatted_entry(reformatted_lines)
        
        if current_url is not None:
            # e.g. https://www.aclweb.org/anthology/J19-1001
            id = current_url.split("/")[-1]
            
            # assumption: the first item is the entry line
            key = reformatted_lines[0]
            reformatted_lines[0] = key[:-1] + "_" + id + ","
    
    return reformatted_lines
    
    
def __extract_url_from_reformatted_entry(reformatted_lines):
    
    current_url = None
    
    for line in reformatted_lines:
        line = line.strip()
        if line.startswith("url = "):
            current_url = line.split("{")[1].split("}")[0]
    
    return current_url


def main_download_acl_bibs(output_path,
                           keep_overviews,
                           reformat_bibs,
                           concatenated_filename=None,
                           restrictions=None,
                           input_url_stem=HTML.VOLUME_URL_STEM_CLOSED.value):
    """Main function."""
    
    logger.log(logging.INFO,  f"Extract names of volume urls from {input_url_stem}.")
    os.makedirs(output_path, exist_ok=True)
    
    if not restrictions:
        logger.log(logging.INFO, f"No restrictions")
    else:
        logger.log(logging.INFO, f"Restriction dict: {restrictions}")
    
    
    list_of_volume_urls = extract_volume_overviews(
        output_path = output_path + LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEW.value,
        keep_output_fn = keep_overviews,
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
    
    all_bibfiles = []
    if reformat_bibs is True:
        for bibfile in downloaded_bibs:
            
            path, name = FORMAT.SLASH.value.join(bibfile.split(FORMAT.SLASH.value)[:-1]), bibfile.split(FORMAT.SLASH.value)[-1]
            reformatted_bibfile = path + FORMAT.SLASH.value + name.replace(".bib", "_reformatted.bib")
            all_bibfiles.append(reformatted_bibfile)
            reformat_bib(bibfile, reformatted_bibfile)
    else:
        all_bibfiles = downloaded_bibs
    
    if concatenated_filename is not None:
        __concatenate_bib_files(all_bibfiles, output_path, concatenated_filename)
        

def __concatenate_bib_files(list_of_input_bibfilenames, output_path, output_bibfilename):
    
    allbib = output_path + output_bibfilename
    logger.log(logging.INFO, f"\nConcatenate {len(list_of_input_bibfilenames)} bib-files into '{allbib}'.")
    with open(allbib, "w") as fout:
        for local_bib_fn in list_of_input_bibfilenames:
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
        epilog=f'Minimal use: python3 aclanthology_bibfiles_downloader.py -o <output_path>'
               f' --> Extracts all bib files into <output_path>/bibs/.')
        
    if print_help:
        parser.print_help()
    else:
    
        parser.add_argument(
            '-o', dest="output_path", type=str, required=True,
            help='required argument: path for the downloaded bib files -- it will be reused if already existing; The individual bib-files will be saved in a subfolder of the given output_path called bibs/.')
        parser.add_argument('-f', dest="reformat_bibs", action="store_true",
            help="optional argument for additional formatting of the bib-entries. If set, reformatting is done: the quoted values will be replaced with curly braces, the title with doubled curly braces. See code for more details.")
        parser.add_argument(
            '-k', dest="keep_overview_files", action="store_true",
            help='optional argument; if set, the intermediate overview files will be kept in a subfolder called "' + LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEW.value + '"; otherwise they will be deleted as soon as possible.')
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
        
    return parser

logger = logging.getLogger("biblogger")


def run_download_acl_bibs(args_raw:List):
    #LOG
    #logger = logging.getLogger("biblogger")
    #logger.setLevel(logging.DEBUG)
    
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    
    argparser = load_argument_parser()
    args = argparser.parse_args(args_raw)
    
    output_path = args.output_path  # new files
    output_path = __normalize_path_end(output_path)
    
    keep_overview_files = args.keep_overview_files
    
    concatenated_filename = args.concatenated_file
    reformat_bibs = args.reformat_bibs
    
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
    
    msg_reformat = "Reformatting bib entries." if reformat_bibs else "Keeping bib entries as downloaded."
    msg_concat = f"Output bib-files will be concatenated and saved in '{output_path}{concatenated_filename}' additionally to the files in subfolder '{LOCAL.OUTPUT_SUBFOLDER_BIBS.value}'." if concatenated_filename else f"Output bib-files are saved in subfolder '{LOCAL.OUTPUT_SUBFOLDER_BIBS.value}'."
    msg_keepov = f"The overview files will be saved in subfolder '{LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEW.value}'" if keep_overview_files else "Temporary files will be removed at the end of the downloading process."
    msg = f"{msg_output}\n- {msg_restriction_years}\n- {msg_restriction_venues}\n- {msg_reformat}\n- {msg_concat}\n- {msg_keepov}\n\n"
    
    logger.log(logging.INFO, msg)
    
    #RUN DOWNLOAD PROCESS
    main_download_acl_bibs(output_path,
                           keep_overviews=keep_overview_files,
                           reformat_bibs=reformat_bibs,
                           concatenated_filename=concatenated_filename,
                           restrictions=restrictions_dict)
    
    logger.log(logging.INFO, "(DONE)")


if __name__ == "__main__":
    
    assert sys.version_info >= (3, 6), "Use Python 3.6 or later"
    
    args_raw = sys.argv
    
    if len(args_raw) < 2:
        load_argument_parser(print_help=True)
        sys.exit(1)
        
    run_download_acl_bibs(args_raw[1:])
    
