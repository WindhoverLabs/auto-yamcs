import argparse
import yaml
import sqlite3


def parse_cli() -> argparse.Namespace:
    """
    Parses cli argyments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in path to sqlite database.')

    parser.add_argument('--database', type=str, required=True, help='The path to the SQLITE database..')

    parser.add_argument('--yaml_path', type=str, required=True,
                        help='The yaml config file that has the symbol remappings.')

    return parser.parse_args()


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def remap_symbols(db_handle, yaml_map: dict):
    db_cursor = db_handle.cursor()
    for old_symbol, new_symbol in yaml_map.items():
        old_symbol_id = db_cursor.execute('SELECT id FROM symbols where name=?',
                                          (old_symbol,)).fetchone()[0]

        new_symbol_id = db_cursor.execute('SELECT id FROM symbols where name=?',
                                          (new_symbol,)).fetchone()[0]

        field_ids = db_cursor.execute('SELECT id FROM fields where type=?',
                                      (old_symbol_id,)).fetchall()

        print(f'new_symbol_id-->{new_symbol_id}')
        print(f'old_symbol_id-->{old_symbol_id}')

        for field_id in field_ids:
            db_handle.execute("UPDATE fields SET type = ? WHERE id = ?",
                          (new_symbol_id, field_id[0]))
            db_handle.commit()


def main():
    args = parse_cli()
    yaml_data = read_yaml(args.yaml_path)
    db_handle = sqlite3.connect(args.database)
    db_cursor = db_handle.cursor()

    remap_symbols(db_handle, yaml_data['remaps'])

    db_handle.commit()


if __name__ == '__main__':
    main()