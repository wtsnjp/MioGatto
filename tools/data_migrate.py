# The data migration tool for MioGatto
import sys
import yaml
import json


def main():
    input_file = sys.argv[1]

    if input_file[-4:] != 'yaml':
        print('Input must be yaml file')
        exit(1)

    output_file = input_file[:-4] + 'json'

    with open(input_file) as f:
        org_mcdict = yaml.load(f, Loader=yaml.FullLoader)

    new_mcdict = {
        'mcdict_version': '0.2',
        'annotator': 'NAME',
        'concepts': org_mcdict
    }

    # write the new generated data
    with open(output_file, 'w') as f:
        json.dump(new_mcdict,
                  f,
                  ensure_ascii=False,
                  indent=4,
                  sort_keys=True,
                  separators=(',', ': '))


if __name__ == '__main__':
    main()
