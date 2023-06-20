# The server implementation for MioGatto
from flask import request, redirect, flash, render_template, Markup
from typing import Optional
from logging import Logger
from copy import deepcopy
from lxml import etree
import subprocess
import json
import re

from lib.version import VERSION
from lib.annotation import MiAnno, McDict
from lib.datatypes import MathConcept

# get git revision
try:
    GIT_REVISON = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip().decode('ascii')
except OSError:
    GIT_REVISON = 'Unknown'


def make_concept(res) -> Optional[MathConcept]:
    # check arity
    if not res.get('arity').isdigit():
        flash('Arity must be non-negative integer.')
        return None
    else:
        arity = int(res.get('arity'))

    # check description
    description = res.get('description')
    if len(description) == 0:
        flash('Description must be filled.')
        return None

    # get affixes
    affixes = []
    for i in range(10):
        t_i = res.get('affixes{}'.format(i))
        if t_i != '':
            affixes.append(t_i)

    return MathConcept(description, arity, affixes)


def affixes_pulldowns():
    select_tag = '''<li><select name="affixes{}">
<option value="">-----</option>
<option value="subscript">Subscript</option>
<option value="superscript">Superscript</option>
<option value="comma">Comma</option>
<option value="semicolon">Semicolon</option>
<option value="colon">Colon</option>
<option value="prime">Prime</option>
<option value="asterisk">Asterisk</option>
<option value="circle">Circle</option>
<option value="hat">Hat</option>
<option value="tilde">Tilde</option>
<option value="bar">Bar</option>
<option value="over">Over</option>
<option value="over right arrow">Over right arrow</option>
<option value="over left arrow">Over left arrow</option>
<option value="dot">Dot</option>
<option value="double dot">Double dot</option>
<option value="open parenthesis">Open parenthesis</option>
<option value="close parenthesis">Close parenthesis</option>
<option value="open bracket">Open bracket</option>
<option value="close bracket">Close bracket</option>
<option value="open brace">Open brace</option>
<option value="close brace">Close brace</option>
<option value="vertical bar">Vertical bar</option>
<option value="leftside argument">Leftside argument</option>
<option value="rightside argument">Rightside argument</option>
<option value="leftside base">Leftside base</option>
</select></li>'''
    items = '\n'.join([select_tag.format(i) for i in range(10)])

    return '<ol>{}</ol>'.format(items)


def preprocess_mcdict(concepts):
    # description processor
    def process_math(math):
        def construct_mi(idf_text, idf_var, concept_id):
            mi = '<mi data-math-concept="{}"'.format(concept_id)

            if idf_var == 'roman':
                mi += ' mathvariant="normal">'
            else:
                mi += '>'

            mi += idf_text + '</mi>'

            return mi

        # protect references (@x)
        math = re.sub(r'(@\d+)', r'<mi>\1</mi>', math)

        # expand \gf
        rls = [
            (construct_mi(m.group(1), m.group(2), int(m.group(3))), m.span())
            for m in re.finditer(r'\\gf{(.*?)}{(.*?)}{(\d*?)}', math)
        ]
        for r in reversed(rls):
            s, e = r[1]
            math = math[:s] + r[0] + math[e:]

        return '<math>' + math + '</math>'

    def process_desc(desc):
        if not desc or '$' not in desc:
            return desc

        # process maths
        it = desc.split('$')
        desc_new = ''.join([a + process_math(b) for a, b in zip(it[::2], it[1::2])])
        if len(it) % 2 != 0:
            desc_new += it[-1]

        return desc_new

    # initialize
    mcdict = dict()

    for idf_hex, idf in concepts.items():
        mcdict[idf_hex] = dict()
        for idf_var, cls in idf.items():
            mcdict[idf_hex][idf_var] = [
                {'description': process_desc(c.description), 'arity': c.arity, 'affixes': c.affixes} for c in cls
            ]

    return mcdict


