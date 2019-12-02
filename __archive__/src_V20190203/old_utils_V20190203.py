#!/usr/bin/env python3.6 or newer

"""
Utils for the acl-bib-downloader.

Author: emm (mujdricza@cl.uni-heidelberg.de)
Version: 20190203

Licence: This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/.
"""

from enum import Enum
import re
import os


class FORMAT(Enum):
    """Some format constants."""
    SLASH = "/"
    SPACE = " "
    HYPHEN = "-"


class URL(Enum):
    ROOT = "https://aclanthology.info/"  # !
    VOLUMES = "https://aclanthology.info/volumes/"  # e.g. https://aclanthology.info/volumes/proceedings-of-the-56th-annual-meeting-of-the-association-for-computational-linguistics-volume-1-long-papers
    PAPERS = "https://aclanthology.info/papers/"  # e.g. https://aclanthology.info/papers/P18-1000/p18-1000
    VENUES = "https://aclanthology.info/venues/"  # e.g. "https://aclanthology.info/venues/acl"
    EVENTS = "https://aclanthology.info/events/"  # e.g. https://aclanthology.info/events/acl-2018


class HTML(Enum):
    """Constants for the target html pages (ACL Anthology)."""
    VOLUME_URL_STEM = "https://aclanthology.info/volumes"
    VOLUME_URL_STEM_CLOSED = VOLUME_URL_STEM + FORMAT.SLASH.value
    
    TBODY_OPENING = "<tbody>"  # NOTE assumption: there is one and only one table with tbody
    TBODY_CLOSING = "</tbody>"
    HREF_VOLUMES_PATTERN = re.compile('<a href="/volumes/(?P<volume>[^"]+)"')
    HREF_VOLUME_GROUP = "volume"
    TR_OPENING = "<tr>"
    TR_CLOSING = "</tr>"
    TD_OPENING = "<td>"
    TD_PATTERN = re.compile('<td>(?P<info>[^<]+?)</td>')
    TD_INFO_GROUP = "info"
    
    VENUEID_PATTERN = re.compile("(?P<id>[A-Z])(?P<year>[0-9][0-9])-[0-9]+") #e.g. A00-1, P18-1, W17-40
    VENUEID_ID_GROUP = "id"
    VENUEID_SHORTYEAR_GROUP = "year"
    
    
    EXTENSION_HTML = ".html"
    EXTENSION_BIB = ".bib"
    A_HREF_STRING = "<a href="
    PAGINATION_STRING = "?page="
    LAST_PAGE = 32  # amount of pages available (to date), but this constraint is not necessarily used
    

class LOCAL(Enum):
    """Customizable constants for the downloaded data."""
    OUTPUT_PATH = "../outputs/data_acl/"
    OUTPUT_SUBFOLDER_VOLUMEOVERVIEWS = "volume-overviews" + FORMAT.SLASH.value
    OUTPUT_CONCATENATED_FILENAME = "all.bib"
    TMP_FILENAME = "tmp.html"
    OUTPUT_SUBFOLDER_BIBS = "bibs" + FORMAT.SLASH.value
    PAGE = "page"
    KEEP_FILES_CMDL_OPTION = "keep"


class RESTRICTIONS(Enum):
    YEARS = "years"
    VENUES = "venues" #via the url_id letter !!! e.g. ACL = "P"
    ALL = "all"




#Venue acronyms to their venue url id, e.g. acl --> P

