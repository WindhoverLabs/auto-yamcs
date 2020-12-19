import argparse
import yaml
import sqlite3


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


# FIXME: In order to work with the singleton config, yaml_path should the contents of the YAML file itself.
def remap_symbols(database_path, yaml_path: str):
    db_handle = sqlite3.connect(database_path)
    db_cursor = db_handle.cursor()

    yaml_map = read_yaml(yaml_path)['remaps']

    for old_symbol, new_symbol in yaml_map.items():
        old_symbol_id = db_cursor.execute('SELECT id FROM symbols where name=?',
                                          (old_symbol,)).fetchone()[0]

        new_symbol_id = db_cursor.execute('SELECT id FROM symbols where name=?',
                                          (new_symbol,)).fetchone()[0]

        field_ids = db_cursor.execute('SELECT id FROM fields where type=?',
                                      (old_symbol_id,)).fetchall()

        for field_id in field_ids:
            db_handle.execute("UPDATE fields SET type = ? WHERE id = ?",
                              (new_symbol_id, field_id[0]))
            db_handle.commit()


def parse_cli() -> argparse.Namespace:
    """
    Parses cli arguments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in path to sqlite database.')

    parser.add_argument('--database', type=str, required=True, help='The path to the SQLITE database..')

    parser.add_argument('--yaml_path', type=str, required=True,
                        help='The yaml config file that has the symbol remappings.')

    return parser.parse_args()


def main():
    args = parse_cli()

    remap_symbols(args.database, args.yaml_path)


if __name__ == '__main__':
    main()
