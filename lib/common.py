# The common codes
import json


def get_mi2idf(tree):
    root = tree.getroot()
    mi2idf = dict()

    # dirty settings
    ellipsises = [
        'e280a6',  # HORIZONTAL ELLIPSIS (…)
        'e28baf',  # MIDLINE HORIZONTAL ELLIPSIS (⋯)
    ]

    # loop mi in the tree
    for e in root.xpath('//mi'):
        mi_id = e.attrib.get('id')

        # skip if empty
        if e.text is None:
            continue

        # get idf hex
        idf_hex = e.text.encode().hex()

        # None if ellipsises
        if idf_hex in ellipsises:
            mi2idf[mi_id] = None
            continue

        # detect the idf variant
        # Note: mathvariant is replaced (None -> default, normal -> roman)
        idf_var = e.attrib.get('mathvariant', 'default')
        if idf_var == 'normal':
            idf_var = 'roman'

        mi2idf[mi_id] = {'idf_hex': idf_hex, 'idf_var': idf_var}

    return mi2idf


def load_anno_json(fn, logger):
    with open(fn, encoding='utf-8') as f:
        data = json.load(f)

    if data.get('anno_version', '') != '0.2':
        logger.warning('{}: Annotation data version is incompatible', fn)

    return data['mi_anno'], data['annotator']


def load_mcdict_json(fn, logger):
    with open(fn, encoding='utf-8') as f:
        data = json.load(f)

    if data.get('mcdict_version', '') != '0.2':
        logger.warning('{}: Math concept dict version is incompatible', fn)

    return data['concepts'], data['annotator']