#TODO FIXME: The letter "W" is assigned to many conferences (workshops)! There are also conferences (workshops) without any papers --> "None" as letter
ACRONYM2LETTER_DICT = {
        'cl' :  'J', # https://aclanthology.info/venues/cl      Computational Linguistics Journal
        'tacl' :        'Q', # https://aclanthology.info/venues/tacl    Transactions of the Association for Computational Linguistics
        'acl' : 'P', # https://aclanthology.info/venues/acl     ACL Annual Meeting
        'eacl' :        'E', # https://aclanthology.info/venues/eacl    European Chapter of ACL
        'naacl' :       'N', # https://aclanthology.info/venues/naacl   North American Chapter of ACL
        'semeval' :     'S', # https://aclanthology.info/venues/semeval Lexical and Computational Semantics and Semantic Evaluation (formerly Workshop on Sense Evaluation)
        'anlp' :        'A', # https://aclanthology.info/venues/anlp    Applied Natural Language Processing Conference
        'emnlp' :       'D', # https://aclanthology.info/venues/emnlp   Conference on Empirical Methods in Natural Language Processing (and forerunners)
        'coling' :      'C', # https://aclanthology.info/venues/coling  Int&#39;l Committee on Computational Linguistics (ICCL) Conf.
        'hlt' : 'N', # https://aclanthology.info/venues/hlt     Human Language Technology Conf.
        'ijcnlp' :      'I', # https://aclanthology.info/venues/ijcnlp  Int&#39;l Joint Conf. on Natural Language Processing (and workshops)
        'lrec' :        'L', # https://aclanthology.info/venues/lrec    International Conference on Language Resources and Evaluation
        'paclic' :      'Y', # https://aclanthology.info/venues/paclic  Pacific Asia Conference on Language, Information and Computation
        'rocling-ijclclp' :     'O', # https://aclanthology.info/venues/rocling-ijclclp Rocling Computation Linguistics Conference and Journal
        'tinlap' :      'T', # https://aclanthology.info/venues/tinlap  Theoretical Issues In Natural Language Processing
        'alta' :        'U', # https://aclanthology.info/venues/alta    Australasian Language Technology Association Workshop
        'ranlp' :       'R', # https://aclanthology.info/venues/ranlp   International Conference Recent Advances in Natural Language Processing
        'jep-taln-recital' :    'F', # https://aclanthology.info/venues/jep-taln-recital        JEP/TALN/RECITAL
        'muc' : 'M', # https://aclanthology.info/venues/muc     Message Understanding Conf.
        'tipster' :     'X', # https://aclanthology.info/venues/tipster NIST&#39;s TIPSTER Text Program
        
        'law' : 'W', # https://aclanthology.info/venues/law     Linguistic Annotation Workshop
        'bionlp' :      'W', # https://aclanthology.info/venues/bionlp  Biomedical Natural Language Processing Workshop
        'vlc' : 'W', # https://aclanthology.info/venues/vlc     Workshop on Very Large Corpora
        'sigdial' :     'W', # https://aclanthology.info/venues/sigdial SIGDial Conference
        'fsmnlp' :      'W', # https://aclanthology.info/venues/fsmnlp  International Conference on Finite State Methods for Natural Language Processing
        'atanlp' :      'W', # https://aclanthology.info/venues/atanlp  Workshop on Applications of Tree Automata Techniques in Natural Language Processing
        'inlg' :        'W', # https://aclanthology.info/venues/inlg    International Natural Language Generation Conference
        'enlg' :        'W', # https://aclanthology.info/venues/enlg    European Workshop on Natural Language Generation
        'sighan' :      'W', # https://aclanthology.info/venues/sighan  SIGHAN Workshop on Chinese Language Processing
        'latech' :      'W', # https://aclanthology.info/venues/latech  Workshop on Language Technology for Cultural Heritage, Social Sciences, and Humanities
        'mol' : 'W', # https://aclanthology.info/venues/mol     Meeting on the Mathematics of Language
        'wmt' : 'W', # https://aclanthology.info/venues/wmt     Workshop on Statistical Machine Translation
        'ssst' :        'W', # https://aclanthology.info/venues/ssst    Workshop on Syntax, Semantics and Structure in Statistical Translation
        'conll' :       'K', # https://aclanthology.info/venues/conll   Conference on Computational Natural Language Learning
        'alnlp' :       'W', # https://aclanthology.info/venues/alnlp   Workshop on Active Learning for Natural Language Processing
        'wassa' :       'W', # https://aclanthology.info/venues/wassa   Workshop on Computational Approaches to Subjectivity and Sentiment Analysis
        'iwpt' :        'W', # https://aclanthology.info/venues/iwpt    International Conference on Parsing Technologies
        'spmrl' :       'W', # https://aclanthology.info/venues/spmrl   Workshop on Statistical Parsing of Morphologically Rich Languages
        'sigmorphon' :  'W', # https://aclanthology.info/venues/sigmorphon      Meeting of the ACL Special Interest Group on Computational Morphology and Phonology
        'sem' : 'None', # https://aclanthology.info/venues/sem  Joint Conference on Lexical and Computational Semantics
        'cosli' :       'None', # https://aclanthology.info/venues/cosli        Workshop on Computational Models of Spatial Language Interpretation and Generation
        'wamm' :        'W', # https://aclanthology.info/venues/wamm    Workshop on Annotation of Modal Meanings in Natural Language
        'gems' :        'W', # https://aclanthology.info/venues/gems    GEometrical Models of Natural Language Semantics
        'iwcs' :        'W', # https://aclanthology.info/venues/iwcs    International Conference on Computational Semantics
        'gl' :  'None', # https://aclanthology.info/venues/gl   International Conference on the Generative Lexicon
        'textinfer' :   'W', # https://aclanthology.info/venues/textinfer       Workshop on Textual Entailment
        'nesp-nlp' :    'W', # https://aclanthology.info/venues/nesp-nlp        Negation and Speculation in Natural Language Processing
        'prep' :        'W', # https://aclanthology.info/venues/prep    Workshop on Prepositions
        'icos' :        'W', # https://aclanthology.info/venues/icos    International Workshop on Inference in Computational Semantics
        'step' :        'W', # https://aclanthology.info/venues/step    Semantics in Text Processing
        'sew' : 'W', # https://aclanthology.info/venues/sew     Workshop on Semantic Evaluations
        'ws' :  'W', # https://aclanthology.info/venues/ws      Other Workshops and Events
        'semitic' :     'W', # https://aclanthology.info/venues/semitic Workshop on Computational Approaches to Semitic Languages
        'pitr' :        'W', # https://aclanthology.info/venues/pitr    Workshop on Predicting and Improving Text Readability for Target Reader Populations
        'slpat' :       'W', # https://aclanthology.info/venues/slpat   Workshop on Speech and Language Processing for Assistive Technologies
        'wac' : 'W', # https://aclanthology.info/venues/wac     Workshop on Web as Corpus
        'cvir' :        'W', # https://aclanthology.info/venues/cvir    Content Visualization and Intermedia Representations
        'gwc' : 'W', # https://aclanthology.info/venues/gwc     Global WordNet Conference
        'cogacll' :     'W', # https://aclanthology.info/venues/cogacll Workshop on Cognitive Aspects of Computational Language Learning
        'catocl' :      'W', # https://aclanthology.info/venues/catocl  Workshop on Computational Approaches to Causality in Language
        'mwe' : 'W', # https://aclanthology.info/venues/mwe     Workshop on Multiword Expressions
        'clfl' :        'W', # https://aclanthology.info/venues/clfl    Workshop on Computational Linguistics for Literature
        'hytra' :       'W', # https://aclanthology.info/venues/hytra   Workshop on Hybrid Approaches to Machine Translation
        'louhi' :       'W', # https://aclanthology.info/venues/louhi   International Workshop on Health Text Mining and Information Analysis
        'lasm' :        'W', # https://aclanthology.info/venues/lasm    Workshop on Language Analysis for Social Media
        'events' :      'W', # https://aclanthology.info/venues/events  Workshop on EVENTS
        'ttnls' :       'W', # https://aclanthology.info/venues/ttnls   Workshop on Type Theory and Natural Language Semantics
        'cvsc' :        'W', # https://aclanthology.info/venues/cvsc    Workshop on Continuous Vector Space Models and their Compositionality
        'lg-lp' :       'W', # https://aclanthology.info/venues/lg-lp   Workshop on Lexical and Grammatical Resources for Language Processing
        'wanlp' :       'W', # https://aclanthology.info/venues/wanlp   Workshop on Arabic Natural Language Processing
        'codeswitch' :  'W', # https://aclanthology.info/venues/codeswitch      Workshop on Computational Approaches to Code Switching
        'moocs' :       'W', # https://aclanthology.info/venues/moocs   Workshop on Modeling Large Scale Social Interaction In Massively Open Online Courses
        'lt4var' :      'W', # https://aclanthology.info/venues/lt4var  Workshop on Language Technology for Closely Related Languages and Language Variants
        'cogalex' :     'W', # https://aclanthology.info/venues/cogalex Workshop on Cognitive Aspects of the Lexicon
        'wssanlp' :     'W', # https://aclanthology.info/venues/wssanlp Workshop on South and Southeast Asian NLP
        'ats-ma' :      'W', # https://aclanthology.info/venues/ats-ma  Workshop on Automatic Text Simplification - Methods and Applications in the Multilingual Society
        'comacoma' :    'W', # https://aclanthology.info/venues/comacoma        Workshop on Computational Approaches to Compound Analysis
        'swaie' :       'W', # https://aclanthology.info/venues/swaie   Workshop on Semantic Web and Information Extraction
        'sadaatl' :     'W', # https://aclanthology.info/venues/sadaatl Workshop on Synchronic and Diachronic Approaches to Analyzing Technical Language
        'computerm' :   'W', # https://aclanthology.info/venues/computerm       Workshop on Computational Terminology
        'oiaf4hlt' :    'W', # https://aclanthology.info/venues/oiaf4hlt        Workshop on Open Infrastructures and Analysis Frameworks for HLT
        'vardial' :     'W', # https://aclanthology.info/venues/vardial Workshop on Applying NLP Tools to Similar Languages, Varieties and Dialects
        'vl' :  'W', # https://aclanthology.info/venues/vl      Workshop on Vision and Language
        'cltw' :        'W', # https://aclanthology.info/venues/cltw    Celtic Language Technology Workshop
        'aha' : 'W', # https://aclanthology.info/venues/aha     AHA!-Workshop on Information Discovery in Text
        'nlp4call' :    'W', # https://aclanthology.info/venues/nlp4call        Workshop on NLP for Computer-Assisted Language Learning
        'wat' : 'W', # https://aclanthology.info/venues/wat     Workshop on Asian Translation
        'csct' :        'W', # https://aclanthology.info/venues/csct    Workshop on Computational Semantics in Clinical Text
        'cosli-b11fbd90-cbc7-4fec-bd4c-b2fba36724e0' :  'W', # https://aclanthology.info/venues/cosli-b11fbd90-cbc7-4fec-bd4c-b2fba36724e0      Computational Models of Spatial Language Interpretation and Generation
        'nlp4ita' :     'W', # https://aclanthology.info/venues/nlp4ita Workshop on Natural Language Processing for Improving Textual Accessibility
        'depling' :     'W', # https://aclanthology.info/venues/depling International Conference on Dependency Linguistics
        'alr' : 'W', # https://aclanthology.info/venues/alr     Workshop on Asian Language Resources
        'bucc' :        'W', # https://aclanthology.info/venues/bucc    Workshop on Building and Using Comparable Corpora
        'cmcl' :        'W', # https://aclanthology.info/venues/cmcl    Workshop on Cognitive Modeling and Computational Linguistics
        'socialnlp' :   'W', # https://aclanthology.info/venues/socialnlp       Workshop on Natural Language Processing for Social Media
        'bea' : 'W', # https://aclanthology.info/venues/bea     Workshop on Innovative Use of NLP for Building Educational Applications
        'textgraphs' :  'W', # https://aclanthology.info/venues/textgraphs      Graph-based Methods for Natural Language Processing
        'teachingnlp' : 'W', # https://aclanthology.info/venues/teachingnlp     Workshop on Teaching Natural Language Processing
        'clp' : 'W', # https://aclanthology.info/venues/clp     Chinese Language Processing
        'nodalida' :    'W', # https://aclanthology.info/venues/nodalida        Nordic Conference of Computational Linguistics
        'wnut' :        'W', # https://aclanthology.info/venues/wnut    Workshop on Noisy User-generated Text
        'news' :        'W', # https://aclanthology.info/venues/news    Named Entities Workshop
        's2mt' :        'W', # https://aclanthology.info/venues/s2mt    Workshop on Semantics-Driven Statistical Machine Translation
        'geaf' :        'W', # https://aclanthology.info/venues/geaf    Grammar Engineering Across Frameworks Workshop
        'ldl' : 'W', # https://aclanthology.info/venues/ldl     Workshop on Linked Data in Linguistics
        'nlp-tea' :     'W', # https://aclanthology.info/venues/nlp-tea Workshop on Natural Language Processing Techniques for Educational Applications
        'cnewsstory' :  'W', # https://aclanthology.info/venues/cnewsstory      Workshop on Computing News Storylines
        'exprom' :      'W', # https://aclanthology.info/venues/exprom  Workshop on Extra-Propositional Aspects of Meaning in Computational Semantics
        'metaphor' :    'W', # https://aclanthology.info/venues/metaphor        Workshop on Metaphor in NLP
        'latentvar' :   'W', # https://aclanthology.info/venues/latentvar       Workshop on Vector Space Modeling for Natural Language Processing
        'clpsych' :     'W', # https://aclanthology.info/venues/clpsych Workshop on Computational Linguistics and Clinical Psychology
        'discomt' :     'W', # https://aclanthology.info/venues/discomt Workshop on Discourse in Machine Translation
        'lsdsem' :      'W', # https://aclanthology.info/venues/lsdsem  Workshop on Linking Computational Models of Lexical, Sentential and Discourse-level Semantics
        'eamt' :        'W', # https://aclanthology.info/venues/eamt    Conference of the European Association for Machine Translation
        'bsnlp' :       'W', # https://aclanthology.info/venues/bsnlp   Workshop on Balto-Slavic Natural Language Processing
        'nlp4tm' :      'W', # https://aclanthology.info/venues/nlp4tm  Workshop on Natural Language Processing for Translation Memories
        'nlplod' :      'W', # https://aclanthology.info/venues/nlplod  Workshop on Natural Language Processing and Linked Open Data
        'stil' :        'W', # https://aclanthology.info/venues/stil    Brazilian Symposium in Information and Human Language Technology
        'dmtw' :        'None', # https://aclanthology.info/venues/dmtw Deep Machine Translation Workshop
        'sedmt' :       'W', # https://aclanthology.info/venues/sedmt   Workshop on Semantics-Driven Machine Translation
        'corbon' :      'W', # https://aclanthology.info/venues/corbon  Workshop on Coreference Resolution Beyond OntoNotes
        'akbc' :        'W', # https://aclanthology.info/venues/akbc    Workshop on Automated Knowledge Base Construction
        'birndl' :      'None', # https://aclanthology.info/venues/birndl       Joint Workshop on Bibliometric-enhanced Information Retrieval and Natural Language Processing for Digital Libraries
        'tag' : 'W', # https://aclanthology.info/venues/tag     International Workshop on Tree Adjoining Grammars and Related Formalisms
        'argmining' :   'W', # https://aclanthology.info/venues/argmining       Workshop on Argument Mining
        'repeval' :     'W', # https://aclanthology.info/venues/repeval Workshop on Evaluating Vector-Space Representations for NLP
        'rep4nlp' :     'W', # https://aclanthology.info/venues/rep4nlp Workshop on Representation Learning for NLP
        'bioasq' :      'W', # https://aclanthology.info/venues/bioasq  BioASQ Workshop
        'statfsm' :     'W', # https://aclanthology.info/venues/statfsm Workshop on Statistical NLP and Weighted Automata
        'webnlg' :      'W', # https://aclanthology.info/venues/webnlg  International Workshop on Natural Language Generation and the Semantic Web
        'nlp-css' :     'W', # https://aclanthology.info/venues/nlp-css Workshop on NLP and Computational Social Science
        'cns' : 'W', # https://aclanthology.info/venues/cns     Workshop on Computing News Storylines
        'ccnlg' :       'W', # https://aclanthology.info/venues/ccnlg   Workshop on Computational Creativity in Natural Language Generation
        'gramlex' :     'W', # https://aclanthology.info/venues/gramlex Workshop on Grammar and Lexicon
        'lt4dh' :       'W', # https://aclanthology.info/venues/lt4dh   Workshop on Language Technology Resources and Tools for Digital Humanities
        'cl4lc' :       'W', # https://aclanthology.info/venues/cl4lc   Workshop on Computational Linguistics for Linguistic Complexity
        'clinicalnlp' : 'W', # https://aclanthology.info/venues/clinicalnlp     Clinical Natural Language Processing Workshop
        'icon' :        'W', # https://aclanthology.info/venues/icon    International Conference on Natural Language Processing
        'multiling' :   'W', # https://aclanthology.info/venues/multiling       Workshop on Multilingual Summarization
        'ethnlp' :      'W', # https://aclanthology.info/venues/ethnlp  Workshop on Ethics in NLP
        'sembear' :     'W', # https://aclanthology.info/venues/sembear Workshop on Computational Semantics Beyond Events and Roles
        'sense' :       'W', # https://aclanthology.info/venues/sense   Workshop on Sense, Concept and Entity Representations and their Applications
        'udw' : 'W', # https://aclanthology.info/venues/udw     Universal Dependencies Workshop
        'alw' : 'W', # https://aclanthology.info/venues/alw     Workshop on Abusive Language Online
        'robonlp' :     'W', # https://aclanthology.info/venues/robonlp Workshop on Language Grounding for Robotics
        'winlp' :       'None', # https://aclanthology.info/venues/winlp        Women and Underrepresented Minorities in Natural Language Processing
        'nmt' : 'W', # https://aclanthology.info/venues/nmt     Workshop on Neural Machine Translation
        'scil' :        'W', # https://aclanthology.info/venues/scil    Society for Computation in Linguistics
        'crac' :        'W', # https://aclanthology.info/venues/crac    Workshop on Computational models of Reference
        'ethics-nlp' :  'W', # https://aclanthology.info/venues/ethics-nlp      Workshop on Ethics in Natural Language Processing
        'fig-lang' :    'W', # https://aclanthology.info/venues/fig-lang        Workshop on Figurative Language Processing
        'gen-deep' :    'W', # https://aclanthology.info/venues/gen-deep        Workshop on Generalization in the Age of Deep Learning
        'peoples' :     'W', # https://aclanthology.info/venues/peoples Workshop on Computational Modeling of People&#39;s Opinions, Personality, and Emotions in Social Media
        'sclem' :       'W', # https://aclanthology.info/venues/sclem   Workshop on Subword and Character LEvel Models in NLP
        'splu' :        'W', # https://aclanthology.info/venues/splu    Spatial Language Understanding
        'story-nlp' :   'W', # https://aclanthology.info/venues/story-nlp       Workshop on Storytelling
        'style-var' :   'W', # https://aclanthology.info/venues/style-var       Workshop on Stylistic Variation
        'amta' :        'W', # https://aclanthology.info/venues/amta    Conference of the Association for Machine Translation in the Americas
        'lr4nlp' :      'W', # https://aclanthology.info/venues/lr4nlp  Workshop on Linguistic Resources for NLP
        'semdeep' :     'W', # https://aclanthology.info/venues/semdeep Workshop on Semantic Deep Learning
        'lccm' :        'W', # https://aclanthology.info/venues/lccm    Workshop on Language, Cognition and Computational Models
        'nlp4if' :      'W', # https://aclanthology.info/venues/nlp4if  Workshop on NLP for Internet Freedom
        'eventstory' :  'W', # https://aclanthology.info/venues/eventstory      Workshop on Events and Stories in the News
        'trac' :        'W', # https://aclanthology.info/venues/trac    Workshop on Trolling, Aggression and Cyberbullying
        'isa' : 'W', # https://aclanthology.info/venues/isa     ISO Workshop on Interoperable Semantic Annotation
        'pylo' :        'W', # https://aclanthology.info/venues/pylo    Workshop on Computational Modeling of Polysynthetic Languages
}