class MioGattoServer:
    def __init__(self, paper_id: str, tree, mi_anno: MiAnno, mcdict: McDict, logger: Logger):
        self.paper_id = paper_id
        self.tree = tree
        self.mi_anno = mi_anno
        self.mcdict = mcdict
        self.logger = logger

    def index(self):
        # avoid destroying the original tree
        copied_tree = deepcopy(self.tree)
        root = copied_tree.getroot()

        # add data-math-concept for each mi element
        for mi in root.xpath('//mi'):
            mi_id = mi.get('id', None)
            if mi_id is None:
                continue

            concept_id = self.mi_anno.occr.get(mi_id, dict()).get('concept_id', None)
            if concept_id is None:
                continue

            mi.attrib['data-math-concept'] = str(concept_id)

        # progress info
        nof_anno = len(self.mi_anno.occr)
        nof_done = sum(1 for v in self.mi_anno.occr.values() if not v['concept_id'] is None)
        p_concept = '{}/{} ({:.2f}%)'.format(nof_done, nof_anno, nof_done / nof_anno * 100)

        nof_sog = 0
        for anno in self.mi_anno.occr.values():
            for sog in anno['sog']:
                nof_sog += 1

        # construction
        title = root.xpath('//head/title')[0].text
        body = root.xpath('body')[0]
        main_content = etree.tostring(body, method='html', encoding=str)

        return render_template(
            'index.html',
            title=title,
            version=VERSION,
            git_revision=GIT_REVISON,
            paper_id=self.paper_id,
            annotator=self.mi_anno.annotator,
            p_concept=p_concept,
            nof_sog=nof_sog,
            affixes=Markup(affixes_pulldowns()),
            main_content=Markup(main_content),
        )

    def assign_concept(self):
        res = request.form

        mi_id = res['mi_id']
        concept_id = int(res['concept'])

        if res.get('concept'):
            # register
            self.mi_anno.occr[mi_id]['concept_id'] = concept_id
            self.mi_anno.dump()

        return redirect('/')

    def remove_concept(self):
        res = request.form

        mi_id = res['mi_id']
        self.mi_anno.occr[mi_id]['concept_id'] = None
        self.mi_anno.dump()

        return redirect('/')

    def new_concept(self):
        res = request.form

        idf_hex = res.get('idf_hex')
        idf_var = res.get('idf_var')

        # make concept with checking
        concept = make_concept(res)
        if concept is None:
            return redirect('/')

        # register
        self.mcdict.concepts[idf_hex][idf_var].append(concept)
        self.mcdict.dump()

        return redirect('/')

    def update_concept(self):
        # register and save data_anno
        res = request.form

        idf_hex = res.get('idf_hex')
        idf_var = res.get('idf_var')
        concept_id = int(res.get('concept_id'))

        # make concept with checking
        concept = make_concept(res)
        if concept is None:
            return redirect('/')

        self.mcdict.concepts[idf_hex][idf_var][concept_id] = concept
        self.mcdict.dump()

        return redirect('/')

    def add_sog(self):
        res = request.form

        mi_id = res['mi_id']
        start_id, stop_id = res['start_id'], res['stop_id']

        # TODO: validate the span range
        existing_sog_pos = [(s['start'], s['stop']) for s in self.mi_anno.occr[mi_id]['sog']]
        if (start_id, stop_id) not in existing_sog_pos:
            self.mi_anno.occr[mi_id]['sog'].append({'start': start_id, 'stop': stop_id, 'type': 0})
            self.mi_anno.dump()

        return redirect('/')

    def delete_sog(self):
        res = request.form

        mi_id = res['mi_id']
        start_id, stop_id = res['start_id'], res['stop_id']

        delete_idx = None
        for idx, sog in enumerate(self.mi_anno.occr[mi_id]['sog']):
            if sog['start'] == start_id and sog['stop'] == stop_id:
                delete_idx = idx
                break

        if delete_idx is not None:
            del self.mi_anno.occr[mi_id]['sog'][delete_idx]
            self.mi_anno.dump()

        return redirect('/')

    def change_sog_type(self):
        res = request.form

        mi_id = res['mi_id']
        start_id, stop_id = res['start_id'], res['stop_id']
        sog_type = res['sog_type']

        for sog in self.mi_anno.occr[mi_id]['sog']:
            if sog['start'] == start_id and sog['stop'] == stop_id:
                sog['type'] = sog_type
                self.mi_anno.dump()
                break

        return redirect('/')

    def gen_mcdict_json(self):
        data = preprocess_mcdict(self.mcdict.concepts)

        return json.dumps(data, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))

    def gen_sog_json(self):
        data = {'sog': []}

        for mi_id, anno in self.mi_anno.occr.items():
            for sog in anno['sog']:
                data['sog'].append(
                    {'mi_id': mi_id, 'start_id': sog['start'], 'stop_id': sog['stop'], 'type': sog['type']}
                )

        return json.dumps(data, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
