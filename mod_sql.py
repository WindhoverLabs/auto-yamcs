import sqlite3

import sqlite_utils
import argparse
import sys
import logging
import yaml


def parse_cli() -> argparse.Namespace:
    """
    Parses cli arguments.
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


def write_dict_to_database(data_dict: dict, db_handle: sqlite_utils.Database):
    """
    Writes data_dict to database following the schema specified on [1].
    :return:
    [1]:https://github.com/WindhoverLabs/juicer/tree/develop
    """
    for table in data_dict:
        for data in data_dict[table]:
            if table == 'symbols':
                elf_key = list(db_handle['elfs'].rows_where("name =?", [data['elf']]))[0]['id']
                data['elf'] = elf_key
                db_handle['symbols'].insert(data, ignore=True)

            elif table == 'fields':
                type_key = list(db_handle['symbols'].rows_where("name =?", [data['type']]))[0]['id']
                symbol_key = list(db_handle['symbols'].rows_where("name =?", [data['symbol']]))[0]['id']
                data['type'] = type_key
                data['symbol'] = symbol_key
                db_handle['fields'].insert(data, ignore=True)

            elif table == 'telemetry':
                module_key = list(db_handle['modules'].rows_where("name =?", [data['module']]))[0]['id']
                symbol_key = list(db_handle['symbols'].rows_where("name =?", [data['symbol']]))[0]['id']
                data['module'] = module_key
                data['symbol'] = symbol_key
                db_handle['telemetry'].insert(data, ignore=True)

            elif table == 'commands':
                module_key = list(db_handle['modules'].rows_where("name =?", [data['module']]))[0]['id']
                symbol_key = list(db_handle['symbols'].rows_where("name =?", [data['symbol']]))[0]['id']
                data['module'] = module_key
                data['symbol'] = symbol_key
                db_handle['commands'].insert(data, ignore=True)

            elif table == 'elfs':
                db_handle['elfs'].insert(data, ignore=True)

            elif table == 'enumerations':
                symbol_key = list(db_handle['symbols'].rows_where("name =?", [data['symbol']]))[0]['id']
                data['symbol'] = symbol_key
                db_handle['enumerations'].insert(data, ignore=True)

            elif table == 'events':
                module_key = list(db_handle['modules'].rows_where("name =?", [data['symbol']]))[0]['id']
                data['module'] = module_key
                db_handle['events'].insert(data, ignore=True)

            elif table == 'configurations':
                module_key = list(db_handle['modules'].rows_where("name =?", [data['symbol']]))[0]['id']
                data['module'] = module_key
                db_handle['configurations'].insert(data, ignore=True)

            elif table == 'performance_ids':
                module_key = list(db_handle['modules'].rows_where("name =?", [data['symbol']]))[0]['id']
                data['module'] = module_key
                db_handle['performance_ids'].insert(data, ignore=True)


def mod_sql(sqlite_path: str, yaml_path: str):
    db = sqlite_utils.Database(sqlite_path)

    yaml_dict = read_yaml(yaml_path)

    write_dict_to_database(yaml_dict, db)


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    args = parse_cli(sys.argv)

    mod_sql(args.sqlite_path, args.yaml_path)

    logging.info('DONE.')


if __name__ == '__main__':
    main()
