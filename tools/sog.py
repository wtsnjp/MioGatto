# An analysis script for sources of grounding
import lxml.html
import numpy as np
from docopt import docopt
from pathlib import Path

from lib.version import VERSION
from lib.logger import get_logger
from lib.util import get_mi2idf
from lib.annotation import MiAnno, McDict

# meta
PROG_NAME = "tools.sog"
HELP = """An analysis script for sources of grounding

Usage:
    {p} [options] ID

Options:
    -d DIR, --data=DIR  Dir for the gold data [default: ./data]
    --sources=DIR       Dir for preprocessed HTML [default: ./sources]

    -s, --show-sog      Show actual SoG by concept
    -D, --debug         Show debug messages
    -q, --quiet         Show less messages

    -h, --help          Show this screen and exit
    -V, --version       Show version
""".format(p=PROG_NAME)

logger = get_logger(PROG_NAME)


def analyze_sog(tree, mi_anno: MiAnno, mcdict: McDict) -> dict:
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

    # initialize sog_by_concept
    sog_by_concept = {
        idf_hex: {
            idf_var: [[] for _ in cs]
            for idf_var, cs in v.items()
        }
        for idf_hex, v in mcdict.concepts.items()
    }

    # get actual text
    for mi_id, anno in mi_anno.occr.items():
        for sog in anno['sog']:
            w_ids = wl[wl.index(sog['start']):wl.index(sog['stop']) + 1]
            idf, c_id = mi2idf[mi_id], anno['concept_id']
            idf_hex, idf_var = idf['idf_hex'], idf['idf_var']
            sog_by_concept[idf_hex][idf_var][c_id].append(' '.join([
                words[w_id] for w_id in w_ids if words.get(w_id) is not None
            ]))

    return sog_by_concept


def main():
    # parse options
    args = docopt(HELP, version=VERSION)

    logger.set_logger(args['--quiet'], args['--debug'])
    paper_id = args['ID']

    # dirs and files
    data_dir = Path(args['--data'])

    sources_dir = Path(args['--sources'])
    source_html = sources_dir / '{}.html'.format(paper_id)

    anno_json = data_dir / '{}_anno.json'.format(paper_id)
    mcdict_json = data_dir / '{}_mcdict.json'.format(paper_id)

    # load the data
    mi_anno = MiAnno(anno_json, logger)
    mcdict = McDict(mcdict_json, logger)

    # analyze and show the results
    tree = lxml.html.parse(str(source_html))
    sog_by_concept = analyze_sog(tree, mi_anno, mcdict)

    print('* Metadata')
    print('Paper ID: {}'.format(paper_id))
    print('Author of math concept dict: {}'.format(mi_anno.annotator))
    print('Annotator: {}'.format(mcdict.author))
    print()

    print('* Number of SoG by concept')
    nof_sogs = [
        len(sogs) for v in sog_by_concept.values() for cs in v.values()
        for sogs in cs
    ]
    print('Max: {}'.format(max(nof_sogs)))
    print('Median: {}'.format(int(np.median(nof_sogs))))
    print('Mean: {:.1f}'.format(np.mean(nof_sogs)))
    print('Variance: {:.1f}'.format(np.var(nof_sogs)))
    print('Standard deviation: {:.1f}'.format(np.std(nof_sogs)))
    print('#zeros: {}'.format(nof_sogs.count(0)))
    print()

    if not args['--show-sog']:
        exit(0)

    print('* Actual SoG by concept')
    for idf_hex, v in sog_by_concept.items():
        for idf_var, cs in v.items():
            print('{} ({})'.format(mcdict.surfaces[idf_hex]['text'], idf_var))
            for cid, sogs in enumerate(cs):
                print('    - {}'.format(
                    mcdict.concepts[idf_hex][idf_var][cid].description))
                for idx, sog in enumerate(sogs):
                    print('        {}. {}'.format(idx + 1, sog))


if __name__ == '__main__':
    main()
