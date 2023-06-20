# Common utilities


def get_mi2idf(tree):
    root = tree.getroot()
    mi2idf = dict()

    # dirty settings
    non_identifiers = [
        'e280a6',  # HORIZONTAL ELLIPSIS (…)
        'e28baf',  # MIDLINE HORIZONTAL ELLIPSIS (⋯)
        'e28bae',  # VERTICAL ELLIPSIS (⋮)
        'e28bb1',  # DOWN RIGHT DIAGONAL ELLIPSIS (⋱)
        'e296a1',  # QED BOX (□)
    ]

    # loop mi in the tree
    for e in root.xpath('//mi'):
        mi_id = e.attrib.get('id')

        # skip if empty
        if e.text is None:
            continue

        # get idf hex
        idf_hex = e.text.encode().hex()

        # None if non-identifiers
        if idf_hex in non_identifiers:
            mi2idf[mi_id] = None
            continue

        # detect the idf variant
        # Note: mathvariant is replaced (None -> default, normal -> roman)
        idf_var = e.attrib.get('mathvariant', 'default')
        if idf_var == 'normal':
            idf_var = 'roman'

        mi2idf[mi_id] = {'idf_hex': idf_hex, 'idf_var': idf_var}

    return mi2idf
