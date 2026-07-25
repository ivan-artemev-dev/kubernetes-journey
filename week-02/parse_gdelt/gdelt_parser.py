#!/usr/bin/env python3
"""
Парсер GKG V2 файлов GDELT.
Колонки (табуляция):
0  GKGRECORDID
1  DATE (YYYYMMDDHHmmss)
2  SourceCollectionIdentifier
3  SourceCommonName
4  DocumentIdentifier (URL)
5  Counts
6  V2Counts
7  Themes
8  V2Themes        ← theme,offset;theme,offset
9  Locations
10 V2Locations     ← type#name#cc#adm1#adm2#lat#lon#featureid#offset;...
11 Persons
12 V2Persons       ← name,offset;...
13 Organizations
14 V2Organizations ← name,offset;...
15 V2Tone          ← tone,pos,neg,polarity,activity,selfref
16 Dates
17 GCAM            ← key:value,key:value,...
18 SharingImage
19 RelatedImages
20 SocialImageEmbeds
21 SocialVideoEmbeds
22 Quotations      ← offset#speaker#speakeroffset#quote|...
23 AllNames        ← name,offset;...
24 Amounts         ← amount,object,offset;...
25 TranslationInfo
26 Extras
"""


def parse_tone(s):
    if not s:
        return {}
    parts = s.split(',')
    keys = ['tone', 'positive', 'negative', 'polarity', 'activity', 'selfref']
    result = {}
    for i, key in enumerate(keys):
        if i < len(parts):
            try:
                result[key] = float(parts[i])
            except ValueError:
                pass
    return result


def parse_v2themes(s):
    """V2Themes: theme,offset;theme,offset → список тем"""
    if not s:
        return []
    themes = []
    for item in s.split(';'):
        item = item.strip()
        if ',' in item:
            theme = item.rsplit(',', 1)[0].strip()
        else:
            theme = item
        if theme:
            themes.append(theme)
    return list(set(themes))  # дедупликация


def parse_v2entities(s):
    """V2Persons/V2Organizations: name,offset;... → список имён"""
    if not s:
        return []
    entities = []
    for item in s.split(';'):
        item = item.strip()
        if ',' in item:
            name = item.rsplit(',', 1)[0].strip().lower()
        else:
            name = item.strip().lower()
        if name:
            entities.append(name)
    return list(set(entities))


def parse_v2locations(s):
    """V2Locations: type#name#cc#adm1#adm2#lat#lon#featureid#offset;..."""
    if not s:
        return []
    locations = []
    seen = set()
    for loc in s.split(';'):
        parts = loc.strip().split('#')
        if len(parts) < 7:
            continue
        try:
            lat = float(parts[5]) if parts[5] else None
            lon = float(parts[6]) if parts[6] else None
            if lat is None or lon is None:
                continue
            key = f"{parts[1]}_{lat}_{lon}"
            if key in seen:
                continue
            seen.add(key)
            locations.append({
                "geo_type":    int(parts[0]) if parts[0].isdigit() else 0,
                "fullname":    parts[1],
                "countrycode": parts[2],
                "adm1code":    parts[3],
                "adm2code":    parts[4] if len(parts) > 4 else '',
                "location":    {"lat": lat, "lon": lon},
            })
        except (ValueError, IndexError):
            pass
    return locations


def parse_quotations(s):
    """Quotations: offset#speaker#speakeroffset#quote|..."""
    if not s:
        return []
    quotes = []
    for item in s.split('|'):
        parts = item.split('#')
        if len(parts) >= 4:
            speaker = parts[1].strip().lower()
            quote = parts[3].strip()
            if quote:
                quotes.append({"speaker": speaker, "quote": quote})
    return quotes


def parse_allnames(s):
    """AllNames: name,offset;..."""
    if not s:
        return []
    names = []
    for item in s.split(';'):
        item = item.strip()
        if ',' in item:
            name = item.rsplit(',', 1)[0].strip().lower()
        else:
            name = item.lower()
        if name:
            names.append(name)
    return list(set(names))


def parse_amounts(s):
    """Amounts: amount,object,offset;..."""
    if not s:
        return []
    amounts = []
    for item in s.split(';'):
        parts = item.strip().split(',')
        if len(parts) >= 2:
            try:
                amount = float(parts[0])
                obj = parts[1].strip()
                amounts.append({"amount": amount, "object": obj})
            except ValueError:
                pass
    return amounts


def parse_gcam(s):
    """GCAM: key:value,key:value,... → dict"""
    if not s:
        return {}
    result = {}
    for item in s.split(','):
        if ':' in item:
            k, v = item.split(':', 1)
            try:
                result[k.strip()] = float(v.strip())
            except ValueError:
                result[k.strip()] = v.strip()
    return result


def row_to_doc(row):
    if len(row) < 16:
        return None

    record_id = row[0].strip() if len(row) > 0 else ''
    date_str  = row[1].strip() if len(row) > 1 else ''
    source    = row[3].strip() if len(row) > 3 else ''
    url       = row[4].strip() if len(row) > 4 else ''
    raw_counts= row[6].strip() if len(row) > 6 else ''
    raw_themes= row[8].strip() if len(row) > 8 else ''
    raw_locs  = row[10].strip() if len(row) > 10 else ''
    v2persons = row[12].strip() if len(row) > 12 else ''
    v2orgs    = row[14].strip() if len(row) > 14 else ''
    tone_str  = row[15].strip() if len(row) > 15 else ''
    gcam_str  = row[17].strip() if len(row) > 17 else ''
    sharing   = row[18].strip() if len(row) > 18 else ''
    quotes    = row[22].strip() if len(row) > 22 else ''
    allnames  = row[23].strip() if len(row) > 23 else ''
    amounts   = row[24].strip() if len(row) > 24 else ''
    trans     = row[25].strip() if len(row) > 25 else ''

    if not date_str or len(date_str) < 8:
        return None

    return {
        "record_id":       record_id,
        "date":            date_str,
        "source_name":     source,
        "url":             url,
        "themes":          parse_v2themes(raw_themes),
        "locations":       parse_v2locations(raw_locs),
        "persons":         parse_v2entities(v2persons),
        "organizations":   parse_v2entities(v2orgs),
        "tone":            parse_tone(tone_str),
        "gcam":            parse_gcam(gcam_str),
        "sharing_image":   sharing,
        "quotations":      parse_quotations(quotes),
        "all_names":       parse_allnames(allnames),
        "amounts":         parse_amounts(amounts),
        "translation_info": trans,
        "raw_themes":      raw_themes,
        "raw_locations":   raw_locs,
        "raw_counts":      raw_counts,
    }