# The preprocess tool for MioGatto
import lxml.html
import unicodedata
from docopt import docopt
from pathlib import Path

from lib.version import VERSION
from lib.logger import get_logger
from lib.util import get_mi2idf
from lib.annotation import dump_json

# meta
PROG_NAME = "tools.preprocess"
HELP = """Preprocess tool for MioGatto

Usage:
    {p} [options] HTML

Options:
    --embed-floats      Preserve embed figure/table codes
    --overwrite         Overwrite output files if already exist

    -d DIR, --data=DIR  Dir for data outputs [default: ./templates]
    --sources=DIR       Dir for HTML outputs [default: ./sources]

    -D, --debug         Show debug messages
    -q, --quiet         Show less messages

    -h, --help          Show this screen and exit
    -V, --version       Show version
""".format(
    p=PROG_NAME
)

logger = get_logger(PROG_NAME)


def hex2surface(idf_hex):
    idf_text = bytes.fromhex(idf_hex).decode()
    surface = {'text': idf_text}

    if len(idf_text) < 2:
        surface['unicode_name'] = unicodedata.name(idf_text)

    return surface


# add word span tags to text directly
def split_words_into_span_tags(text, parent_id, idx):
    from lxml.html.builder import SPAN

    def word_span(w, p, i, c):
        s = SPAN(w)
        s.attrib['class'] = 'gd_word'
        s.attrib['id'] = '{}.{}.w{}'.format(p, i + 1, c)
        return s

    words = text.split(' ')
    word_cnt, spans = 1, []

    for w in words[:-1]:
        spans.extend([word_span(w, parent_id, idx, word_cnt), SPAN(' ')])
        word_cnt += 1

    if not words[-1] == '':
        spans.append(word_span(words[-1], parent_id, idx, word_cnt))

    return spans


def embed_word_span_tags(e, parent_id):
    # get texts and remove
    texts = [e.text]
    e.text = None
    for c in e.getchildren():
        texts.append(c.tail)
        c.tail = None

    spans = [split_words_into_span_tags(t, parent_id, i) if t else None for i, t in enumerate(texts)]

    for i in range(len(spans) - 1, -1, -1):
        if not spans[i] is None:
            for s in reversed(spans[i]):
                e.insert(i, s)


def remove_embed_floats(root, paper_id):
    # remove embed float
    from lxml.html.builder import IMG

    for e in root.xpath('//figure[@class="ltx_figure"]'):
        # remove embed figures
        for c in e:
            if c.tag != 'img' and c.tag != 'figcaption':
                e.remove(c)

        # add <img>
        if [c.tag for c in e] == ['figcaption']:
            img = IMG()
            src = '/static/img/{}/{}.png'.format(paper_id, e.attrib['id'].replace('.', '_'))
            img.attrib['src'] = src
            img.attrib['alt'] = src
            e.insert(0, img)

    for e in root.xpath('//figure[@class="ltx_table"]'):
        # remove embed tables
        for c in e:
            if c.tag != 'figcaption':
                e.remove(c)

        # add <img>
        img = IMG()
        src = '/static/img/{}/{}.png'.format(paper_id, e.attrib['id'].replace('.', '_'))
        img.attrib['src'] = src
        img.attrib['alt'] = src
        e.insert(0, img)


def preprocess_html(tree, paper_id, embed_floats):
    root = tree.getroot()

    # drop unnecessary annotations
    for e in root.xpath('//annotation|//annotation-xml'):
        e.drop_tree()

    for e in root.xpath('//span[contains(@class,"ltx_text")]'):
        e.drop_tag()

    # tweak images
    for e in root.xpath('//img'):
        if 'ltx_graphics' in e.attrib.get('class', '').split(' '):
            src = '/static/img/{}/'.format(paper_id) + e.attrib['src']
            e.attrib['src'] = src
            e.attrib['alt'] = src
            e.attrib['width'] = None
            e.attrib['height'] = None

    # normal paragraphs
    for e in root.xpath('//p'):
        parent_id = e.attrib['id']
        embed_word_span_tags(e, parent_id)

    # captions
    for e in root.xpath('//figcaption'):
        parent_id = e.getparent().attrib['id']
        embed_word_span_tags(e, parent_id)

    # footnotes
    for e in root.xpath('//span[contains(@class,"ltx_note_content")]'):
        parent_id = e.getparent().getparent().attrib['id']
        embed_word_span_tags(e, parent_id)

    # paragraphs in inline blocks
    for e in root.xpath('//span[contains(@class,"ltx_inline-block")]//span[contains(@class, "ltx_p")]'):
        parent_id = e.attrib['id']
        embed_word_span_tags(e, parent_id)

    # almost done
    if not embed_floats:
        remove_embed_floats(root, paper_id)


