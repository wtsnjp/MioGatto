# Usage: python -m tools.migrate_data_02to10 <original_data_dir> <new_data_dir>
import sys
import json
from pathlib import Path


def write_json(fp, content):
    with open(fp, mode='w') as f:
        json.dump(content, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))


def process_anno(original_file, new_data_dir):
    with open(original_file, encoding='utf-8') as f:
        data = json.load(f)

    if data.get('anno_version') != '0.2':
        print(f'Anno version of "{original_file}" is not 0.2, skipping', file=sys.stderr)
        return

    # metadata
    annotator = data['annotator']
    del data['anno_version']
    del data['annotator']
    data['_anno_version'] = '1.0'
    data['_annotator'] = annotator

    # data update
    for mi in data['mi_anno'].values():
        old_sog_ls = mi['sog']
        new_sog_ls = []

        for tp in old_sog_ls:
            new_sog_ls.append({'start': tp[0], 'stop': tp[1], 'type': 0})

        mi['sog'] = new_sog_ls

    # write data
    filename = original_file.name
    write_json(new_data_dir / filename, data)


def process_mcdict(original_file, new_data_dir):
    with open(original_file, encoding='utf-8') as f:
        data = json.load(f)

    if data.get('mcdict_version') != '0.2':
        print(f'Anno version of "{original_file}" is not 0.2, skipping', file=sys.stderr)
        return

    # metadata
    author = data['annotator']
    del data['mcdict_version']
    del data['annotator']
    data['_mcdict_version'] = '1.0'
    data['_author'] = author

    # data update
    for obj in data['concepts'].values():
        surface = obj['surface']
        del obj['surface']
        obj['_surface'] = surface

        for concept_ls in obj['identifiers'].values():
            for concept in concept_ls:
                affixes = concept['args_type']
                del concept['args_type']
                concept['affixes'] = affixes

    # write data
    filename = original_file.name
    write_json(new_data_dir / filename, data)


def main():
    if len(sys.argv) < 3:
        print('Not enough arguments are given', file=sys.stderr)
        exit(1)

    original_data_dir = Path(sys.argv[1])
    new_data_dir = Path(sys.argv[2])

    # dir varidations
    if not original_data_dir.is_dir():
        print(f'{original_data_dir} is not an existing dir', file=sys.stderr)
        exit(1)

    if new_data_dir.exists():
        print(f'{new_data_dir} already exists', file=sys.stderr)
        exit(1)

    new_data_dir.mkdir(parents=True)

    # process all data files
    for anno_file in original_data_dir.glob('*_anno.json'):
        process_anno(anno_file, new_data_dir)

    for mcdict_file in original_data_dir.glob('*_mcdict.json'):
        process_mcdict(mcdict_file, new_data_dir)


if __name__ == '__main__':
    main()