LETTER2ACRONYM_DICT = {
    "A" : "anlp",
    "C" : "coling",
    "D" : "emnlp",
    "E" : "eacl",
    "F" : "jep-taln-recital",
    "I" : "ijcnlp",
    "J" : "cl",
    "L" : "lrec",
    "M" : "muc",
    "N" : "naacl_hlt", #NOTE grouped together NAACL and HLT
    "O" : "rocling-ijclclp",
    "P" : "acl",
    "Q" : "tacl",
    "R" : "ranlp",
    "S" : "semeval",
    "T" : "tinlap",
    "U" : "alta",
    "W" : "SIGs", #NOTE many conferences/workshops are included in this group
    "X" : "tipster",
    "Y" : "paclic"
}



def __extract_venue_acronym2idletter_dict(url_venues):

    """
    
    1) venues: Extract the acronym (first column) and full name (second column) as well as the further url for the current venue (second column)
    ...
    <tbody>
      ...
      <tr>
        <td>ACL</td>
        <td><a href="/venues/acl">ACL Annual Meeting</a></td>
        <td>ACL</td>
        <!-- <td>
          <a class="btn btn-mini" href="/venues/acl/edit">Edit</a>
          <a class="btn btn-mini btn-danger" data-confirm="Are you sure?" data-method="delete" href="/venues/acl" rel="nofollow">Delete</a>
        </td> -->
      </tr>
    ...
    
    2) venues/<ACRONYM>: Extract the "id" for the venue, e.g. for acl = P (first column)
    ...
    <tbody>
            <tr>
              <td>P18-1</td>
              <td><a href="/volumes/proceedings-of-the-56th-annual-meeting-of-the-association-for-computational-linguistics-volume-1-long-papers">Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)</a></td>
              <td>257</td>
            </tr>
    ...
    
    :param url_venues: URL to the Anthology overview according to Venues
    :return: dictionary with the acronym of the venues as key and the url-id as well as the full name as value (list)
    """
    local_fn = "tmp_venues.html"
    local_fn_ov_retrieved, headers = urllib.request.urlretrieve(url_venues, filename=local_fn)
    
    file = open(local_fn_ov_retrieved)  # one page of the volume overviews
    lines = file.readlines()
    file.close()
    
    venue_dict = {}
    
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
    
    #<td><a href="/venues/cl">Computational Linguistics Journal</a></td>
    tdahref_string = "<td><a href="
    pattern_venue = re.compile('<td><a href="/venues/(?P<acronym>[^"]+)">(?P<fullname>[^<]+)</a></td>')
    for line in tbodylines:
        if tdahref_string in line:
            match = pattern_venue.search(line)
            if match is not None:
                # value of the href attribute -- part of an url
                acronym = match.group("acronym")
                fullname = match.group("fullname")
                # extend it to the whole target url with the volume
                url_venue = url_venues + acronym
            
                venue_dict[acronym] = [url_venue, fullname]
    
    #print(venue_dict)
    
    for acronym, value_list in venue_dict.items():
        url_venue = value_list[0]
        local_fn_retrieved, headers = urllib.request.urlretrieve(url_venue, filename=local_fn)
        
        with open(local_fn_retrieved) as f:
            lines = f.readlines()
        
        """
        <tbody>
            <tr>
              <td>P18-1</td>
        """
        id = None
        for i, line in enumerate(lines):
            
            if line.strip() == "<tbody>":
                #print(lines[i:i+5])
                target_line = lines[i+2].strip()
                match = HTML.VENUEID_PATTERN.value.search(target_line)
                
                if match is not None:
                    id = match.group(HTML.VENUEID_ID_GROUP.value)
    
                    if id is None:
                        msg = f"Not recognized venue information in raw volume string:\n{target_line}"
                        raise ValueError(msg)
                    break
                else:
                    #not the correct one
                    pass
            
        
        venue_dict[acronym].append(id)
    
    os.remove(local_fn)
    
    return venue_dict