def observe_mi(tree):
    # initialize
    identifiers = set()
    occurences = dict()
    mi_attribs = set()

    # the process
    mi2idf = get_mi2idf(tree)
    root = tree.getroot()

    for e in root.xpath('//mi'):
        # get mi_id and idf
        mi_id = e.attrib.get('id')
        idf = mi2idf.get(mi_id)

        if mi_id is None:
            # wired but to avoid errors
            continue

        if idf is not None:
            idf_hex = idf['idf_hex']
            idf_var = idf['idf_var']
        else:
            continue

        # check for the attrib
        mi_attribs.update(e.attrib)

        occurences[mi_id] = None

        identifiers.add((idf_hex, idf_var))

    return occurences, identifiers, mi_attribs


def idf2mc(idf_set):
    # initialize
    idf_dict = dict()

    # organize the identifiers
    for idf in idf_set:
        idf_hex, idf_var = idf
        if idf_hex not in idf_dict:
            idf_dict[idf_hex] = [idf_var]
        else:
            idf_dict[idf_hex].append(idf_var)

    idf_sorted = sorted(idf_dict.items(), key=lambda x: x[0])

    # construct a list of grounding functions
    return {idf[0]: {'_surface': hex2surface(idf[0]), 'identifiers': {v: [] for v in idf[1]}} for idf in idf_sorted}


def main():
    # parse options
    args = docopt(HELP, version=VERSION)

    logger.set_logger(args['--quiet'], args['--debug'])
    embed_floats = args['--embed-floats']

    # dirs and files
    data_dir = Path(args['--data'])
    sources_dir = Path(args['--sources'])

    html_in = Path(args['HTML'])
    paper_id = html_in.stem
    html_out = sources_dir / '{}.html'.format(paper_id)

    # now prepare for the preprocess
    logger.info('Begin to preprocess Paper "{}"'.format(paper_id))

    data_dir.mkdir(parents=True, exist_ok=True)
    anno_json = data_dir / '{}_anno.json'.format(paper_id)
    mcdict_json = data_dir / '{}_mcdict.json'.format(paper_id)

    # prevent unintentional overwriting
    if args['--overwrite'] is not True:
        if html_out.exists():
            logger.error('Source file %s exists. Use --overwrite to force', html_out)
            exit(1)

        if anno_json.exists() or mcdict_json.exists():
            logger.error('Data files exist in %s. Use --overwrite to force', data_dir)
            exit(1)

    # load the HTML and modify the DOM tree
    tree = lxml.html.parse(str(html_in))
    preprocess_html(tree, paper_id, embed_floats)

    # extract formulae information
    occurences, identifiers, attribs = observe_mi(tree)
    print('#indentifiers: {}'.format(len(identifiers)))
    print('#occurences: {}'.format(len(occurences)))
    print('mi attributes: {}'.format(', '.join(attribs)))

    # make the annotation structure
    mi_anno = {
        mi_id: {
            'concept_id': concept_id,
            'sog': [],
        }
        for mi_id, concept_id in occurences.items()
    }

    # write output files
    logger.info('Writing preprocessed HTML to %s', html_out)
    tree.write(str(html_out), pretty_print=True, encoding='utf-8')

    logger.info('Writing initialized anno template to %s', anno_json)
    with open(anno_json, 'w') as f:
        dump_json(
            {
                '_anno_version': '1.0',
                '_annotator': 'YOUR NAME',
                'mi_anno': mi_anno,
            },
            f,
        )

    logger.info('Writing initialized mcdict template to %s', mcdict_json)
    with open(mcdict_json, 'w') as f:
        dump_json(
            {
                '_author': 'YOUR NAME',
                '_mcdict_version': '1.0',
                'concepts': idf2mc(identifiers),
            },
            f,
        )


if __name__ == '__main__':
    main()
