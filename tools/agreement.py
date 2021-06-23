# Agreement calculation tool for MioGatto
import yaml
import json
import itertools
import lxml.html
import numpy as np
from docopt import docopt
from pathlib import Path
from sklearn.metrics import cohen_kappa_score

from lib.version import VERSION
from lib.cli import set_level
from lib.common import get_mi2idf

# use logger
import logging as log

log.Logger.set_level = set_level
logger = log.getLogger('agreement')

# dirty hack: suspend warning
np.seterr(divide='ignore', invalid='ignore')

# meta
PROG_NAME = "tools.agreement"
HELP = """Agreement calculation tool for MioGatto

Usage:
    {p} [options] ID

Options:
    -t DIR, --target=DIR  Dir for the reference data (Required)
    --reference=DIR    Dir for the reference data [default: ./data]
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


def calc_agreements(data_anno, data_anno_target, data_mcdict, mi_info):
    pos, neg, pt_miss, unannotated = 0, 0, 0, 0
    labels = dict()

    print('* Mismatches')
    print('ID\tReference Concept\tAnnotated Concept\tPattern Agreed')

    mi_anno, mi_anno_target = data_anno['mi_anno'], data_anno_target['mi_anno']

    for mi_id in mi_anno.keys():
        concept_id_gold = mi_anno[mi_id]['concept_id']
        concept_id_target = mi_anno_target[mi_id]['concept_id']

        if concept_id_target is None:
            unannotated += 1
            continue

        mi = mi_info[mi_id]
        idf_hex, idf_var = mi['idf_hex'], mi['idf_var']

        # for calculatin kappa
        idf_key = (idf_hex, idf_var)
        if idf_key not in labels.keys():
            labels[idf_key] = ([concept_id_gold], [concept_id_target])
        else:
            labels[idf_key][0].append(concept_id_gold)
            labels[idf_key][1].append(concept_id_target)

        # agreement
        if concept_id_target == concept_id_gold:
            pos += 1

        else:
            concept_list = data_mcdict[idf_hex]['identifiers'][idf_var]

            concept_gold = concept_list[concept_id_gold]
            concept_target = concept_list[concept_id_target]

            if concept_gold['args_type'] == concept_target['args_type']:
                pattern_agreed = True
            else:
                pt_miss += 1
                pattern_agreed = False

            print('{}\t{} ({})\t{} ({})\t{}'.format(
                mi_id, concept_id_gold, concept_gold['description'],
                concept_id_target, concept_target['description'],
                pattern_agreed))
            neg += 1

    total = pos + neg

    print('* Summary')
    print('Agreement: {}/{} = {:.2f}%'.format(pos, total, pos / total * 100))
    if neg > 0:
        rate = pt_miss / neg * 100
        print('Pattern mismatches: {}/{} = {:.2f}%'.format(pt_miss, neg, rate))

    print('* Kappas')
    kappas = []
    for k, v in labels.items():
        idf_hex, idf_var = k
        kappa = cohen_kappa_score(v[0], v[1])
        count = len(v[0])
        kappas.append((idf_hex, idf_var, kappa, count))

    w_sum, w_cnt = 0, 0
    print('symbol\tvariation\tKappa\tcount')
    for res in sorted(kappas, key=lambda x: x[3], reverse=True):
        print(bytes.fromhex(res[0]).decode(), res[1], res[2], res[3], sep='\t')
        if not np.isnan(res[2]):
            w_cnt += res[3]
            w_sum += res[2] * res[3]
    print('Kappa (weighted avg.): %.4f' % (w_sum / w_cnt))

    # warn if annotation is incompleted
    if unannotated > 0:
        logger.warning('Found %d unannotated occurence(s).', unannotated)


def analyze_annotation(data_anno, data_mcdict, mi_info):
    # basic analysis for mcdict
    nof_idf = 0
    nof_idf_mul = 0
    nof_concept = 0

    for letter in data_mcdict.values():
        nof_idf += len(letter['identifiers'])

        for idf in letter['identifiers'].values():
            if len(idf) > 1:
                nof_idf_mul += 1
            nof_concept += len(idf)

    print('* Basic information')
    print('#strings for identifiers: {}'.format(len(data_mcdict)))
    print('#entries (identifiers): {}'.format(nof_idf))
    print('#items (mathematical concepts): {}'.format(nof_concept))
    print('#entries with multiple items: {}'.format(nof_idf_mul))

    # analyse items
    items = sorted([(v['surface']['text'], idf_var, len(idf))
                    for idf_hex, v in data_mcdict.items()
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
    for idf_hex, v in data_mcdict.items():
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
    if type(args['--target']) is not str:
        logger.critical('Option --target (-t) is required')
        exit(1)
    target_dir = Path(args['--target'])
    target_anno_json = target_dir / '{}_anno.json'.format(paper_id)

    ref_dir = Path(args['--reference'])
    anno_json = ref_dir / '{}_anno.json'.format(paper_id)
    mcdict_yaml = ref_dir / '{}_mcdict.yaml'.format(paper_id)

    sources_dir = Path(args['--sources'])
    source_html = sources_dir / '{}.html'.format(paper_id)

    # load the target data
    with open(target_anno_json) as f:
        data_anno_target = json.load(f)

    # load the reference data
    with open(anno_json) as f:
        data_anno = json.load(f)
    with open(mcdict_yaml) as f:
        data_mcdict = yaml.load(f, Loader=yaml.FullLoader)

    # check the version of annotation data
    if data_anno.get('anno_version', '') != '0.2':
        logger.warning('Annotation data version is incompatible')

    # load the source HTML and extract information
    tree = lxml.html.parse(str(source_html))
    mi_info, sec_info = extract_info(tree)

    calc_agreements(data_anno, data_anno_target, data_mcdict, mi_info)


if __name__ == '__main__':
    main()
