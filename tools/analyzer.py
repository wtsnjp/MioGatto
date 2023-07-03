# The analyzer tool for MioGatto
import itertools
import lxml.html
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from docopt import docopt
from pathlib import Path

from lib.version import VERSION
from lib.logger import get_logger
from lib.util import get_mi2idf
from lib.annotation import MiAnno, McDict

# meta
PROG_NAME = "tools.analyzer"
HELP = """Analysing tool for MioGatto

Usage:
    {p} [options] ID

Options:
    -o DIR, --out=DIR   Dir to save results
    -d DIR, --data=DIR  Dir for the gold data [default: ./data]
    --sources=DIR       Dir for preprocessed HTML [default: ./sources]

    -D, --debug         Show debug messages
    -q, --quiet         Show less messages

    -h, --help          Show this screen and exit
    -V, --version       Show version
""".format(
    p=PROG_NAME
)

logger = get_logger(PROG_NAME)


def extract_info(tree, mi2idf):
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
        pos = html_str.find(lxml.html.tostring(e, encoding='utf-8').decode('utf-8'))
        mi_info[mi_id]['pos'] = pos

    # extract section info
    sec_info = dict()
    for e in root.xpath('//section'):
        sec_id = e.attrib.get('id')
        pos = html_str.find(lxml.html.tostring(e, encoding='utf-8').decode('utf-8'))
        sec_info[sec_id] = pos

    logger.debug('{sec_info=}')

    return mi_info, sec_info


def analyze_annotation(paper_id, tree, mi_anno, mcdict, mi_info, mi2idf):
    concepts = mcdict.concepts

    # basic analysis for mcdict
    nof_idf = 0
    nof_idf_mul = 0
    nof_concept = 0

    for letter in concepts.values():
        nof_idf += len(letter)

        for idf in letter.values():
            if len(idf) > 1:
                nof_idf_mul += 1
            nof_concept += len(idf)

    root = tree.getroot()
    nof_words = len(root.xpath('//span[@class = "gd_word"]'))

    print('* Basic information')
    print('Paper ID: {}'.format(paper_id))
    print('#words: {}'.format(nof_words))
    print('Author of math concept dict: {}'.format(mcdict.author))
    print('Annotator: {}'.format(mi_anno.annotator))
    print('#types of identifiers: {}'.format(len(concepts)))
    print('#occurences: {}'.format(len(mi_anno.occr)))
    print()

    # analyse items
    items = sorted(
        [
            (mcdict.surfaces[idf_hex]['text'], idf_var, len(idf))
            for idf_hex, v in concepts.items()
            for idf_var, idf in v.items()
        ],
        key=lambda x: x[2],
        reverse=True,
    )
    logger.debug(f'{items=}')
    nof_items = np.array([i[2] for i in items])

    print('* Math concept dictionary')
    print('#entries (identifiers): {}'.format(nof_idf))
    print('#items (math concepts): {}'.format(nof_concept))
    print('#entries with multiple items: {}'.format(nof_idf_mul))
    print()

    print('* Number of items in each entry')
    print('Max: {}'.format(nof_items[0]))
    print('Median: {}'.format(int(np.median(nof_items))))
    print('Mean: {:.1f}'.format(np.mean(nof_items)))
    print('Variance: {:.1f}'.format(np.var(nof_items)))
    print('Standard deviation: {:.1f}'.format(np.std(nof_items)))
    print()

    # analyze occurences
    cnt_iter = itertools.count(0)

    concept_dict = dict()
    for idf_hex, v in concepts.items():
        concept_dict[idf_hex] = dict()
        for idf_var, idf in v.items():
            concept_dict[idf_hex][idf_var] = [
                {'sid': next(cnt_iter), 'count': 0} for _ in idf  # unique ID, number of occurences
            ]

    nof_annotated, total_nof_candidates, nof_sog = 0, 0, 0
    candidates = [0] * nof_items[0]
    occurences = []
    for mi_id, anno in mi_anno.occr.items():
        mi = mi_info.get(mi_id, None)
        if mi is None:
            continue
        idf_hex, idf_var = mi['idf_hex'], mi['idf_var']

        nof_sog += len(anno.get('sog', []))

        nof_candidates = len(concept_dict[idf_hex][idf_var])
        candidates[nof_candidates - 1] += 1
        total_nof_candidates += nof_candidates

        concept_id = anno.get('concept_id')
        if concept_id is not None:
            nof_annotated += 1

            concept_sid = concept_dict[idf_hex][idf_var][concept_id]['sid']
            concept_dict[idf_hex][idf_var][concept_id]['count'] += 1
            occurences.append((concept_sid, mi['pos']))

    print('* Annotation')
    nof_occurences = len(mi_anno.occr)
    progress_rate = nof_annotated / nof_occurences * 100
    print('Progress rate: {:.2f}% ({}/{})'.format(progress_rate, nof_annotated, nof_occurences))
    print('Average #candidates: {:.1f}'.format(total_nof_candidates / nof_occurences))
    print('#SoG: {}'.format(nof_sog))
    print()

    print('* Number of occurences by concept')
    counts, count_zeros = [], []
    for idf_hex, v in concept_dict.items():
        for idf_var, cls in v.items():
            for cid, c in enumerate(cls):
                cnt = c['count']
                if cnt == 0:
                    # do not consider if no occurence is associated
                    # this will be warned afterwards
                    count_zeros.append((idf_hex, idf_var, cid))
                else:
                    counts.append(cnt)

    print('Max: {}'.format(max(counts)))
    print('Median: {}'.format(int(np.median(counts))))
    print('Mean: {:.1f}'.format(np.mean(counts)))
    print('Variance: {:.1f}'.format(np.var(counts)))
    print('Standard deviation: {:.1f}'.format(np.std(counts)))
    print()

    # warnings
    if len(count_zeros) > 0:
        logger.warning('Nothing is associated with the following concepts:')
        for tp in count_zeros:
            idf_hex, idf_var, cid = tp
            surface = mcdict.surfaces[idf_hex]['text']
            desc = concepts[idf_hex][idf_var][cid].description
            logger.warning('    %s > %s > %d (%s)', surface, idf_var, cid, desc)

    # output for debugging
    logger.debug(f'{concept_dict=}')
    logger.debug(f'{occurences=}')
    logger.debug(f'{candidates=}')

    return items, concept_dict, occurences


def export_graphs(paper_id, items, concept_dict, occurences, sec_info, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    tex_paper_id = paper_id.replace('.', '_')

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
    s0 = r'\addplot [domain=-2:106, dashed] {{{}}} ' r'node [pos=0, left] {{\S{}}};'
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
    plt.scatter([v[0] for v in occurences], [v[1] for v in occurences], s=2)
    plt.xlabel('Concepts')
    plt.ylabel('Position')

    occurences_png = str(out_dir / '{}_occurences.png'.format(paper_id))
    plt.savefig(occurences_png)
    plt.clf()


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

    # load the source HTML and extract information
    tree = lxml.html.parse(str(source_html))
    mi2idf = get_mi2idf(tree)
    mi_info, sec_info = extract_info(tree, mi2idf)

    items, concept_dict, occurences = analyze_annotation(paper_id, tree, mi_anno, mcdict, mi_info, mi2idf)

    # supplementary graphs
    if args['--out'] is not None:
        out_dir = Path(args['--out'])
        export_graphs(paper_id, items, concept_dict, occurences, sec_info, out_dir)


if __name__ == '__main__':
    main()
