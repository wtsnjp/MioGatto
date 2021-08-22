# Agreement calculation tool for MioGatto
import lxml.html
import numpy as np
from docopt import docopt
from pathlib import Path
from sklearn.metrics import cohen_kappa_score

from lib.version import VERSION
from lib.cli import set_level
from lib.common import get_mi2idf, load_anno_json, load_mcdict_json

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
    -r DIR, --reference=DIR
                    Dir for the reference data [default: ./data]
    --sources=DIR   Dir for preprocessed HTML [default: ./sources]

    -s, --show-mismatch  Show mismatch details
    -d, --debug     Show debug messages
    -q, --quiet     Show less messages

    -h, --help      Show this screen and exit
    -V, --version   Show version
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

    return mi_info


def calc_agreements(ref_mi_anno, target_mi_anno, ref_concepts, mi_info,
                    show_mismatch):
    pos, neg, pt_miss, unannotated = 0, 0, 0, 0
    labels = dict()

    if show_mismatch:
        print('* Mismatches')
        print('ID\tReference Concept\tAnnotated Concept\tPattern Agreed')

    for mi_id in ref_mi_anno.keys():
        concept_id_gold = ref_mi_anno[mi_id]['concept_id']
        concept_id_target = target_mi_anno[mi_id]['concept_id']

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
            concept_list = ref_concepts[idf_hex]['identifiers'][idf_var]

            concept_gold = concept_list[concept_id_gold]
            concept_target = concept_list[concept_id_target]

            if concept_gold['args_type'] == concept_target['args_type']:
                pattern_agreed = True
            else:
                pt_miss += 1
                pattern_agreed = False

            if show_mismatch:
                print('{}\t{} ({})\t{} ({})\t{}'.format(
                    mi_id, concept_id_gold, concept_gold['description'],
                    concept_id_target, concept_target['description'],
                    pattern_agreed))
            neg += 1

    # warn if annotation is incompleted
    if unannotated > 0:
        logger.warning('Found %d unannotated occurence(s).', unannotated)

    return pos, neg, pt_miss, labels


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
    show_mismatch = args['--show-mismatch']

    # dirs and files
    if type(args['--target']) is not str:
        logger.critical('Option --target (-t) is required')
        exit(1)
    target_dir = Path(args['--target'])
    target_anno_json = target_dir / '{}_anno.json'.format(paper_id)
    target_mcdict_json = target_dir / '{}_mcdict.json'.format(paper_id)

    ref_dir = Path(args['--reference'])
    ref_anno_json = ref_dir / '{}_anno.json'.format(paper_id)
    ref_mcdict_json = ref_dir / '{}_mcdict.json'.format(paper_id)

    sources_dir = Path(args['--sources'])
    source_html = sources_dir / '{}.html'.format(paper_id)

    # load the target data
    target_mi_anno, target_annotator = load_anno_json(target_anno_json, logger)
    _, target_mcdict_author = load_mcdict_json(target_mcdict_json, logger)

    # load the reference data
    ref_mi_anno, ref_annotator = load_anno_json(ref_anno_json, logger)
    ref_concepts, ref_mcdict_author = load_mcdict_json(ref_mcdict_json, logger)

    # load the source HTML and extract information
    tree = lxml.html.parse(str(source_html))
    mi_info = extract_info(tree)

    pos, neg, pt_miss, labels = calc_agreements(ref_mi_anno, target_mi_anno,
                                                ref_concepts, mi_info,
                                                show_mismatch)

    # show results
    total = pos + neg
    print('* Summary')
    print('Reference data: Annotation by {}, Math concept dict by {}'.format(
        ref_annotator, ref_mcdict_author))
    print('Target data: Annotation by {}, Math concept dict by {}'.format(
        target_annotator, target_mcdict_author))
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
        print(bytes.fromhex(res[0]).decode(),
              res[1],
              '{:.3f}'.format(res[2]),
              res[3],
              sep='\t')
        if not np.isnan(res[2]):
            w_cnt += res[3]
            w_sum += res[2] * res[3]
    print('Kappa (weighted avg.): %.3f' % (w_sum / w_cnt))


if __name__ == '__main__':
    main()
