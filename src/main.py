import sqlite3
import argparse
import yaml


def add_tables(db_cursor: sqlite3.Cursor):
    """
    Creates the telemetry and commands tables needed for the database.
    :param db_cursor: The cursor datbase handle.
    :return:
    """
    db_cursor.execute('create table if not exists telemetry(' 
                      'id INTEGER primary key, '
                      'name TEXT UNIQUE NOT NULL, '
                      'message_id INTEGER NOT NULL, '
                      'macro TEXT UNIQUE NOT NULL'
                      'symbol INTEGER NOT NULL, '
                      'module INTEGER NOT NULL'
                      'FOREIGN KEY (symbol) REFERENCES symbols(id), '
                      'FOREIGN KEY (module) REFERENCES modules(id)'
                      'UNIQUE (name, message_id, module));')

    db_cursor.execute('create table if not exists commands('
                      'id primary key,'
                      'name TEXT UNIQUE NOT NULL,'
                      'command_code INTEGER NOT NULL,'
                      'message_id INTEGER NOT NULL'
                      'macro TEXT UNIQUE NOT NULL'
                      'symbol INTEGER NOT NULL, '
                      'module INTEGER NOT NULL'
                      'FOREIGN KEY (symbol) REFERENCES symbols(id),'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, command_code, module));')


def read_yaml(yaml_file:str):
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def get_module_id(module_name: str, db_cursor: sqlite3.Cursor):
    """
    Fetches the id of the module whose name module_name
    :param module_name: The name of the module as it appears in the database.
    :param db_cursor: The cursor that points to the databse.
    :return: The module id.
    """
    module_id = db_cursor.execute('SELECT * FROM modules where name =?',
                                  (module_name,))
    return module_id.fetchone()[0]


def get_symbol_id(symbol_name: str, db_cursor: sqlite3.Cursor):
    """
    Fetches the id of the symbol whose name symbol_name
    :param symbol_name: The name of the module as it appears in the database.
    :param db_cursor: The cursor that points to the databse.
    :return: The module id.
    """
    symbol_id = db_cursor.execute('SELECT * FROM symbols where name =?',
                                  (symbol_name,))
    return symbol_id.fetchone()[0]


def write_telemetry_record(telemetry_data: dict, db_cursor: sqlite3.Cursor):
    name = None
    message_id = None
    macro = None
    symbol_id = None
    module_id = None

    for module_name in telemetry_data['modules']:
        module_id = get_module_id(module_name, db_cursor)

        for message in telemetry_data['modules'][module_name]['telemetry']:
            name = message
            message_id = telemetry_data['modules'][module_name]['telemetry'][message]['message_id']
            print('symbol id-->', get_symbol_id(telemetry_data['modules'][module_name]['telemetry'][message]['symbol'], db_cursor))

    # db_cursor.execute('INSERT INTO telemtry(name, message_id, macro, symbol ,module) '
    #                   'VALUES (?, ?, ?, ?, ?)',
    #                   (name, message_id, macro, symbol_id, module_id,))



def parse_cli() -> argparse.Namespace:
    """
    Parses cli argyments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='YAML file which contains telemetry and command metadata.')
    parser.add_argument('-yaml_path', '--yaml_path', metavar='YAML file path', type=str,
                        help='The file path to the YAML file which contains telemetry and command metadata')
    parser.add_argument('-sqlite_path', '--sqlite_path', metavar='Sqlite datbase path', type=str,
                        help='The file path to the sqlite database')

    return parser.parse_args()


def main():
    args = parse_cli()
    db_handle = sqlite3.connect(args.sqlite_path)
    db_cursor = db_handle.cursor()
    # add_tables(db_cursor)
    yaml_data = read_yaml(args.yaml_path)

    print('yaml-->', yaml_data['Airliner'])
    write_telemetry_record(read_yaml(args.yaml_path)['Airliner'], db_cursor)


if __name__ == '__main__':
    main()
