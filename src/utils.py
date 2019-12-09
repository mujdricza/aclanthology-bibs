#!/usr/bin/env python3.6 or newer

"""
Utils for the acl-bib-downloader.

Author: emm (mujdricza@cl.uni-heidelberg.de)
Version: 20190209

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
    NL = "\n"
    UNDERSCORE = "_"

class URL(Enum):
    ROOT = "https://www.aclweb.org/anthology/"  # !
    VOLUMES = ROOT + "volumes/"  # e.g. https://www.aclweb.org/anthology/volumes/P18-1/
    #PAPERS = ROOT + "papers/"  # NO SUBFOLDER "PAPERS" ANY MORE, but e.g. https://www.aclweb.org/anthology/P18-1000/
    VENUES = ROOT + "venues/"  # e.g. https://www.aclweb.org/anthology/venues/acl/
    EVENTS = ROOT + "events/"  # e.g. https://www.aclweb.org/anthology/events/acl-2018/
    
class HTML(Enum):
    """Constants for the target html pages (ACL Anthology)."""
    VOLUME_URL_STEM = "https://www.aclweb.org/anthology/volumes"
    VOLUME_URL_STEM_CLOSED = VOLUME_URL_STEM + FORMAT.SLASH.value
    
    MAIN_OPENING_BEGIN = "<main "  # NOTE assumption: there is one and only one tag with the name main in the volumes document. This area contains the list of the volume URLs: <main aria-role=main> ... </main>
    MAIN_CLOSING = "</main>"
    HREF_VOLUMES_PATTERN = re.compile('<a href="/anthology/volumes/(?P<volume>[^"]+)"') # see return value in the function aclanthology_bibfiles_downloader.__prettify_lines()
    HREF_VOLUME_GROUP = "volume"
    
    VENUEID_PATTERN = re.compile("(?P<id>[A-Z])(?P<year>[0-9][0-9])-[0-9]+") #e.g. A00-1, P18-1, W17-40
    VENUEID_ID_GROUP = "id"
    VENUEID_SHORTYEAR_GROUP = "year"
    
    INDEXHTML = "index.html"
    EXTENSION_HTML = ".html"
    EXTENSION_BIB = ".bib"
    A_HREF_STRING = "<a href="
    
    HREF_VENUES_PATTERN = re.compile('<a href="/anthology/venues/(?P<venue>[^"]+)/">(?P<shortname>[^<]+)</a>') # see return value in the function aclanthology_bibfiles_downloader.prettify_lines()
    HREF_VENUE_GROUP = "venue"
    HREF_SHORTNAME_GROUP = "shortname"
    
    
    H2_TITLE_OPENING_BEGIN = '<h2 id="title">'
    H2_CLOSING = "</h2>"
    
    
class LOCAL(Enum):
    """Customizable constants for the downloaded data."""
    OUTPUT_PATH = "../outputs/data_acl/"
    OUTPUT_SUBFOLDER_VOLUMEOVERVIEW = "volume-overview" + FORMAT.SLASH.value
    OUTPUT_CONCATENATED_FILENAME = "all.bib"
    TMP_FILENAME = "tmp.html"
    OUTPUT_SUBFOLDER_BIBS = "bibs" + FORMAT.SLASH.value
    KEEP_FILES_CMDL_OPTION = "keep"


class RESTRICTIONS(Enum):
    YEARS = "years"
    VENUES = "venues" #via the url_id letter !!! e.g. ACL = "P"
    ALL = "all"

class BIB(Enum):
    TITLE = "title"
    QUOTATION_MARK = '"'
    BRACE_OPENING = "{"
    BRACE_CLOSING = "}"
    EQUALS = " = "
    
    ATTRIBUTEVALUE_PATTERN = re.compile("^\s*(?P<attribute>[^\s]+)\s*=\s*(?P<value_with_quotes>\"(?P<value>.*)\"),?$")
    ATTRIBUTEVALUE_BEGIN_PATTERN = re.compile("^\s*(?P<attribute>[^\s]+)\s*=\s*(?P<value_with_quotes>\"(?P<value>.*[^,]))$")
    ATTRIBUTEVALUE_END_PATTERN = re.compile("^\s*(?P<value_with_quotes>(?P<value>.*)\"),?$")
    ENTRY_BEGIN_PATTERN = re.compile("^\s*@[^\s]+\s*{.+,$")
    ENTRY_KEY_PATTERN = re.compile("^@(?P<type>[^\s{]+){(?P<key>[^,]+),$")
    ATTRIBUTE_GROUP = "attribute"
    VALUE_GROUP = "value"
    VALUE_WITH_QUOTES = "value_with_quotes"
    TYPE_GROUP = "type"
    KEY_GROUP = "key"
    


#Venue acronyms to their venue url id, e.g. acl --> P

#TODO FIXME: The letter "W" is assigned to many conferences (workshops)! There are also conferences (workshops) without any papers --> "None" as letter
# from the V20190203
ACRONYM2LETTER_DICT = {
        'cl' :  'J', # https://www.aclweb.org/anthology/venues/cl      Computational Linguistics Journal
        'tacl' :        'Q', # https://www.aclweb.org/anthology/venues/tacl    Transactions of the Association for Computational Linguistics
        'acl' : 'P', # https://www.aclweb.org/anthology/venues/acl     ACL Annual Meeting
        'eacl' :        'E', # https://www.aclweb.org/anthology/venues/eacl    European Chapter of ACL
        'naacl' :       'N', # https://www.aclweb.org/anthology/venues/naacl   North American Chapter of ACL
        'semeval' :     'S', # https://www.aclweb.org/anthology/venues/semeval Lexical and Computational Semantics and Semantic Evaluation (formerly Workshop on Sense Evaluation)
        'anlp' :        'A', # https://www.aclweb.org/anthology/venues/anlp    Applied Natural Language Processing Conference
        'emnlp' :       'D', # https://www.aclweb.org/anthology/venues/emnlp   Conference on Empirical Methods in Natural Language Processing (and forerunners)
        'coling' :      'C', # https://www.aclweb.org/anthology/venues/coling  Int&#39;l Committee on Computational Linguistics (ICCL) Conf.
        'hlt' : 'N', # https://www.aclweb.org/anthology/venues/hlt     Human Language Technology Conf.
        'ijcnlp' :      'I', # https://www.aclweb.org/anthology/venues/ijcnlp  Int&#39;l Joint Conf. on Natural Language Processing (and workshops)
        'lrec' :        'L', # https://www.aclweb.org/anthology/venues/lrec    International Conference on Language Resources and Evaluation
        'paclic' :      'Y', # https://www.aclweb.org/anthology/venues/paclic  Pacific Asia Conference on Language, Information and Computation
        'rocling-ijclclp' :     'O', # https://www.aclweb.org/anthology/venues/rocling-ijclclp Rocling Computation Linguistics Conference and Journal
        'tinlap' :      'T', # https://www.aclweb.org/anthology/venues/tinlap  Theoretical Issues In Natural Language Processing
        'alta' :        'U', # https://www.aclweb.org/anthology/venues/alta    Australasian Language Technology Association Workshop
        'ranlp' :       'R', # https://www.aclweb.org/anthology/venues/ranlp   International Conference Recent Advances in Natural Language Processing
        'jep-taln-recital' :    'F', # https://www.aclweb.org/anthology/venues/jep-taln-recital        JEP/TALN/RECITAL
        'muc' : 'M', # https://www.aclweb.org/anthology/venues/muc     Message Understanding Conf.
        'tipster' :     'X', # https://www.aclweb.org/anthology/venues/tipster NIST&#39;s TIPSTER Text Program
        
        'law' : 'W', # https://www.aclweb.org/anthology/venues/law     Linguistic Annotation Workshop
        'bionlp' :      'W', # https://www.aclweb.org/anthology/venues/bionlp  Biomedical Natural Language Processing Workshop
        'vlc' : 'W', # https://www.aclweb.org/anthology/venues/vlc     Workshop on Very Large Corpora
        'sigdial' :     'W', # https://www.aclweb.org/anthology/venues/sigdial SIGDial Conference
        'fsmnlp' :      'W', # https://www.aclweb.org/anthology/venues/fsmnlp  International Conference on Finite State Methods for Natural Language Processing
        'atanlp' :      'W', # https://www.aclweb.org/anthology/venues/atanlp  Workshop on Applications of Tree Automata Techniques in Natural Language Processing
        'inlg' :        'W', # https://www.aclweb.org/anthology/venues/inlg    International Natural Language Generation Conference
        'enlg' :        'W', # https://www.aclweb.org/anthology/venues/enlg    European Workshop on Natural Language Generation
        'sighan' :      'W', # https://www.aclweb.org/anthology/venues/sighan  SIGHAN Workshop on Chinese Language Processing
        'latech' :      'W', # https://www.aclweb.org/anthology/venues/latech  Workshop on Language Technology for Cultural Heritage, Social Sciences, and Humanities
        'mol' : 'W', # https://www.aclweb.org/anthology/venues/mol     Meeting on the Mathematics of Language
        'wmt' : 'W', # https://www.aclweb.org/anthology/venues/wmt     Workshop on Statistical Machine Translation
        'ssst' :        'W', # https://www.aclweb.org/anthology/venues/ssst    Workshop on Syntax, Semantics and Structure in Statistical Translation
        'conll' :       'K', # https://www.aclweb.org/anthology/venues/conll   Conference on Computational Natural Language Learning
        'alnlp' :       'W', # https://www.aclweb.org/anthology/venues/alnlp   Workshop on Active Learning for Natural Language Processing
        'wassa' :       'W', # https://www.aclweb.org/anthology/venues/wassa   Workshop on Computational Approaches to Subjectivity and Sentiment Analysis
        'iwpt' :        'W', # https://www.aclweb.org/anthology/venues/iwpt    International Conference on Parsing Technologies
        'spmrl' :       'W', # https://www.aclweb.org/anthology/venues/spmrl   Workshop on Statistical Parsing of Morphologically Rich Languages
        'sigmorphon' :  'W', # https://www.aclweb.org/anthology/venues/sigmorphon      Meeting of the ACL Special Interest Group on Computational Morphology and Phonology
        'sem' : 'None', # https://www.aclweb.org/anthology/venues/sem  Joint Conference on Lexical and Computational Semantics
        'cosli' :       'W', # https://www.aclweb.org/anthology/venues/cosli        Workshop on Computational Models of Spatial Language Interpretation and Generation
        'wamm' :        'W', # https://www.aclweb.org/anthology/venues/wamm    Workshop on Annotation of Modal Meanings in Natural Language
        'gems' :        'W', # https://www.aclweb.org/anthology/venues/gems    GEometrical Models of Natural Language Semantics
        'iwcs' :        'W', # https://www.aclweb.org/anthology/venues/iwcs    International Conference on Computational Semantics
        'gl' :  'None', # https://www.aclweb.org/anthology/venues/gl   International Conference on the Generative Lexicon
        'textinfer' :   'W', # https://www.aclweb.org/anthology/venues/textinfer       Workshop on Textual Entailment
        'nesp-nlp' :    'W', # https://www.aclweb.org/anthology/venues/nesp-nlp        Negation and Speculation in Natural Language Processing
        'prep' :        'W', # https://www.aclweb.org/anthology/venues/prep    Workshop on Prepositions
        'icos' :        'W', # https://www.aclweb.org/anthology/venues/icos    International Workshop on Inference in Computational Semantics
        'step' :        'W', # https://www.aclweb.org/anthology/venues/step    Semantics in Text Processing
        'sew' : 'W', # https://www.aclweb.org/anthology/venues/sew     Workshop on Semantic Evaluations
        'ws' :  'W', # https://www.aclweb.org/anthology/venues/ws      Other Workshops and Events
        'semitic' :     'W', # https://www.aclweb.org/anthology/venues/semitic Workshop on Computational Approaches to Semitic Languages
        'pitr' :        'W', # https://www.aclweb.org/anthology/venues/pitr    Workshop on Predicting and Improving Text Readability for Target Reader Populations
        'slpat' :       'W', # https://www.aclweb.org/anthology/venues/slpat   Workshop on Speech and Language Processing for Assistive Technologies
        'wac' : 'W', # https://www.aclweb.org/anthology/venues/wac     Workshop on Web as Corpus
        'cvir' :        'W', # https://www.aclweb.org/anthology/venues/cvir    Content Visualization and Intermedia Representations
        'gwc' : 'W', # https://www.aclweb.org/anthology/venues/gwc     Global WordNet Conference
        'cogacll' :     'W', # https://www.aclweb.org/anthology/venues/cogacll Workshop on Cognitive Aspects of Computational Language Learning
        'catocl' :      'W', # https://www.aclweb.org/anthology/venues/catocl  Workshop on Computational Approaches to Causality in Language
        'mwe' : 'W', # https://www.aclweb.org/anthology/venues/mwe     Workshop on Multiword Expressions
        'clfl' :        'W', # https://www.aclweb.org/anthology/venues/clfl    Workshop on Computational Linguistics for Literature
        'hytra' :       'W', # https://www.aclweb.org/anthology/venues/hytra   Workshop on Hybrid Approaches to Machine Translation
        'louhi' :       'W', # https://www.aclweb.org/anthology/venues/louhi   International Workshop on Health Text Mining and Information Analysis
        'lasm' :        'W', # https://www.aclweb.org/anthology/venues/lasm    Workshop on Language Analysis for Social Media
        'events' :      'W', # https://www.aclweb.org/anthology/venues/events  Workshop on EVENTS
        'ttnls' :       'W', # https://www.aclweb.org/anthology/venues/ttnls   Workshop on Type Theory and Natural Language Semantics
        'cvsc' :        'W', # https://www.aclweb.org/anthology/venues/cvsc    Workshop on Continuous Vector Space Models and their Compositionality
        'lg-lp' :       'W', # https://www.aclweb.org/anthology/venues/lg-lp   Workshop on Lexical and Grammatical Resources for Language Processing
        'wanlp' :       'W', # https://www.aclweb.org/anthology/venues/wanlp   Workshop on Arabic Natural Language Processing
        'codeswitch' :  'W', # https://www.aclweb.org/anthology/venues/codeswitch      Workshop on Computational Approaches to Code Switching
        'moocs' :       'W', # https://www.aclweb.org/anthology/venues/moocs   Workshop on Modeling Large Scale Social Interaction In Massively Open Online Courses
        'lt4var' :      'W', # https://www.aclweb.org/anthology/venues/lt4var  Workshop on Language Technology for Closely Related Languages and Language Variants
        'cogalex' :     'W', # https://www.aclweb.org/anthology/venues/cogalex Workshop on Cognitive Aspects of the Lexicon
        'wssanlp' :     'W', # https://www.aclweb.org/anthology/venues/wssanlp Workshop on South and Southeast Asian NLP
        'ats-ma' :      'W', # https://www.aclweb.org/anthology/venues/ats-ma  Workshop on Automatic Text Simplification - Methods and Applications in the Multilingual Society
        'comacoma' :    'W', # https://www.aclweb.org/anthology/venues/comacoma        Workshop on Computational Approaches to Compound Analysis
        'swaie' :       'W', # https://www.aclweb.org/anthology/venues/swaie   Workshop on Semantic Web and Information Extraction
        'sadaatl' :     'W', # https://www.aclweb.org/anthology/venues/sadaatl Workshop on Synchronic and Diachronic Approaches to Analyzing Technical Language
        'computerm' :   'W', # https://www.aclweb.org/anthology/venues/computerm       Workshop on Computational Terminology
        'oiaf4hlt' :    'W', # https://www.aclweb.org/anthology/venues/oiaf4hlt        Workshop on Open Infrastructures and Analysis Frameworks for HLT
        'vardial' :     'W', # https://www.aclweb.org/anthology/venues/vardial Workshop on Applying NLP Tools to Similar Languages, Varieties and Dialects
        'vl' :  'W', # https://www.aclweb.org/anthology/venues/vl      Workshop on Vision and Language
        'cltw' :        'W', # https://www.aclweb.org/anthology/venues/cltw    Celtic Language Technology Workshop
        'aha' : 'W', # https://www.aclweb.org/anthology/venues/aha     AHA!-Workshop on Information Discovery in Text
        'nlp4call' :    'W', # https://www.aclweb.org/anthology/venues/nlp4call        Workshop on NLP for Computer-Assisted Language Learning
        'wat' : 'W', # https://www.aclweb.org/anthology/venues/wat     Workshop on Asian Translation
        'csct' :        'W', # https://www.aclweb.org/anthology/venues/csct    Workshop on Computational Semantics in Clinical Text
        'cosli-b11fbd90-cbc7-4fec-bd4c-b2fba36724e0' :  'W', # https://www.aclweb.org/anthology/venues/cosli-b11fbd90-cbc7-4fec-bd4c-b2fba36724e0      Computational Models of Spatial Language Interpretation and Generation
        'nlp4ita' :     'W', # https://www.aclweb.org/anthology/venues/nlp4ita Workshop on Natural Language Processing for Improving Textual Accessibility
        'depling' :     'W', # https://www.aclweb.org/anthology/venues/depling International Conference on Dependency Linguistics
        'alr' : 'W', # https://www.aclweb.org/anthology/venues/alr     Workshop on Asian Language Resources
        'bucc' :        'W', # https://www.aclweb.org/anthology/venues/bucc    Workshop on Building and Using Comparable Corpora
        'cmcl' :        'W', # https://www.aclweb.org/anthology/venues/cmcl    Workshop on Cognitive Modeling and Computational Linguistics
        'socialnlp' :   'W', # https://www.aclweb.org/anthology/venues/socialnlp       Workshop on Natural Language Processing for Social Media
        'bea' : 'W', # https://www.aclweb.org/anthology/venues/bea     Workshop on Innovative Use of NLP for Building Educational Applications
        'textgraphs' :  'W', # https://www.aclweb.org/anthology/venues/textgraphs      Graph-based Methods for Natural Language Processing
        'teachingnlp' : 'W', # https://www.aclweb.org/anthology/venues/teachingnlp     Workshop on Teaching Natural Language Processing
        'clp' : 'W', # https://www.aclweb.org/anthology/venues/clp     Chinese Language Processing
        'nodalida' :    'W', # https://www.aclweb.org/anthology/venues/nodalida        Nordic Conference of Computational Linguistics
        'wnut' :        'W', # https://www.aclweb.org/anthology/venues/wnut    Workshop on Noisy User-generated Text
        'news' :        'W', # https://www.aclweb.org/anthology/venues/news    Named Entities Workshop
        's2mt' :        'W', # https://www.aclweb.org/anthology/venues/s2mt    Workshop on Semantics-Driven Statistical Machine Translation
        'geaf' :        'W', # https://www.aclweb.org/anthology/venues/geaf    Grammar Engineering Across Frameworks Workshop
        'ldl' : 'W', # https://www.aclweb.org/anthology/venues/ldl     Workshop on Linked Data in Linguistics
        'nlp-tea' :     'W', # https://www.aclweb.org/anthology/venues/nlp-tea Workshop on Natural Language Processing Techniques for Educational Applications
        'cnewsstory' :  'W', # https://www.aclweb.org/anthology/venues/cnewsstory      Workshop on Computing News Storylines
        'exprom' :      'W', # https://www.aclweb.org/anthology/venues/exprom  Workshop on Extra-Propositional Aspects of Meaning in Computational Semantics
        'metaphor' :    'W', # https://www.aclweb.org/anthology/venues/metaphor        Workshop on Metaphor in NLP
        'latentvar' :   'W', # https://www.aclweb.org/anthology/venues/latentvar       Workshop on Vector Space Modeling for Natural Language Processing
        'clpsych' :     'W', # https://www.aclweb.org/anthology/venues/clpsych Workshop on Computational Linguistics and Clinical Psychology
        'discomt' :     'W', # https://www.aclweb.org/anthology/venues/discomt Workshop on Discourse in Machine Translation
        'lsdsem' :      'W', # https://www.aclweb.org/anthology/venues/lsdsem  Workshop on Linking Computational Models of Lexical, Sentential and Discourse-level Semantics
        'eamt' :        'W', # https://www.aclweb.org/anthology/venues/eamt    Conference of the European Association for Machine Translation
        'bsnlp' :       'W', # https://www.aclweb.org/anthology/venues/bsnlp   Workshop on Balto-Slavic Natural Language Processing
        'nlp4tm' :      'W', # https://www.aclweb.org/anthology/venues/nlp4tm  Workshop on Natural Language Processing for Translation Memories
        'nlplod' :      'W', # https://www.aclweb.org/anthology/venues/nlplod  Workshop on Natural Language Processing and Linked Open Data
        'stil' :        'W', # https://www.aclweb.org/anthology/venues/stil    Brazilian Symposium in Information and Human Language Technology
        'dmtw' :        'W', # https://www.aclweb.org/anthology/venues/dmtw Deep Machine Translation Workshop
        'sedmt' :       'W', # https://www.aclweb.org/anthology/venues/sedmt   Workshop on Semantics-Driven Machine Translation
        'corbon' :      'W', # https://www.aclweb.org/anthology/venues/corbon  Workshop on Coreference Resolution Beyond OntoNotes
        'akbc' :        'W', # https://www.aclweb.org/anthology/venues/akbc    Workshop on Automated Knowledge Base Construction
        'birndl' :      'None', # https://www.aclweb.org/anthology/venues/birndl       Joint Workshop on Bibliometric-enhanced Information Retrieval and Natural Language Processing for Digital Libraries
        'tag' : 'W', # https://www.aclweb.org/anthology/venues/tag     International Workshop on Tree Adjoining Grammars and Related Formalisms
        'argmining' :   'W', # https://www.aclweb.org/anthology/venues/argmining       Workshop on Argument Mining
        'repeval' :     'W', # https://www.aclweb.org/anthology/venues/repeval Workshop on Evaluating Vector-Space Representations for NLP
        'rep4nlp' :     'W', # https://www.aclweb.org/anthology/venues/rep4nlp Workshop on Representation Learning for NLP
        'bioasq' :      'W', # https://www.aclweb.org/anthology/venues/bioasq  BioASQ Workshop
        'statfsm' :     'W', # https://www.aclweb.org/anthology/venues/statfsm Workshop on Statistical NLP and Weighted Automata
        'webnlg' :      'W', # https://www.aclweb.org/anthology/venues/webnlg  International Workshop on Natural Language Generation and the Semantic Web
        'nlp-css' :     'W', # https://www.aclweb.org/anthology/venues/nlp-css Workshop on NLP and Computational Social Science
        'cns' : 'W', # https://www.aclweb.org/anthology/venues/cns     Workshop on Computing News Storylines
        'ccnlg' :       'W', # https://www.aclweb.org/anthology/venues/ccnlg   Workshop on Computational Creativity in Natural Language Generation
        'gramlex' :     'W', # https://www.aclweb.org/anthology/venues/gramlex Workshop on Grammar and Lexicon
        'lt4dh' :       'W', # https://www.aclweb.org/anthology/venues/lt4dh   Workshop on Language Technology Resources and Tools for Digital Humanities
        'cl4lc' :       'W', # https://www.aclweb.org/anthology/venues/cl4lc   Workshop on Computational Linguistics for Linguistic Complexity
        'clinicalnlp' : 'W', # https://www.aclweb.org/anthology/venues/clinicalnlp     Clinical Natural Language Processing Workshop
        'icon' :        'W', # https://www.aclweb.org/anthology/venues/icon    International Conference on Natural Language Processing
        'multiling' :   'W', # https://www.aclweb.org/anthology/venues/multiling       Workshop on Multilingual Summarization
        'ethnlp' :      'W', # https://www.aclweb.org/anthology/venues/ethnlp  Workshop on Ethics in NLP
        'sembear' :     'W', # https://www.aclweb.org/anthology/venues/sembear Workshop on Computational Semantics Beyond Events and Roles
        'sense' :       'W', # https://www.aclweb.org/anthology/venues/sense   Workshop on Sense, Concept and Entity Representations and their Applications
        'udw' : 'W', # https://www.aclweb.org/anthology/venues/udw     Universal Dependencies Workshop
        'alw' : 'W', # https://www.aclweb.org/anthology/venues/alw     Workshop on Abusive Language Online
        'robonlp' :     'W', # https://www.aclweb.org/anthology/venues/robonlp Workshop on Language Grounding for Robotics
        'winlp' :       'None', # https://www.aclweb.org/anthology/venues/winlp        Women and Underrepresented Minorities in Natural Language Processing
        'nmt' : 'W', # https://www.aclweb.org/anthology/venues/nmt     Workshop on Neural Machine Translation
        'scil' :        'W', # https://www.aclweb.org/anthology/venues/scil    Society for Computation in Linguistics
        'crac' :        'W', # https://www.aclweb.org/anthology/venues/crac    Workshop on Computational models of Reference
        'ethics-nlp' :  'W', # https://www.aclweb.org/anthology/venues/ethics-nlp      Workshop on Ethics in Natural Language Processing
        'fig-lang' :    'W', # https://www.aclweb.org/anthology/venues/fig-lang        Workshop on Figurative Language Processing
        'gen-deep' :    'W', # https://www.aclweb.org/anthology/venues/gen-deep        Workshop on Generalization in the Age of Deep Learning
        'peoples' :     'W', # https://www.aclweb.org/anthology/venues/peoples Workshop on Computational Modeling of People&#39;s Opinions, Personality, and Emotions in Social Media
        'sclem' :       'W', # https://www.aclweb.org/anthology/venues/sclem   Workshop on Subword and Character LEvel Models in NLP
        'splu' :        'W', # https://www.aclweb.org/anthology/venues/splu    Spatial Language Understanding
        'story-nlp' :   'W', # https://www.aclweb.org/anthology/venues/story-nlp       Workshop on Storytelling
        'style-var' :   'W', # https://www.aclweb.org/anthology/venues/style-var       Workshop on Stylistic Variation
        'amta' :        'W', # https://www.aclweb.org/anthology/venues/amta    Conference of the Association for Machine Translation in the Americas
        'lr4nlp' :      'W', # https://www.aclweb.org/anthology/venues/lr4nlp  Workshop on Linguistic Resources for NLP
        'semdeep' :     'W', # https://www.aclweb.org/anthology/venues/semdeep Workshop on Semantic Deep Learning
        'lccm' :        'W', # https://www.aclweb.org/anthology/venues/lccm    Workshop on Language, Cognition and Computational Models
        'nlp4if' :      'W', # https://www.aclweb.org/anthology/venues/nlp4if  Workshop on NLP for Internet Freedom
        'eventstory' :  'W', # https://www.aclweb.org/anthology/venues/eventstory      Workshop on Events and Stories in the News
        'trac' :        'W', # https://www.aclweb.org/anthology/venues/trac    Workshop on Trolling, Aggression and Cyberbullying
        'isa' : 'W', # https://www.aclweb.org/anthology/venues/isa     ISO Workshop on Interoperable Semantic Annotation
        'pylo' :        'W', # https://www.aclweb.org/anthology/venues/pylo    Workshop on Computational Modeling of Polysynthetic Languages
}

#for the V20191201, but not usable for the anthology downloader
__ACRONYM2LETTER_DICT = {
	'acl' :	['W43', 'W30', 'W38', 'W39', 'W33', 'W50', 'W47', 'W34', 'W48', 'W41', 'W26', 'W51', 'W25', 'W42', 'W29', 'W44', 'W37', 'W53', 'W31', 'W54', 'P', 'W27', 'W23', 'W24', 'W45', 'W40', 'W28', 'W35', 'W36', 'W49', 'W32', 'W46', 'W52'], # ['ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL', 'ACL']
	'aha' :	'W45', # 'AHA'
	'akbc' :	'W12', # 'AKBC'
	'alnlp' :	'W19', # 'ALNLP'
	'alr' :	['W54', 'W43'], # ['ALR', 'ALR']
	'alta' :	'U', # 'ALTA'
	'alw' :	'W30', # 'ALW'
	'amta' :	['W19', 'W18'], # ['AMTA', 'AMTA']
	'anlp' :	'A', # 'ANLP'
	'argmining' :	['W51', 'W28'], # ['ArgMining', 'ArgMining']
	'atanlp' :	'W08', # 'ATANLP'
	'ats-ma' :	'W56', # 'ATS-MA'
	'bea' :	['W17', 'W05', 'W06', 'W50', 'W18'], # ['BEA', 'BEA', 'BEA', 'BEA', 'BEA']
	'bioasq' :	'W31', # 'BioASQ'
	'bionlp' :	['W30', 'W02', 'W13', 'W38', 'W24', 'W18', 'W23', 'W29', 'W19', 'W20', 'W14', 'W34'], # ['BioNLP', 'BioNLP', 'BioNLP', 'BioNLP', 'BioNLP', 'BioNLP', 'BioNLP', 'BioNLP', 'BioNLP', 'BioNLP', 'BioNLP', 'BioNLP']
	'bsnlp' :	['W14', 'W53'], # ['BSNLP', 'BSNLP']
	'bucc' :	['W34', 'W25'], # ['BUCC', 'BUCC']
	'catocl' :	'W07', # 'CAtoCL'
	'ccnlg' :	['W39', 'W55'], # ['CCNLG', 'CCNLG']
	'cl' :	'J', # 'CL'
	'cl4lc' :	'W41', # 'CL4LC'
	'clfl' :	['W07', 'W09'], # ['CLFL', 'CLFL']
	'clinicalnlp' :	'W42', # 'ClinicalNLP'
	'clp' :	'W68', # 'CLP'
	'clpsych' :	['W06', 'W31', 'W12'], # ['CLPsych', 'CLPsych', 'CLPsych']
	'cltw' :	'W46', # 'CLTW'
	'cmcl' :	['W01', 'W11', 'W07', 'W26', 'W20'], # ['CMCL', 'CMCL', 'CMCL', 'CMCL', 'CMCL']
	'cnewsstory' :	'W45', # 'CNewsStory'
	'cns' :	'W57', # 'CNS'
	'codeswitch' :	'W39', # 'CodeSwitch'
	'cogacll' :	['W05', 'W19', 'W24'], # ['CogACLL', 'CogACLL', 'CogACLL']
	'cogalex' :	['W53', 'W47'], # ['CogALex', 'CogALex']
	'coling' :	['W40', 'W41', 'W49', 'W42', 'W45', 'C', 'W47', 'W39', 'W38', 'W48', 'W44', 'W43'], # ['COLING', 'COLING', 'COLING', 'COLING', 'COLING', 'COLING', 'COLING', 'COLING', 'COLING', 'COLING', 'COLING', 'COLING']
	'comacoma' :	'W57', # 'ComAComA'
	'computerm' :	['W47', 'W48'], # ['CompuTerm', 'CompuTerm']
	'conll' :	['W07', 'W24', 'W29', 'W06', 'D', 'W36', 'W21', 'W17', 'W11', 'W35', 'W12', 'W10', 'W19', 'W45', 'W04', 'W20', 'W16', 'W03', 'K', 'W30'], # ['CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL', 'CoNLL']
	'corbon' :	['W15', 'W07'], # ['CORBON', 'CORBON']
	'cosli' :	'W07', # 'CoSLI'
	'crac' :	'W07', # 'CRAC'
	'csct' :	'W04', # 'CSCT'
	'cvir' :	'W02', # 'CVIR'
	'cvsc' :	['W40', 'W15'], # ['CVSC', 'CVSC']
	'depling' :	['W21', 'W37', 'W65'], # ['DepLing', 'DepLing', 'DepLing']
	'discomt' :	['W48', 'W25'], # ['DiscoMT', 'DiscoMT']
	'dmtw' :	'W57', # 'DMTW'
	'eacl' :	'E', # 'EACL'
	'eamt' :	['W49', 'W34'], # ['EAMT', 'EAMT']
	'emnlp' :	['W06', 'W13', 'W32', 'W05', 'W61', 'W57', 'W53', 'W56', 'W59', 'W03', 'W10', 'W02', 'W54', 'W55', 'W16', 'W62', 'W60', 'W64', 'W51', 'W52', 'W63', 'W58', 'D', 'W15', 'H'], # ['EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP', 'EMNLP']
	'enlg' :	['W08', 'W23', 'W28', 'W16', 'W47', 'W06'], # ['ENLG', 'ENLG', 'ENLG', 'ENLG', 'ENLG', 'ENLG']
	'ethics-nlp' :	'W08', # 'Ethics-NLP'
	'ethnlp' :	'W16', # 'EthNLP'
	'events' :	['W29', 'W08', 'W10'], # ['EVENTS', 'EVENTS', 'EVENTS']
	'exprom' :	['W50', 'W13'], # ['EXprom', 'EXprom']
	'fig-lang' :	'W09', # 'Fig-Lang'
	'fsmnlp' :	['W44', 'W40', 'W18', 'W48', 'W13'], # ['FSMNLP', 'FSMNLP', 'FSMNLP', 'FSMNLP', 'FSMNLP']
	'geaf' :	'W33', # 'GEAF'
	'gems' :	'W25', # 'GEMS'
	'gen-deep' :	'W10', # 'Gen-Deep'
	'gramlex' :	'W38', # 'GramLex'
	'gwc' :	'W01', # 'GWC'
	'hlt' :	['H', 'N'], # ['HLT', 'HLT']
	'hytra' :	['W10', 'W28', 'W45', 'W41'], # ['HyTra', 'HyTra', 'HyTra', 'HyTra']
	'icon' :	['W59', 'W51', 'W63'], # ['ICON', 'ICON', 'ICON']
	'icos' :	'W39', # 'ICoS'
	'ijcnlp' :	'I', # 'IJCNLP'
	'inlg' :	['W66', 'W67', 'W70', 'W50', 'W21', 'W86', 'W69', 'W15', 'W11', 'W03', 'W14', 'W35', 'W05', 'W42', 'W65', 'W44', 'W01', 'W04'], # ['INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG', 'INLG']
	'iwcs' :	['W09', 'W01', 'W06', 'W08', 'W03', 'W04', 'W69', 'W10', 'W02', 'W68', 'W05', 'W12', 'W37'], # ['IWCS', 'IWCS', 'IWCS', 'IWCS', 'IWCS', 'IWCS', 'IWCS', 'IWCS', 'IWCS', 'IWCS', 'IWCS', 'IWCS', 'IWCS']
	'iwpt' :	['W29', 'W22', 'W63', 'W15', 'W38'], # ['IWPT', 'IWPT', 'IWPT', 'IWPT', 'IWPT']
	'jep-taln-recital' :	['W13', 'W64', 'W11', 'W66', 'W12', 'W14', 'W63', 'F', 'W67', 'W65'], # ['JEP/TALN/RECITAL', 'JEP/TALN/RECITAL', 'JEP/TALN/RECITAL', 'JEP/TALN/RECITAL', 'JEP/TALN/RECITAL', 'JEP/TALN/RECITAL', 'JEP/TALN/RECITAL', 'JEP/TALN/RECITAL', 'JEP/TALN/RECITAL', 'JEP/TALN/RECITAL']
	'lasm' :	['W13', 'W11'], # ['LASM', 'LASM']
	'latech' :	['W06', 'W21', 'W22', 'W37', 'W15', 'W10', 'W27', 'W03', 'W09'], # ['LaTeCH', 'LaTeCH', 'LaTeCH', 'LaTeCH', 'LaTeCH', 'LaTeCH', 'LaTeCH', 'LaTeCH', 'LaTeCH']
	'latentvar' :	'W15', # 'LatentVar'
	'law' :	['W08', 'W30', 'W04', 'W15', 'W16', 'W18', 'W23', 'W17', 'W49', 'W36'], # ['LAW', 'LAW', 'LAW', 'LAW', 'LAW', 'LAW', 'LAW', 'LAW', 'LAW', 'LAW']
	'ldl' :	'W42', # 'LDL'
	'lg-lp' :	'W58', # 'LG-LP'
	'louhi' :	['W61', 'W26', 'W11'], # ['Louhi', 'Louhi', 'Louhi']
	'lrec' :	'L', # 'LREC'
	'lsdsem' :	['W09', 'W27'], # ['LSDSem', 'LSDSem']
	'lt4dh' :	'W40', # 'LT4DH'
	'lt4var' :	['W42', 'W54'], # ['LT4VAR', 'LT4VAR']
	'metaphor' :	['W11', 'W14'], # ['Metaphor', 'Metaphor']
	'mol' :	['W30', 'W23'], # ['MoL', 'MoL']
	'moocs' :	'W41', # 'MOOCs'
	'mtsummit' :	['W67', 'W66'], # ['MTSummit', 'MTSummit']
	'muc' :	'M', # 'MUC'
	'multiling' :	'W10', # 'MultiLing'
	'mwe' :	['W18', 'W10', 'W08', 'W17', 'W09'], # ['MWE', 'MWE', 'MWE', 'MWE', 'MWE']
	'naacl' :	['W16', 'N', 'W18', 'W23', 'W25', 'W20', 'W27', 'W19', 'W22', 'W11', 'W21', 'W29', 'W28', 'W30', 'W13', 'W15', 'W14', 'W12', 'W24', 'W17', 'W26'], # ['NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL', 'NAACL']
	'nesp-nlp' :	'W31', # 'NeSp-NLP'
	'news' :	['W27', 'W39'], # ['NEWS', 'NEWS']
	'nlp-css' :	['W56', 'W29'], # ['NLP+CSS', 'NLP+CSS']
	'nlp-tea' :	['W49', 'W44', 'W59'], # ['NLP-TEA', 'NLP-TEA', 'NLP-TEA']
	'nlp4call' :	['W03', 'W35', 'W65', 'W71', 'W19'], # ['NLP4CALL', 'NLP4CALL', 'NLP4CALL', 'NLP4CALL', 'NLP4CALL']
	'nlp4ita' :	'W15', # 'NLP4ITA'
	'nlp4tm' :	'W52', # 'NLP4TM'
	'nlplod' :	'W55', # 'NLPLOD'
	'nmt' :	'W32', # 'NMT'
	'nodalida' :	['W63', 'W62', 'W65', 'W17', 'W05', 'W46', 'W61', 'W24', 'W10', 'W01', 'W02', 'W56', 'W64', 'W04', 'W16', 'W03', 'W18'], # ['NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa', 'NoDaLiDa']
	'oiaf4hlt' :	'W52', # 'OIAF4HLT'
	'paclic' :	'Y', # 'PACLIC'
	'pitr' :	['W22', 'W12', 'W29'], # ['PITR', 'PITR', 'PITR']
	'prep' :	['W16', 'W21'], # ['PREP', 'PREP']
	'ranlp' :	['W78', 'W81', 'W79', 'W80', 'R', 'W77'], # ['RANLP', 'RANLP', 'RANLP', 'RANLP', 'RANLP', 'RANLP']
	'rep4nlp' :	['W26', 'W16'], # ['Rep4NLP', 'Rep4NLP']
	'repeval' :	['W25', 'W53'], # ['RepEval', 'RepEval']
	'robonlp' :	'W28', # 'RoboNLP'
	'rocling-ijclclp' :	'O', # 'ROCLING/IJCLCLP'
	's2mt' :	'W35', # 'S2MT'
	'sadaatl' :	'W60', # 'SADAATL'
	'scil' :	['W01', 'W03'], # ['SCiL', 'SCiL']
	'sedmt' :	'W06', # 'SedMT'
	'sembear' :	'W18', # 'SemBEaR'
	'semeval' :	['S', 'W08'], # ['*SEMEVAL', '*SEMEVAL']
	'semitic' :	['W05', 'W08', 'W10', 'W07'], # ['SEMITIC', 'SEMITIC', 'SEMITIC', 'SEMITIC']
	'sense' :	'W19', # 'SENSE'
	'sew' :	'W24', # 'SEW'
	'sigdial' :	['W23', 'W40', 'W46', 'W10', 'W55', 'W01', 'W50', 'W20', 'W39', 'W02', 'W16', 'W21', 'W36', 'W43', 'W13'], # ['SIGDIAL', 'SIGDIAL', 'SIGDIAL', 'SIGDIAL', 'SIGDIAL', 'SIGDIAL', 'SIGDIAL', 'SIGDIAL', 'SIGDIAL', 'SIGDIAL', 'SIGDIAL', 'SIGDIAL', 'SIGDIAL', 'SIGDIAL', 'SIGDIAL']
	'sighan' :	['W41', 'W31', 'W44', 'W18', 'W11', 'W17', 'W60', 'W63', 'W01'], # ['SIGHAN', 'SIGHAN', 'SIGHAN', 'SIGHAN', 'SIGHAN', 'SIGHAN', 'SIGHAN', 'SIGHAN', 'SIGHAN']
	'sigmorphon' :	['W23', 'W32', 'W01', 'W20', 'W07', 'W22', 'W02', 'W09', 'W06', 'W13', 'W11'], # ['SIGMORPHON', 'SIGMORPHON', 'SIGMORPHON', 'SIGMORPHON', 'SIGMORPHON', 'SIGMORPHON', 'SIGMORPHON', 'SIGMORPHON', 'SIGMORPHON', 'SIGMORPHON', 'SIGMORPHON']
	'slpat' :	['W29', 'W51', 'W19', 'W39'], # ['SLPAT', 'SLPAT', 'SLPAT', 'SLPAT']
	'socialnlp' :	['W62', 'W59', 'W17', 'W42', 'W11'], # ['SocialNLP', 'SocialNLP', 'SocialNLP', 'SocialNLP', 'SocialNLP']
	'spmrl' :	['W49', 'W38', 'W34', 'W14'], # ['SPMRL', 'SPMRL', 'SPMRL', 'SPMRL']
	'ssst' :	['W08', 'W04', 'W23', 'W40', 'W42', 'W10'], # ['SSST', 'SSST', 'SSST', 'SSST', 'SSST', 'SSST']
	'statfsm' :	'W24', # 'StatFSM'
	'step' :	'W22', # 'STEP'
	'stil' :	['W66', 'W56'], # ['STIL', 'STIL']
	'swaie' :	'W62', # 'SWAIE'
	'tacl' :	'Q', # 'TACL'
	'tag' :	['W01', 'W33', 'W15', 'W22', 'W23', 'W62', 'W44', 'W46', 'W20', 'W02'], # ['TAG+', 'TAG+', 'TAG+', 'TAG+', 'TAG+', 'TAG+', 'TAG+', 'TAG+', 'TAG+', 'TAG+']
	'teachingnlp' :	'W34', # 'TeachingNLP'
	'textgraphs' :	['W14', 'W50', 'W37', 'W24'], # ['TextGraphs', 'TextGraphs', 'TextGraphs', 'TextGraphs']
	'textinfer' :	'W24', # 'TextInfer'
	'tinlap' :	'T', # 'TINLAP'
	'tipster' :	'X', # 'TIPSTER'
	'ttnls' :	'W14', # 'TTNLS'
	'udw' :	'W04', # 'UDW'
	'vardial' :	['W53', 'W12', 'W48'], # ['VarDial', 'VarDial', 'VarDial']
	'vl' :	['W54', 'W28', 'W20'], # ['VL', 'VL', 'VL']
	'vlc' :	['W01', 'W11', 'W03'], # ['VLC', 'VLC', 'VLC']
	'wac' :	['W15', 'W17', 'W26', 'W04'], # ['WAC', 'WAC', 'WAC', 'WAC']
	'wamm' :	'W03', # 'WAMM'
	'wanlp' :	['W13', 'W32', 'W36'], # ['WANLP', 'WANLP', 'WANLP']
	'wassa' :	['W26', 'W29', 'W04', 'W52', 'W16', 'W37'], # ['WASSA', 'WASSA', 'WASSA', 'WASSA', 'WASSA', 'WASSA']
	'wat' :	['W70', 'W46', 'W50', 'W57'], # ['WAT', 'WAT', 'WAT', 'WAT']
	'wmt' :	['W33', 'W22', 'W07', 'W21', 'W47', 'W03', 'W31', 'W23', 'W30', 'W04'], # ['WMT', 'WMT', 'WMT', 'WMT', 'WMT', 'WMT', 'WMT', 'WMT', 'WMT', 'WMT']
	'wnut' :	['W44', 'W43', 'W39'], # ['WNUT', 'WNUT', 'WNUT']
	'ws' :	['W13', 'W69', 'W53', 'W26', 'W15', 'W59', 'W40', 'W11', 'W64', 'W52', 'W41', 'W68', 'W71', 'W08', 'W09', 'W72', 'W33', 'W50', 'W23', 'W27', 'W62', 'W54', 'W49', 'W57', 'W47', 'W45', 'W80', 'W14', 'W35', 'W21', 'W46', 'W01', 'W19', 'W32', 'W12', 'W03', 'W07', 'W43', 'W22', 'W79', 'W51', 'W37', 'W38', 'W30', 'W31', 'W10', 'W24', 'W73', 'W60', 'W17', 'W78', 'W55', 'W04', 'W75', 'W48', 'W74', 'W28', 'W76', 'W29', 'W05', 'W58', 'W61', 'W56', 'W85', 'W39', 'W20', 'W34', 'W70', 'W16', 'W77', 'W36', 'W44', 'W25', 'W42', 'W02', 'W18', 'W06'] # ['WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS', 'WS']
}


# from the V20190203
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

# extracted for V20191201, but not usable for the bibfile extractor due to inconsistent format!
__LETTER2ACRONYM_DICT = {
	'A' :	'anlp', # 'ANLP'
	'C' :	'coling', # 'COLING'
	'D' :	['conll', 'emnlp'], # ['CoNLL', 'EMNLP']
	'E' :	'eacl', # 'EACL'
	'F' :	'jep-taln-recital', # 'JEP/TALN/RECITAL'
	'H' :	['hlt', 'emnlp'], # ['HLT', 'EMNLP']
	'I' :	'ijcnlp', # 'IJCNLP'
	'J' :	'cl', # 'CL'
	'K' :	'conll', # 'CoNLL'
	'L' :	'lrec', # 'LREC'
	'M' :	'muc', # 'MUC'
	'N' :	['hlt', 'naacl'], # ['HLT', 'NAACL']
	'O' :	'rocling-ijclclp', # 'ROCLING/IJCLCLP'
	'P' :	'acl', # 'ACL'
	'Q' :	'tacl', # 'TACL'
	'R' :	'ranlp', # 'RANLP'
	'S' :	'semeval', # '*SEMEVAL'
	'T' :	'tinlap', # 'TINLAP'
	'U' :	'alta', # 'ALTA'
    'W' :   'SIGs', # !!! manually added instead of many W-related _items
    'X' :	'tipster', # 'TIPSTER'
	'Y' :	'paclic' # 'PACLIC'
}


def extract_volume_and_venue_infos(get_local_files=False):
    
    from aclanthology_bibfiles_downloader import extract_volume_overviews
    from aclanthology_bibfiles_downloader import logger
    from aclanthology_bibfiles_downloader import prettify_lines
    import logging
    import urllib.request
    output_path = "../outputs/" + LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEW.value
    
    #LOG
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    
    #get the URLs for all volumes
    list_of_volume_urls = extract_volume_overviews(
        output_path = output_path + LOCAL.OUTPUT_SUBFOLDER_VOLUMEOVERVIEW.value,
        output_temp_fn = None, #if None: all the files will be  kept after download
        url_stem = HTML.VOLUME_URL_STEM_CLOSED.value,
        restrictions = None
    )
    os.makedirs(output_path, exist_ok=True)
    
    letterid2info_dict = {}
    
    # download the volume and extract the relevant information from the URL or the content
    # - from the URL: letter id
    # - from the content: venue abbreviation (acronym), venue short title
    #  <dt>Venue:</dt><dd><a href=/anthology/venues/semeval/>*SEMEVAL</a></dd>
    for idx, volume_url in enumerate(list_of_volume_urls):
        volume_url = volume_url[:-1] if volume_url.endswith(FORMAT.SLASH.value) else volume_url
        
        volume_id = volume_url.split(FORMAT.SLASH.value)[-1] # e.g. P18-1, W93-03
        local_fn_ov_html = output_path + volume_id + HTML.EXTENSION_HTML.value
        
        print(f"{idx+1}./{len(list_of_volume_urls)} VOLUME url: '{volume_url}' -> '{local_fn_ov_html}'")
        
        letterid = volume_id[0]   # W
        key = letterid
        if letterid == "W":
            subtype = volume_id[-2:] # 03
            key += subtype
        letterid2info_dict.setdefault(key, set())
        
        if get_local_files is True:
            if os.path.exists(local_fn_ov_html):
                local_fn_ov_retrieved = local_fn_ov_html
                print("\tFound locally.")
            else:
                local_fn_ov_retrieved = None
        if local_fn_ov_retrieved is None:
            print("\tRetrieving.")
            local_fn_ov_retrieved, headers = urllib.request.urlretrieve(volume_url, filename=local_fn_ov_html)
    
        file = open(local_fn_ov_retrieved)  # one page of the volume overviews
        lines = file.readlines()
        file.close()
        
        pretty_lines = prettify_lines(lines)
        
        for idx, line in enumerate(pretty_lines):
            
            if line.strip() == "<dt>Venue:</dt>"  \
                or line.strip() == "<dt>Venues:</dt>": # TODO: here, we only take the first venue, even there are more than one given. Assumption: the first one is the relevant one
                #<a href=/anthology/venues/semeval/>*SEMEVAL</a>
                if len(pretty_lines) < idx+2:
                    raise ValueError(f"pretty_line[{idx}] = {line}\n length = {len(pretty_lines)} -- requested idx+2 = {idx+2}")
                venue_line = pretty_lines[idx+2]
                
                match = HTML.HREF_VENUES_PATTERN.value.search(venue_line)
                if match is not None:
                    venue = match.group(HTML.HREF_VENUE_GROUP.value)
                    short_name = match.group(HTML.HREF_SHORTNAME_GROUP.value)
                    print(f"{venue_line} ==> Venue acronym = {venue}, Short name = {short_name}")
                    letterid2info_dict[key].add((venue, short_name))
                    
                else:
                    raise ValueError(f"{idx}. line = {line}; {idx+2}. venue line: {venue_line}; not matching '{HTML.HREF_VENUES_PATTERN.value}'\n\n{list(enumerate(pretty_lines))}")
                
                break
            # elif line.strip() == "<dt>Venues:</dt>": # multiple venues are not handled for now!
            #     #TODO
            else:
                if "Venue" in line:
                    raise ValueError(f"VENUE LINE NOT MATCHED: {idx+2}: {venue_line}")
    
    return letterid2info_dict
    
    
    
def main_extract_acronym2letter_dict(get_local_files=False):
    """Extracts the venue dictionary for further use."""
    
    letter2info = extract_volume_and_venue_infos(get_local_files=get_local_files)
    acronym2info = {}
    
    s = """LETTER2ACRONYM_DICT = {\n"""
    
    for letter, acronym_shortname_tuples in sorted(letter2info.items()): #value: set of (acronym, short_name) tuples
        acronym_shortname_tuples = list(acronym_shortname_tuples)
    
        if len(acronym_shortname_tuples) < 1:
            print(f"No acronym for letter ID '{letter}'")
    
        acronym, shortname = acronym_shortname_tuples[0]
        acronym2info.setdefault(acronym, set())
        value = (letter, shortname)
        acronym2info[acronym].add(value)
        
        acronym = "'" + acronym + "'"
        shortname = "'" + shortname + "'"
    
        if len(acronym_shortname_tuples) > 1:
            print(f"{len(acronym_shortname_tuples)} acronyms for letter ID '{letter}': {acronym_shortname_tuples}")
            acronym = []
            shortname = []
            for acro, short in acronym_shortname_tuples:
                acronym.append(acro)
                shortname.append(short)
                value = (letter, short)
                acronym2info.setdefault(acro, set())
                acronym2info[acro].add(value)
        
    
        s += f"\t'{letter}' :\t{acronym}, # {shortname}\n"
    
    s += "}"
    print(s)
    print()
    
    t = """ACRONYM2LETTER_DICT = {\n"""
    for acronym, letter_shortname_tuples in sorted(acronym2info.items()):
        letter_shortname_tuples = list(letter_shortname_tuples)

        if len(letter_shortname_tuples) < 1:
            print(f"No letter ID for acronym '{acronym}'")
        letter, shortname = letter_shortname_tuples[0]
        letter = "'" + letter + "'"
        shortname = "'" + shortname + "'"
        
        if len(letter_shortname_tuples) > 1:
            print(f"{len(letter_shortname_tuples)} letter IDs for acronym '{acronym}': {letter_shortname_tuples}")
            letter = []
            shortname = []
            for let, short in letter_shortname_tuples:
                letter.append(let)
                shortname.append(short)
                value = (acronym, short)
    
        t += f"\t'{acronym}' :\t{letter}, # {shortname}\n"
    
    t += "}"
    print(t)

if __name__ == "__main__":
    #main_extract_acronym2letter_dict(get_local_files=False)
    main_extract_acronym2letter_dict(get_local_files=True)
    