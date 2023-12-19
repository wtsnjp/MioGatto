# The Flask application
from flask import Flask
import os
import lxml.html
from docopt import docopt
from pathlib import Path

from lib.version import VERSION
from lib.annotation import MiAnno, McDict
from server.miogatto import MioGattoServer

# meta
PROG_NAME = "server"
HELP = """The server implementation for MioGatto

Usage:
    {p} [options] ID

Options:
    -d DIR, --data=DIR
        Dir for the gold data [default: ./data]
    -s DIR, --sources=DIR
        Dir for preprocessed HTML [default: ./sources]

    -D, --debug         Run in the debug mode
    -p, --port=NUM      Port number [default: 4100]
    --host=HOST         Host name [default: localhost]

    -h, --help          Show this screen and exit
    -V, --version       Show version
""".format(
    p=PROG_NAME
)


# the web app
app = Flask(__name__)
app.secret_key = os.urandom(12)


def routing_functions(server):
    @app.route('/', methods=['GET'])
    def index():
        return server.index()

    @app.route('/_concept', methods=['POST'])
    def action_concept():
        return server.assign_concept()

    @app.route('/_remove_concept', methods=['POST'])
    def action_remove_concept():
        return server.remove_concept()

    @app.route('/_new_concept', methods=['POST'])
    def action_new_concept():
        return server.new_concept()

    @app.route('/_update_concept', methods=['POST'])
    def action_update_concept():
        return server.update_concept()

    @app.route('/_update_concept_for_edit_mcdict', methods=['POST'])
    def action_update_concept_for_edit_mcdict():
        return server.update_concept_for_edit_mcdict()

    @app.route('/_add_sog', methods=['POST'])
    def action_add_sog():
        return server.add_sog()

    @app.route('/_delete_sog', methods=['POST'])
    def action_delete_sog():
        return server.delete_sog()

    @app.route('/_change_sog_type', methods=['POST'])
    def action_change_sog_type():
        return server.change_sog_type()

    @app.route('/mcdict.json', methods=['GET'])
    def mcdict_json():
        return server.gen_mcdict_json()

    @app.route('/sog.json', methods=['GET'])
    def sog_json():
        return server.gen_sog_json()

    @app.route('/edit_mcdict', methods=['GET'])
    def edit_mcdict():
        return server.edit_mcdict()


def main():
    # parse options
    args = docopt(HELP, version=VERSION)

    paper_id = args['ID']

    # dir and files
    data_dir = Path(args['--data'])
    sources_dir = Path(args['--sources'])

    anno_json = data_dir / '{}_anno.json'.format(paper_id)
    mcdict_json = data_dir / '{}_mcdict.json'.format(paper_id)
    source_html = sources_dir / '{}.html'.format(paper_id)

    # load the data
    mi_anno = MiAnno(anno_json, app.logger)
    mcdict = McDict(mcdict_json, app.logger)
    tree = lxml.html.parse(str(source_html))

    # run the app
    app.debug = args['--debug']

    server = MioGattoServer(paper_id, tree, mi_anno, mcdict, app.logger)
    routing_functions(server)

    app.run(host=args['--host'], port=args['--port'])


if __name__ == '__main__':
    main()
