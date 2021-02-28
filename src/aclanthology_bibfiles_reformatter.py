"""
Bibfile reformatter for already downloaded bib-files.
"""

import sys

from aclanthology_bibfiles_downloader import reformat_bib


def main_reformat_local_bib(input_bib, output_bib):
    """
    Reformat an already downloaded bib file.
    """
    
    reformat_bib(input_bib, output_bib, reformat_entry_key_emm=True)
    

# def run_reformat_local_bib():
#
#
#         # ("../outputs/outputs_1960-1969/bibs/C65-1.bib", "../outputs/outputs_1960-1969/bibs/C65-1_reformatted.bib")
#     local_bibs = [
#         ("../outputs/outputs_1960-1969/all_1960-1969.bib", "../outputs/outputs_1960-1969/all_1960-1969_reformatted.bib") ,
#         ("../outputs/outputs_1970-1979/all_1970-1979.bib", "../outputs/outputs_1970-1979/all_1970-1979_reformatted.bib"),
#         ("../outputs/outputs_1980-1989/all_1980-1989.bib", "../outputs/outputs_1980-1989/all_1980-1989_reformatted.bib"),
#         ("../outputs/outputs_1990-1999/all_1990-1999.bib", "../outputs/outputs_1990-1999/all_1990-1999_reformatted.bib"),
#         ("../outputs/outputs_2000-2009/all_2000-2009.bib", "../outputs/outputs_2000-2009/all_2000-2009_reformatted.bib"),
#         ("../outputs/outputs_2010-2019/all_2010-2019.bib", "../outputs/outputs_2010-2019/all_2010-2019_reformatted.bib")
#     ]
#
#     for bib_in, bib_out in local_bibs:
#         print(f"reformatting bib: '{bib_in}' to '{bib_out}'")
#         main_reformat_local_bib(bib_in, bib_out)
#
#     #concatenate reformatted files to
#     output_path = "../outputs/"
#     concatenated_bibfile = "all_1960-2019_reformatted.bib"
#     print(f"Concatenate all reformatted bibs to '{output_path+concatenated_bibfile}'")
#     list_of_input_bibfilenames = [item[1] for item in local_bibs]
#     __concatenate_bib_files(list_of_input_bibfilenames, output_path, concatenated_bibfile)
    

if __name__ == "__main__":
    
    assert sys.version_info >= (3, 6), "Use Python 3.6 or later"
    
    args = sys.argv
    if len(args) < 3:
        sys.exit(f"python {args[0]} <input_bib> <output_reformatted_bib>")
    else:
        main_reformat_local_bib(args[1], args[2])
