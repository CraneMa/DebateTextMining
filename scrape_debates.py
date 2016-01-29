import requests
from bs4 import BeautifulSoup
from bs4 import NavigableString
from sklearn.externals import joblib
import time
import re
import pandas as pd
import string
from itertools import chain
from operator import itemgetter

def get_page(pid):
    return requests.get('http://www.presidency.ucsb.edu/ws/index.php?pid={0}'.format(pid)).text


def find_speaker(d, pid):
    # Speaker in caps, not bolded, with colon:
    if pid in [29400, 29401, 29402, 29403, 62249, 29407, 29425, 29424, 29411, 29412, 29423, 29422,
               29421, 29418, 29419, 29420, 29428, 76562, 76561]:
        if type(d)!=unicode:
            speaker = re.match(r'(^(([(Mc)(MaC)A-Z\.,/])+( )*){1,11}:)',d.get_text())
            
            return speaker.group(1) if speaker else None
        else:
            speaker = re.match(r'(^(([(Mc)(MaC)A-Z\.,])+( )*){1,11}:)',d)
            return speaker.group(1) if speaker else None

    #Speaker in italics, not capitalized, followed by period:
    elif pid in [52060, 52115, 72770, 72776, 63163, 102317, 102343, 102344]:
        if type(d)!=unicode:
            speaker = d.i.get_text() if d.i is not None and len(d.i.get_text())>1 else None
            if speaker:
                #flag italicized section headers for removal:
                if d.i.get_text() == d.get_text(): return "REMOVE"

                if re.match(r'(^((([\w\.,])+( )*){1,3}\.(.)*))', speaker):
                    return speaker
            return None
        else:
            speaker = re.search(r'^((Bob)|(Candy)|(Charles)|(Jim))\s([\w\.])*\s*([\w]+){1,2}\.',d)
            
            if speaker:
                return speaker
            return None
    
    #Speaker like rest of text, followed by period:
    elif pid in [39199, 39296, 21605, 21617, 21625]:
        if type(d)!=unicode:
            speaker = re.search(r'^([\w\.]*)((Mr.)|(Ms.)|(The)|(President)|(Governor)|(Senator)|(Ann)|(Jim)|(John)|(Sander)|(Carole)|(Q)|(Helen)|(Gene)|(Susan)|(Fred))\s([\w]+)\.',d.get_text())


            return speaker.group(0) if speaker else None
        else:
            speaker = re.search(r'^([\w\.]*)((Mr.)|(Ms.)|(The)|(President)|(Governor)|(Senator)|(Ann)|(Jim)|(John)|(Sander)|(Carole)|(Q)|(Helen)|(Gene)|(Susan)|(Fred))\s([\w]+)\.',d)
            return speaker.group(0) if speaker else None

    # Speaker in caps, not bolded, with period:
    elif pid in [29404, 6414, 6517, 29408]:
        if type(d)!=unicode:
            speaker = re.match(r'(^(([(Mc)(MaC)A-Z\.,])+( )*){1,3}\.)',d.get_text())
            return speaker.group(1) if speaker else None
        else:
            speaker = re.match(r'(^(([(Mc)(MaC)A-Z\.,])+( )*){1,3}\.)',d)
            return speaker.group(1) if speaker else None
            
    else:
        if type(d)!=unicode:
            return d.b.get_text() if d.b is not None and len(d.b.get_text())>1 else None
        else:
            speaker = re.match(r'(^(([(Mc)(MaC)A-Z\.])+( )*){1,3}:)',d)
            return speaker.group(1) if speaker else None

        
def parse_debate(pid, debate):
    
    lines = []
    punct_re = re.compile('[%s]' % re.escape(string.punctuation))
    for i,d in enumerate(debate):
        
        speaker = find_speaker(d, pid)
        if speaker is None and i==0:
            speaker = "UNSPECIFIED"

        if speaker is not None: current_speaker = speaker
        if speaker is None: speaker = current_speaker
            
        split_s = ''.join([sp for sp in speaker if sp != u':']).split(" ")
        if type(d)!= unicode:
            d=d.get_text()
            d = ''.join([de if ord(de)<128 else "--" for de in d])

            split_d = ''.join([de for de in d if de != u':']).split(" ")

        else:
            split_d = ''.join([de for de in d if de != u':']).split(" ")

        content = " ".join([d for d in split_d if d not in split_s])
        speaker = [a for a in punct_re.sub('',speaker).split(" ") if a is not u''][-1]
        done = [speaker, content]
        lines.append(done)
      
    
    speakerlist = [lines[0][0]]
    linelist = [lines[0][1]]

    allspeakers = map(itemgetter(0),lines)
    alllines = map(itemgetter(1),lines)
    
    for line,speaker in zip(alllines,allspeakers):
        if speaker==speakerlist[-1]:
            linelist[-1]+=" " + line
        else:
            linelist.append(line)
            speakerlist.append(speaker)
    
    new_lines = zip(speakerlist,linelist) 
    
    return new_lines
    #return lines


