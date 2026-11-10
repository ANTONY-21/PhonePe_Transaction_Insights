"""Match PhonePe state slugs to geoBoundaries administrative units."""
import re
import unicodedata


def normalize_state(value):
    value = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
    value = value.lower().replace('&', ' and ')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', value)).strip()


def join_states(frame, geojson):
    by_name = {normalize_state(feature['properties']['shapeName']): feature['properties']['shapeISO']
               for feature in geojson['features']}
    result = frame.copy()
    result['shape_iso'] = result['state'].map(lambda state: by_name.get(normalize_state(state)))
    return result, sorted(result.loc[result['shape_iso'].isna(), 'state'].tolist())
