# The preprocess tool for MioGatto
import lxml.html
import urllib.request
from docopt import docopt
from pathlib import Path

from lib.version import VERSION
from lib.logger import get_logger

# meta
PROG_NAME = "tools.fetch_html"
HELP = """Fetch html file from ar5iv

Usage:
    {p} [options] ARXIVID

Options:
    --overwrite         Overwrite output files if already exist

    --arxmliv-dir=DIR   Dir to save fetched html [default: ./arxmliv]

    -D, --debug         Show debug messages
    -q, --quiet         Show less messages

    -h, --help          Show this screen and exit
    -V, --version       Show version
""".format(
    p=PROG_NAME
)

logger = get_logger(PROG_NAME)


def get_paper_id(arxiv_id: str) -> str:
    # Simply remove the slash '/'.
    return arxiv_id.replace('/', '')


def get_html_tree(arxiv_id: str):
    url: str = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"

    # To get formatted output html.
    parser = lxml.html.HTMLParser(remove_blank_text=True)

    with urllib.request.urlopen(url) as f:
        tree = lxml.html.parse(f, parser=parser)

    return tree


def has_error(tree) -> bool:
    root: lxml.html.HtmlElement = tree.getroot()

    oks = root.xpath('//a[contains(@class, "ar5iv-severity-ok")]')
    fatals = root.xpath('//a[contains(@class, "ar5iv-severity-fatal")]')

    # Ad hoc.
    if len(oks) == 1 and len(fatals) == 0:
        # No error.
        return False
    elif len(oks) == 0 and len(fatals) == 1:
        # There should have been an error in LaTeXML process.
        return True
    else:
        # Something not expected, e.g., specification change, occurred.
        logger.error("Something unexpected has occurred.")
        exit(1)


def clean_and_save(tree, output_file: Path):
    root: lxml.html.HtmlElement = tree.getroot()

    # Remove scripts.
    for e in root.xpath('//script'):
        e.drop_tree()

    # Remove ar5iv related elements.
    for e in root.xpath('//*[contains(@class, "ar5iv")]'):
        e.drop_tree()

    # Remove OGP info.
    for e in root.xpath('/html/head/meta[contains(@name, "twitter") or contains(@property, "og")]'):
        # e.drop_tag()
        e.drop_tree()

    # Remove link to css.
    for e in root.xpath('/html/head/link'):
        e.drop_tree()

    logger.info(f"Saving the fetched html: {str(output_file)}")
    tree.write(str(output_file), pretty_print=True, encoding='utf-8')


def main():
    # Parse options.
    args = docopt(HELP, version=VERSION)

    logger.set_logger(args['--quiet'], args['--debug'])

    arxiv_id: str = args['ARXIVID']
    # paper_id may not be equal to arxiv_id since the latter may contain '/', which is not problematic for filenames.
    paper_id: str = get_paper_id(arxiv_id=arxiv_id)

    arxmliv_dir: Path = Path(args['--arxmliv-dir'])
    output_file: Path = arxmliv_dir.joinpath(f'{paper_id}.html')

    # Prevent unintentional overwriting.
    if args['--overwrite'] is not True:
        if output_file.exists():
            logger.error(f"Source file {str(output_file)} exists. Use --overwrite to force")
            exit(1)

    doc_tree = get_html_tree(arxiv_id=arxiv_id)

    if has_error(tree=doc_tree):
        # Exit if there is an error detedted in the fetched html.
        logger.error(f'Fetch failed; Error should have occurred during applying LaTeXML to {arxiv_id}')
        exit(1)
    else:
        # Save the fetched html.
        clean_and_save(tree=doc_tree, output_file=output_file)


if __name__ == '__main__':
    main()