def scrape_transcripts(page, pid):
    
    primary_soup = BeautifulSoup(page, 'lxml')
    
    title = primary_soup.find('span', 'paperstitle').get_text()
    date = time.strptime(primary_soup.find('span', 'docdate').get_text(), "%B %d, %Y")[:3]
    meat = primary_soup.find('span', 'displaytext')
    debate = [unicode(m) for m in meat.contents if isinstance(m, NavigableString)]
    
    for m in meat('p'):
        debate.append(m)

    return (parse_debate(pid, debate), title, date)


def get_debates():
    
    master_page = requests.get('http://www.presidency.ucsb.edu/debates.php').text
    master_soup = BeautifulSoup(master_page, 'lxml')
    link_re = re.compile(r'(http://www\.presidency\.ucsb\.edu/ws/index\.php\?pid=)([\d]{4,6})')
    links = [lin.attrs['href'] for lin in master_soup.find_all('a')]
    pids = [found.group(2) for link in links for found in [link_re.search(link)] if found]  

    frames=[]

    for pid in [110910,110903,110908,110909,110906,110907,110756,110758,110489,110757,102344,102343,102317,102322,99556,
    99075,99001,98936,98929,98814,98813,97978,97703,97332,97038,97022,96914,96894,96795,96683,96659,96660,90711,90513,
    84526,84482,78691,84382,76913,76688,76563,76339,76271,76237,76224,76123,76122,76041,75950,75796,76561,75664,75631,
    75575,75489,75140,74349,76338,76300,62265,29427,76223,29664,76562,76069,75914,75861,75913,75680,75630,75171,74348,
    74350,63163,72776,72770,29428,75118,74351,29420,29419,29418,29421,105446,105445,105444,105449,105448,109919,105447,
    105443,105442,105441,105440,105439,105438,105437,76120,75089,105436,105435,75090,52115,52060,29422,21625,21617,21605,
    29423,29412,29411,29424,39296,39199,29425,29408,29407,6517,6414,29404,62249,29403,29402,29401,29400,111178,111177,111176]:

        lines, title, date = scrape_transcripts(get_page(pid), pid)    
        for line in lines:  
            frames.append(make_line(line, title, date, pid, pids))
                
    data = pd.DataFrame(frames)
    remove = data.Speaker.isin(['moderators','participants','candidates', 'panelists', 'sponsor', 'others','us','action'])  # 1st 2000 dem primary: just single moderator
    
    return data[~remove]


def make_line(line, title, date, pid, pids):
    new_dict = {"Speaker": line[0].encode('ascii','ignore').lower(),
                "Line_Orig": remove_inter(line[1].encode('ascii','ignore')),
                "Line": split_line(remove_apost(line[1].encode('ascii','ignore'))),
                "Line_Cleaned": clean(remove_inter(remove_apost(line[1].encode('ascii','ignore')))), 
                "Event": title, 
                "Date": date,
                "Speaker_Type": "Cand" if is_cand(line[0].encode('ascii','ignore').lower()) else "Mod",
                "Speaker_Party": is_cand(line[0].encode('ascii','ignore').lower()),
                "Event_ID": pid, 
                'Interjections': "...".join([f for f in find_inter(line[1].encode('ascii','ignore'))]), 
                'Elec_Year': date[0] if date[0]%2==0 else date[0]+1, 
                'Event_Type' : get_type(pid, pids)}
    return new_dict


"""Helper functions:"""

def remove_inter(line):
    return re.sub(r'((\[\s*([\w\., ]+)\s*\])|(\(([\w\., ]+)\)))', '', line)

def find_inter(line):
    lines = list(chain(*re.findall(r'\[([\w\., ]+)\]|\(([\w\., ]+)\)', line)))
    return [''.join([i for i in inter if re.match('[A-Za-z, ]',i)]).lower() for inter in lines if inter is not '']
    
def split_line(line):
    return re.findall(r"[\w]+|[.,?!-;:]",line.lower())

