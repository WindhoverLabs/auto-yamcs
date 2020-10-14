import sqlite3

import sqlite_utils
import argparse
import sys
import logging
import yaml


def parse_cli(args: list = sys.argv) -> argparse.Namespace:
    """
    Parses cli argyments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in path to sqlite database.')

    parser.add_argument('--yaml_path', type=str, required=True,
                        help=' The path to the yaml file')

    parser.add_argument('--sqlite_path', type=str, required=True,
                        help=' The path to the sqlite database.')

    return parser.parse_args()


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def mod_sql(sqlite_path: str, yaml_path: str):
    db = sqlite_utils.Database(sqlite_path)

    yaml_dict = read_yaml(yaml_path)

    for table in yaml_dict['tables']:
        for data in yaml_dict['tables'][table]:
            if table == 'symbols':
                elf_key = list(db['elfs'].rows_where("name =?", [data['elf']]))[0]['id']
                data['elf'] = elf_key
                db['symbols'].insert(data, ignore=True)

            elif table == 'fields':
                type_key = list(db['symbols'].rows_where("name =?", [data['type']]))[0]['id']
                symbol_key = list(db['symbols'].rows_where("name =?", [data['symbol']]))[0]['id']
                data['type'] = type_key
                data['symbol'] = symbol_key
                db['fields'].insert(data, ignore=True)

            elif table == 'telemetry':
                module_key = list(db['modules'].rows_where("name =?", [data['module']]))[0]['id']
                symbol_key = list(db['symbols'].rows_where("name =?", [data['symbol']]))[0]['id']
                data['module'] = module_key
                data['symbol'] = symbol_key
                db['telemetry'].insert(data, ignore=True)


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    args = parse_cli(sys.argv)

    mod_sql(args.sqlite_path, args.yaml_path)

    logging.info('DONE.')


if __name__ == '__main__':
    main()