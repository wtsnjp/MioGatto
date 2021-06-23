# The analyzer tool for MioGatto
import json
import itertools
import lxml.html
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from docopt import docopt
from pathlib import Path

from lib.version import VERSION
from lib.cli import set_level
from lib.common import get_mi2idf

# use logger
import logging as log

log.Logger.set_level = set_level
logger = log.getLogger('analyzer')

# meta
PROG_NAME = "tools.analyzer"
HELP = """Analysing tool for MioGatto

Usage:
    {p} [options] ID

Options:
    -o DIR, --out=DIR  Dir to save results [default: ./results]
    --data=DIR         Dir for the gold data [default: ./data]
    --sources=DIR      Dir for preprocessed HTML [default: ./sources]

    -d, --debug        Show debug messages
    -q, --quiet        Show less messages

    -h, --help         Show this screen and exit
    -V, --version      Show version
""".format(p=PROG_NAME)


def extract_info(tree):
    mi2idf = get_mi2idf(tree)
    root = tree.getroot()
    html_str = lxml.html.tostring(tree, encoding='utf-8').decode('utf-8')

    # extract mi info
    mi_info = dict()
    for e in root.xpath('//mi'):
        mi_id = e.attrib.get('id')

        # idf info
        idf = mi2idf.get(mi_id)

        if idf is not None:
            mi_info[mi_id] = idf
        else:
            continue

        # position info
        pos = html_str.find(
            lxml.html.tostring(e, encoding='utf-8').decode('utf-8'))
        mi_info[mi_id]['pos'] = pos

    # extract section info
    sec_info = dict()
    for e in root.xpath('//section'):
        sec_id = e.attrib.get('id')
        pos = html_str.find(
            lxml.html.tostring(e, encoding='utf-8').decode('utf-8'))
        sec_info[sec_id] = pos

    logger.debug('sec_info: %s', sec_info)

    return mi_info, sec_info


def analyze_annotation(data_anno, data_mcdict, mi_info):
    # basic analysis for mcdict
    nof_idf = 0
    nof_idf_mul = 0
    nof_concept = 0

    concepts = data_mcdict['concepts']

    for letter in concepts.values():
        nof_idf += len(letter['identifiers'])

        for idf in letter['identifiers'].values():
            if len(idf) > 1:
                nof_idf_mul += 1
            nof_concept += len(idf)

    print('* Basic information')
    print('#strings for identifiers: {}'.format(len(concepts)))
    print('#entries (identifiers): {}'.format(nof_idf))
    print('#items (mathematical concepts): {}'.format(nof_concept))
    print('#entries with multiple items: {}'.format(nof_idf_mul))

    # analyse items
    items = sorted([(v['surface']['text'], idf_var, len(idf))
                    for idf_hex, v in concepts.items()
                    for idf_var, idf in v['identifiers'].items()],
                   key=lambda x: x[2],
                   reverse=True)
    logger.debug('items: %s', items)
    nof_items = np.array([i[2] for i in items])

    print('* Items information')
    print('max of #items: {}'.format(nof_items[0]))
    print('median of #items: {}'.format(int(np.median(nof_items))))
    print('mean of #items: {:.1f}'.format(np.mean(nof_items)))
    print('variance of #items: {:.1f}'.format(np.var(nof_items)))
    print('standard deviation of #items: {:.1f}'.format(np.std(nof_items)))

    # analyze occurences
    cnt_iter = itertools.count(0)

    concept_dict = dict()
    for idf_hex, v in concepts.items():
        concept_dict[idf_hex] = dict()
        for idf_var, idf in v['identifiers'].items():
            concept_dict[idf_hex][idf_var] = [next(cnt_iter) for _ in idf]
    logger.debug('concept_dict: %s', concept_dict)

    total = 0
    candidates = [0] * nof_items[0]
    occurences = []
    for mi_id, anno in data_anno['mi_anno'].items():
        mi = mi_info[mi_id]
        idf_hex, idf_var = mi['idf_hex'], mi['idf_var']

        concept_id = anno['concept_id']

        nof_candidates = len(concept_dict[idf_hex][idf_var])
        candidates[nof_candidates - 1] += 1
        total += nof_candidates
        concept_sid = concept_dict[idf_hex][idf_var][concept_id]
        occurences.append((concept_sid, mi['pos']))

    logger.debug('occurences: %s', occurences)
    logger.debug('candidates: %s', candidates)

    print('* occurences information')
    print('#occurences: {}'.format(len(occurences)))
    print('average #candidates: {:.1f}'.format(total / len(occurences)))

    return items, concept_dict, occurences


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
    out_dir = Path(args['--out'])
    out_dir.mkdir(parents=True, exist_ok=True)

    data_dir = Path(args['--data'])

    sources_dir = Path(args['--sources'])
    source_html = sources_dir / '{}.html'.format(paper_id)

    anno_json = data_dir / '{}_anno.json'.format(paper_id)
    mcdict_json = data_dir / '{}_mcdict.json'.format(paper_id)

    # load the data
    with open(anno_json) as f:
        data_anno = json.load(f)
    with open(mcdict_json) as f:
        data_mcdict = json.load(f)

    # check the version of data
    if data_anno.get('anno_version', '') != '0.2':
        logger.warning('Annotation data version is incompatible')

    if data_mcdict.get('mcdict_version', '') != '0.2':
        logger.warning('Mcdict version is incompatible')

    # load the source HTML and extract information
    tree = lxml.html.parse(str(source_html))
    mi_info, sec_info = extract_info(tree)

    tex_paper_id = paper_id.replace('.', '_')

    items, concept_dict, occurences = analyze_annotation(
        data_anno, data_mcdict, mi_info)

    # export items data
    items_tex = out_dir / '{}_items.tex'.format(tex_paper_id)
    with open(items_tex, 'w') as f:
        for i in items:
            f.write('(\\gf{{{}}}{{{}}}, {})\n'.format(i[0], i[1], i[2]))

    # plot items
    sns.set_style("whitegrid", {'axes.grid': False})
    plt.tick_params(labelbottom=False)
    plt.bar([i[0] for i in items], [i[2] for i in items])

    items_png = str(out_dir / '{}_items.png'.format(paper_id))
    plt.savefig(items_png)
    plt.clf()

    # export occurences data
    occurences_dat = out_dir / '{}_occurences.dat'.format(tex_paper_id)
    with open(occurences_dat, 'w') as f:
        for p in occurences:
            f.write('{}  {}\n'.format(p[0] + 0.5, p[1]))

    sections_tex = out_dir / '{}_sections.tex'.format(tex_paper_id)
    s0 = r'\addplot [domain=-2:106, dashed] {{{}}} ' \
         r'node [pos=0, left] {{\S{}}};'
    with open(sections_tex, 'w') as f:
        for sec, pos in sec_info.items():
            f.write(s0.format(pos, sec.replace('S', '')) + '\r')

    identifiers_tex = out_dir / '{}_identifiers.tex'.format(tex_paper_id)
    s1 = r'\addplot [black] coordinates {{({x}, -41900) ({x}, 420000)}};'
    with open(identifiers_tex, 'w') as f:
        x = 0
        for dc in concept_dict.values():
            for ls in dc.values():
                x += len(ls)
                f.write(s1.format(x=x) + '\n')

    # plot occurences
    plt.scatter([v[0] for v in occurences], [v[1] for v in occurences],
                s=2)
    plt.xlabel('Concepts')
    plt.ylabel('Position')

    occurences_png = str(out_dir / '{}_occurences.png'.format(paper_id))
    plt.savefig(occurences_png)
    plt.clf()


if __name__ == '__main__':
    main()
