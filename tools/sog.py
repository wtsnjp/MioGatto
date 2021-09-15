# An analysis script for sources of grounding
import lxml.html
import numpy as np
from docopt import docopt
from pathlib import Path

from lib.version import VERSION
from lib.cli import set_level
from lib.common import get_mi2idf, load_anno_json, load_mcdict_json

# use logger
import logging as log

log.Logger.set_level = set_level
logger = log.getLogger('sog')

# meta
PROG_NAME = "tools.sog"
HELP = """An analysis script for sources of grounding

Usage:
    {p} [options] ID

Options:
    --data=DIR      Dir for the gold data [default: ./data]
    --sources=DIR   Dir for preprocessed HTML [default: ./sources]

    -s, --show-sog  Show actual SoG by concept
    -d, --debug     Show debug messages
    -q, --quiet     Show less messages

    -h, --help      Show this screen and exit
    -V, --version   Show version
""".format(p=PROG_NAME)


def analyze_sog(tree, mi_anno, concepts):
    mi2idf = get_mi2idf(tree)
    root = tree.getroot()

    # prepare the word info
    wl, words = [], dict()
    for e in root.xpath('//span[@class="gd_word"]'):
        w_id = e.attrib.get('id')
        wl.append(w_id)
        if type(e.text) is str:
            words[w_id] = e.text
            # TODO: check for the else case

    # add sog field to concepts
    for v in concepts.values():
        for cs in v['identifiers'].values():
            for c in cs:
                c['sog'] = []

    # get actual text
    for mi_id, anno in mi_anno.items():
        for sog in anno['sog']:
            w_ids = wl[wl.index(sog[0]):wl.index(sog[1]) + 1]
            idf, c_id = mi2idf[mi_id], anno['concept_id']
            idf_hex, idf_var = idf['idf_hex'], idf['idf_var']
            concepts[idf_hex]['identifiers'][idf_var][c_id]['sog'].append(
                ' '.join([
                    words[w_id] for w_id in w_ids
                    if words.get(w_id) is not None
                ]))


def main():
    # parse options
    args = docopt(HELP, version=VERSION)

    # setup logger
    log_level = log.INFO
    if args['--quiet']:
        log_level = log.WARN
    if args['--debug']:
        log_level = log.DEBUG
    logger.set_level(log_level)

    paper_id = args['ID']

    # dirs and files
    data_dir = Path(args['--data'])

    sources_dir = Path(args['--sources'])
    source_html = sources_dir / '{}.html'.format(paper_id)

    anno_json = data_dir / '{}_anno.json'.format(paper_id)
    mcdict_json = data_dir / '{}_mcdict.json'.format(paper_id)

    # load the data
    mi_anno, annotator = load_anno_json(anno_json, logger)
    concepts, mcdict_author = load_mcdict_json(mcdict_json, logger)

    # analyze and show the results
    tree = lxml.html.parse(str(source_html))
    analyze_sog(tree, mi_anno, concepts)

    print('* Metadata')
    print('Paper ID: {}'.format(paper_id))
    print('Author of math concept dict: {}'.format(annotator))
    print('Annotator: {}'.format(mcdict_author))
    print()

    print('* Number of SoG by concept')
    nof_sogs = [
        len(c['sog']) for v in concepts.values()
        for cs in v['identifiers'].values() for c in cs
    ]
    print('Max: {}'.format(max(nof_sogs)))
    print('Median: {}'.format(int(np.median(nof_sogs))))
    print('Mean: {:.1f}'.format(np.mean(nof_sogs)))
    print('Variance: {:.1f}'.format(np.var(nof_sogs)))
    print('Standard deviation: {:.1f}'.format(np.std(nof_sogs)))
    print()

    if not args['--show-sog']:
        exit(0)

    print('* Actual SoG by concept')
    for v in concepts.values():
        for idf_var, cs in v['identifiers'].items():
            print('{} ({})'.format(v['surface']['text'], idf_var))
            for c in cs:
                print('    - {}'.format(c['description']))
                for idx, sog in enumerate(c['sog']):
                    print('        {}. {}'.format(idx + 1, sog))


if __name__ == '__main__':
    main()
