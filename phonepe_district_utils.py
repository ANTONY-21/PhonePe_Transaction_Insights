"""Match district names conservatively within a selected state."""
import re
import unicodedata


def normalize_name(value):
    value=unicodedata.normalize('NFKD',str(value)).encode('ascii','ignore').decode().lower().replace('&',' and ')
    value=re.sub(r'\bdistrict\b',' ',value)
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',value)).strip()


STATE_ALIASES={
    'andaman and nicobar islands': ['andaman and nicobar island'],
    'arunachal pradesh': ['arunanchal pradesh'],
    'delhi': ['nct of delhi'],
    'dadra and nagar haveli and daman and diu': ['dadara and nagar havelli','daman and diu'],
}

# Known name changes and alternate spellings. Historical shapes may not have
# the same extents as today's districts.
DISTRICT_ALIASES={'karnataka': {
    'bagalkote':'bagalkot', 'ballari':'bellary', 'belagavi':'belgaum',
    'bengaluru rural':'bangalore rural', 'bengaluru urban':('bengaluru', 'bangalore'),
    'chamarajanagar':('chamarajanagara', 'chamrajnagar'), 'chikkaballapur':'chikkaballapura',
    'chikkamagaluru':'chikmagalur', 'kalaburagi':'gulbarga', 'mysuru':'mysore',
    'shivamogga':'shimoga', 'tumakuru':'tumkur', 'vijayapura':'bijapur',
    'yadgiri':'yadgir',
}, 'telangana': {'jagtial':'jagitial', 'jangaon':'jangoan',
                 'jayashankar bhupalpally':'jayashankar', 'rangareddy':'ranga reddy'},
   'ladakh': {'leh ladakh':'leh'}}


def match_districts(frame, geojson, state):
    selected=normalize_name(state)
    allowed=set(STATE_ALIASES.get(selected,[selected]))
    shapes={}
    for feature in geojson['features']:
        p=feature['properties']
        if normalize_name(p['state']) in allowed:
            shapes.setdefault(normalize_name(p['district']),[]).append(p['shape_key'])
    aliases=DISTRICT_ALIASES.get(selected,{})
    result=frame.copy()
    def match(name):
        key=normalize_name(name)
        alternatives=aliases.get(key,())
        if isinstance(alternatives,str):
            alternatives=(alternatives,)
        for candidate in (key,*alternatives):
            hits=shapes.get(candidate,[])
            if hits:
                return hits[0] if len(hits)==1 else None
        return None
    result['shape_key']=result['district'].map(match)
    # Never map multiple current districts to the same historical polygon.
    duplicate=result['shape_key'].notna() & result['shape_key'].duplicated(keep=False)
    result.loc[duplicate,'shape_key']=None
    return result, sorted(result.loc[result['shape_key'].isna(),'district'].tolist())


def choose_boundaries(frame, state, sources):
    """Choose one boundary collection per state; never merge polygons from sources."""
    best=None
    for label, geojson in sources:
        matched, unmatched=match_districts(frame,geojson,state)
        candidate=(label,geojson,matched,unmatched)
        if best is None or len(unmatched)<len(best[3]):
            best=candidate
    return best
