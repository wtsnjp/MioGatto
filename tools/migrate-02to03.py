import sys
import json


def main():
    fn = sys.argv[1]

    with open(fn, encoding='utf-8') as f:
        data = json.load(f)

    if data.get('anno_version') != '0.2':
        print('Anno version is not 0.2')
        exit(1)

    data['anno_version'] = '0.3'
    for mi in data['mi_anno'].values():
        old_sog_ls = mi['sog']
        new_sog_ls = []

        for tp in old_sog_ls:
            new_sog_ls.append({'start': tp[0], 'stop': tp[1], 'type': 0})

        mi['sog'] = new_sog_ls

    json.dump(data,
              sys.stdout,
              ensure_ascii=False,
              indent=4,
              sort_keys=True,
              separators=(',', ': '))
    print()


if __name__ == '__main__':
    main()