def main_extract_acronym2letter_dict():
    """Extracts the venue dictionary for further use."""
    
    import urllib.request
    
    venue_dict = __extract_venue_acronym2idletter_dict(URL.VENUES.value)

    # print(venue_dict)
    
    s = """ACRONYM2LETTER_DICT = {\n"""
    
    for acronym, value_list in venue_dict.items():
        s += f"\t'{acronym}' :\t'{value_list[2]}', # {value_list[0]}\t{value_list[1]}\n"
    s += "}"
    
    print(s)

def main_run_experiments_for_all_letters():
    """Extracts all papers for each 'letter'  -- FIXME --> the bash script is ok, use that """
    
    import subprocess
    import sys
    
    path_to_py = os.path.realpath(".")
    #sys.path.append(path_to_py)
    
    for letter, pseudo_acronym in LETTER2ACRONYM_DICT.items():
        print(f"PROCESS {letter} = {pseudo_acronym}")
        cmd_str = f"python3 aclanthology_bibfiles_downloader.py -o ../outputs/bibs/bibs_{letter}_{pseudo_acronym}/ -l ../outputs/bibs_{letter}_{pseudo_acronym}/download.log -f False -i {letter} -c all_{letter}_{pseudo_acronym}.bib"

        process = subprocess.Popen(cmd_str.split(), cwd=path_to_py, capture_output=True, shell=True, check=True)# , stdout=subprocess.PIPE)
        result, error = process.communicate()  # hier: None, None
    

if __name__ == "__main__":
    main_extract_acronym2letter_dict()
    #main_run_experiments_for_all_letters()
    