def remove_apost(line):
    return re.sub(r"'", '',line)

def clean(line):

    line = [a for a in split_line(line.lower()) if a.isalpha()]
    #based on NLTK:
    stopwords=['i','me','my','myself','we','our','ours','ourselves',
              'you','your','yours','yourself','yourselves','he',
              'him','his','himself','she','her','hers','herself',
              'it','its','itself','they','them','their','theirs',
              'themselves','what','which','who','whom','this','that',
              'these','those','am','is','are','was','were','be','been',
               'being','have','has','had','having','do','does','did',
               'doing','a','an','the','and','but','if','or','because',
               'as','until','while','of','at','by','for','with','about',
               'against','between','into','through','during','before',
               'after','above','below','to','from','up','down','in',
               'out','on','off','over','under','again','further','then',
               'once','here','there','when','where','why','how','all',
               'any','both','each','few','more','most','other','some',
               'such','no','nor','not','only','own','same','so',
               'than','too','very','can','will','just',
                'now', #should
               'ive','im','id','youre','youve','youd','hed','hes','shes',
              'shed','weve','wed','theyve','theyd','theyre',
              'thats', 'thatd','dont','doesnt','wont',
              'isnt','arent','wasnt','werent','cant']

    return [w for w in line if w not in stopwords]

def get_type(pid, pids):
    
    _2016_prim_d = pids[-125:-123]
    _2016_prim_r = pids[-123:-115]
    _2012_gen = pids[-115:-111]
    _2012_prim_r = pids[-111:-91]
    _2008_gen = pids[-91:-87]
    _2008_prim_d = pids[-87:-68]
    _2008_prim_r = pids[-68:-52]
    _2004_gen = pids[-52:-48]
    _2004_prim_d = pids[-48:-46]
    _2000_gen = pids[-46:-42]
    _2000_prim_d = pids[-42:-34]
    _2000_prim_r = pids[-34:-23]
    _1996_gen = pids[-23:-20]
    _1992_gen = pids[-20:-16]
    _1988_gen = pids[-16:-13]
    _1984_gen = pids[-13:-10]
    _1980_gen = pids[-10:-8]
    _1976_gen = pids[-8:-4]
    _1960_gen = pids[-4:]
        
    if pid in chain(_2016_prim_d, _2016_prim_r,_2012_prim_r,_2008_prim_d,
                    _2008_prim_r, _2004_prim_d,_2000_prim_d, _2000_prim_r):
        return "Primary"
    elif pid in [102322, 84382, 29428, 29421, 29422, 29423, 29424, 29425, 62249]:
        return "Vice_Presidential"
    else:
        return 'Presidential'


def is_cand(speaker):
    cands = {'fiorina':'r', 'gilmore':'r', 'graham':'r', 'jindal':'r', 'pataki':'r', 'perry':'r', 'santorum':'r',
                    'bush':'r', 'carson':'r', 'christie':'r', 'cruz':'r', 'huckabee':'r', "kasich":'r', 'paul':'r', 'rubio':'r',
                    'trump':'r', 'walker':'r', 
                    'chafee':'d', 'clinton':'d', "omalley":'d', 'sanders':'d', 'webb':'d',
                    'romney':'r', 'ryan': 'r',
                    'pawlenty':'r', 'paul':'r', 'bachmann':'r', 'cain':'r', 'gingrich':'r', 'huntsman':'r',
                    'mccain':'r', 'obama':'d', 'palin': 'r', 'biden':'d',
                    'dodd':'d', 'edwards':'d', 'richardson':'d', 'kucinich':'d', 'gravel':'d', 
                    'thompson':'r', 'tancredo':'r', 'hunter':'r', 'giuliani':'r', 'brownback':'r',
                    'bush':'r',' kerry':'d',
                    'clark':'d', 'lieberman':'d', 'dean':'d', 'sharpton':'d',
                    'cheney':'r', 'gore':'d',
                    'bradley':'d', 
                    'bauer':'r', 'hatch':'r', 'forbes':'r', 'keyes':'r', 'bush':'r',
                    'dole':'r', 'kemp':'r',
                    'bush':'r', 'perot':'i', 'clinton':'d', 'stockdale':'i',
                    'dukakis':'d', 'quayle':'r', 'bentsen':'d',
                    'mondale':'d', 'ferraro':'d',
                    'carter':'d', 'anderson':'i', 
                    'nixon':'r', 'kennedy':'d',
                    'president':'n'}
    return cands[speaker] if speaker in cands else None
