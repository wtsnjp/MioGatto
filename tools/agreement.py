# Agreement calculation tool for MioGatto
import lxml.html
import numpy as np
from docopt import docopt
from pathlib import Path
from sklearn.metrics import cohen_kappa_score

from lib.version import VERSION
from lib.logger import get_logger
from lib.util import get_mi2idf
from lib.annotation import MiAnno, McDict

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
    -D, --debug     Show debug messages
    -q, --quiet     Show less messages

    -h, --help      Show this screen and exit
    -V, --version   Show version
""".format(
    p=PROG_NAME
)

logger = get_logger(PROG_NAME)

# dirty hack: suspend warning
np.seterr(divide='ignore', invalid='ignore')


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
        pos = html_str.find(lxml.html.tostring(e, encoding='utf-8').decode('utf-8'))
        mi_info[mi_id]['pos'] = pos

    # make word list
    wl = [e.attrib.get('id') for e in root.xpath('//span[@class="gd_word"]')]

    return mi_info, wl


def calc_agreements(ref_mi_anno, target_mi_anno, ref_mcdict, mi_info, show_mismatch):
    pos, neg, pt_miss, unannotated = 0, 0, 0, 0
    labels = dict()

    if show_mismatch:
        print('* Mismatches')
        print('ID\tReference Concept\tAnnotated Concept\tPattern Agreed')

    for mi_id in ref_mi_anno.occr.keys():
        concept_id_gold = ref_mi_anno.occr[mi_id]['concept_id']
        concept_id_target = target_mi_anno.occr[mi_id]['concept_id']

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
            concept_list = ref_mcdict.concepts[idf_hex][idf_var]

            concept_gold = concept_list[concept_id_gold]
            concept_target = concept_list[concept_id_target]

            if concept_gold.affixes == concept_target.affixes:
                pattern_agreed = True
            else:
                pt_miss += 1
                pattern_agreed = False

            if show_mismatch:
                print(
                    '{}\t{} ({})\t{} ({})\t{}'.format(
                        mi_id,
                        concept_id_gold,
                        concept_gold.description,
                        concept_id_target,
                        concept_target.description,
                        pattern_agreed,
                    )
                )
            neg += 1

    # warn if annotation is incompleted
    if unannotated > 0:
        logger.warning('Found %d unannotated occurence(s).', unannotated)

    return pos, neg, pt_miss, labels


def sog_match(ref_mi_anno, target_mi_anno, word_list):
    ref_sogs = [
        ((word_list.index(sog[0]), word_list.index(sog[1])), anno['concept_id'])
        for anno in ref_mi_anno.occr.values()
        for sog in anno['sog']
    ]
    target_sogs = [
        ((word_list.index(sog[0]), word_list.index(sog[1])), anno['concept_id'])
        for anno in target_mi_anno.occr.values()
        for sog in anno['sog']
    ]

    pos_sog_match = 0
    neg_sog_match = 0

    for ref_sog_tp in ref_sogs:
        ref_s, ref_e = ref_sog_tp[0]
        ref_concept = ref_sog_tp[1]

        for target_sog_tp in target_sogs:
            target_s, target_e = target_sog_tp[0]
            target_concept = target_sog_tp[1]

            if not (ref_e < target_s and ref_s < target_e) and not (ref_e > target_s and ref_s > target_e):
                if ref_concept == target_concept:
                    pos_sog_match += 1
                else:
                    neg_sog_match += 1

    return len(ref_sogs), len(target_sogs), pos_sog_match, neg_sog_match


def main():
    # parse options
    args = docopt(HELP, version=VERSION)

    logger.set_logger(args['--quiet'], args['--debug'])
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
    target_mi_anno = MiAnno(target_anno_json, logger)
    target_mcdict = McDict(target_mcdict_json, logger)

    # load the reference data
    ref_mi_anno = MiAnno(ref_anno_json, logger)
    ref_mcdict = McDict(ref_mcdict_json, logger)

    # load the source HTML and extract information
    tree = lxml.html.parse(str(source_html))
    mi_info, word_list = extract_info(tree)

    pos, neg, pt_miss, labels = calc_agreements(ref_mi_anno, target_mi_anno, ref_mcdict, mi_info, show_mismatch)

    nof_ref_sogs, nof_target_sogs, pos_sog_match, neg_sog_match = sog_match(ref_mi_anno, target_mi_anno, word_list)

    # show results
    total = pos + neg
    print('* Summary')
    print('Reference data: Annotation by {}, Math concept dict by {}'.format(ref_mi_anno.annotator, ref_mcdict.author))
    print(
        'Target data: Annotation by {}, Math concept dict by {}'.format(target_mi_anno.annotator, target_mcdict.author)
    )
    print('Agreement: {}/{} = {:.2f}%'.format(pos, total, pos / total * 100))
    if neg > 0:
        rate = pt_miss / neg * 100
        print('Pattern mismatches: {}/{} = {:.2f}%'.format(pt_miss, neg, rate))

    print('* Source of grounding')
    print('#ref_sogs: {}'.format(nof_ref_sogs))
    print('#target_sogs: {}'.format(nof_target_sogs))
    print('#pos_sog_match: {}'.format(pos_sog_match))
    print('#neg_sog_match: {}'.format(neg_sog_match))

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
        print(bytes.fromhex(res[0]).decode(), res[1], '{:.3f}'.format(res[2]), res[3], sep='\t')
        if not np.isnan(res[2]):
            w_cnt += res[3]
            w_sum += res[2] * res[3]
    print('Kappa (weighted avg.): %.3f' % (w_sum / w_cnt))


if __name__ == '__main__':
    main()
