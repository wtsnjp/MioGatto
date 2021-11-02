# Annotation data handler
import json
from pathlib import Path
from logging import Logger
from dataclasses import asdict

from lib.datatypes import MathConcept


def dump_json(data, fp):
    json.dump(data,
              fp,
              ensure_ascii=False,
              indent=4,
              sort_keys=True,
              separators=(',', ': '))
    fp.write('\n')


class MiAnno:
    """Math identifier annotation"""

    def __init__(self, file: Path, logger: Logger) -> None:
        with open(file, encoding='utf-8') as f:
            data = json.load(f)

        if data.get('anno_version', '') != '0.2':
            logger.warning('%s: Annotation data version is incompatible', file)

        self.file = file
        self.anno_version: str = data.get('anno_version', 'unknown')
        self.annotator: str = data.get('annotator', 'unknown')
        self.occr: dict = data['mi_anno']

    def dump(self) -> None:
        with open(self.file, 'w') as f:
            dump_json(
                {
                    'anno_version': self.anno_version,
                    'annotator': self.annotator,
                    'mi_anno': self.occr,
                }, f)


class McDict:
    """Math concept dictionariy"""

    def __init__(self, file: Path, logger: Logger) -> None:
        with open(file, encoding='utf-8') as f:
            data = json.load(f)

        if data.get('mcdict_version', '') != '0.2':
            logger.warning('%s: Math concept dict version is incompatible',
                           file)

        self.file = file
        self.mcdict_version: str = data.get('mcdict_version', 'unknown')
        self.author: str = data.get('annotator', 'unknown')

        concepts, surfaces = dict(), dict()
        for idf_hex, obj in data['concepts'].items():
            concepts[idf_hex] = dict()
            surfaces[idf_hex] = obj['surface']

            for idf_var, cls in obj['identifiers'].items():
                concepts[idf_hex][idf_var] = [MathConcept(**c) for c in cls]

        self.concepts = concepts
        self.surfaces = surfaces

    def dump(self):
        concepts = dict()
        for idf_hex, s in self.surfaces.items():
            concepts['concepts'][idf_hex] = {
                'surface': s,
                'identifiers': dict(),
            }

            for idf_var, cls in self.concepts[idf_hex].items():
                concepts['concepts'][idf_hex]['identifiers'][idf_var] = [
                    asdict(c) for c in cls
                ]

        with open(self.file, 'w') as f:
            dump_json({
                'annotator': self.author,
                'mcdict_version': self.mcdict_version,
                'concepts': concepts,
            }, f)
