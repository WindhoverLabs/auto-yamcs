import argparse
import yaml
import sqlite3


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def remap_symbols(database_path, yaml_map: dict):
    """
    Remaps symbols in the database. This is very useful for situations where juicer does not
    accurately capture the intent of the source code. An example is a typedef'd voi* type by a macro.
    Since the "void*" type does not exist in the database(as of DWARF Version4), one may remap the macro to the word size
    of the machine which may represented by uint16, uint32 or uint64 depending on the architecture of course.
    :param database_path: The path to the sqlite database.
    :param yaml_map:A dictionary of the form {old_symbol1:new_symbol1, old_symbol2:new_symbol2} which has all
    of the remaps.
    :return:
    NOTE: This function commits the database transactions; so there is no need for the caller to commit anything to the
    database.
    """
    db_handle = sqlite3.connect(database_path)
    db_cursor = db_handle.cursor()

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

    yaml_remaps = read_yaml(args.yaml_path)['remaps']

    remap_symbols(args.database, yaml_remaps)


if __name__ == '__main__':
    main()
