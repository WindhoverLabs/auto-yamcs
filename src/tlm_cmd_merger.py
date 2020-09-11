import sqlite3
import argparse
import yaml


def add_tables(db_cursor: sqlite3.Cursor):
    """
    Creates the telemetry and commands tables needed for the database.
    :param db_cursor: The cursor database handle.
    :return:
    """
    db_cursor.execute('create table if not exists telemetry('
                      'id INTEGER primary key, '
                      'name TEXT UNIQUE NOT NULL, '
                      'message_id INTEGER NOT NULL, '
                      'macro TEXT NOT NULL,'
                      'symbol INTEGER NOT NULL, '
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (symbol) REFERENCES symbols(id), '
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, message_id, module)'
                      ');')

    db_cursor.execute('create table if not exists commands('
                      'id INTEGER primary key,'
                      'name TEXT UNIQUE NOT NULL,'
                      'command_code INTEGER NOT NULL,'
                      'message_id INTEGER NOT NULL,'
                      'macro TEXT NOT NULL,'
                      'symbol INTEGER NOT NULL, '
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (symbol) REFERENCES symbols(id),'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, command_code, module));')

    db_cursor.execute('create table if not exists events('
                      'id INTEGER primary key,'
                      'event_id INTEGER NOT NULL,'
                      'macro TEXT NOT NULL,'
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (event_id, module));')

    db_cursor.execute('create table if not exists configurations('
                      'id INTEGER primary key,'
                      'name INTEGER NOT NULL,'
                      'value INTEGER NOT NULL,'
                      'macro TEXT NOT NULL,'
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, module));')

    db_cursor.execute('create table if not exists perf_ids('
                      'id INTEGER primary key,'
                      'name INTEGER NOT NULL,'
                      'perf_id INTEGER NOT NULL,'
                      'macro TEXT NOT NULL,'
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, perf_id, module));')


def read_yaml(yaml_file: str) -> dict:
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


def get_symbol_id(symbol_name: str, module_id: int, db_cursor: sqlite3.Cursor):
    """
    Fetches the id of the symbol whose name symbol_name
    :param symbol_name: The name of the module as it appears in the database.
    :param db_cursor: The cursor that points to the databse.
    :return: The module id.
    """
    symbol_id = db_cursor.execute('SELECT * FROM symbols where name =? and module=?',
                                  (symbol_name, module_id))
    return symbol_id.fetchone()[0]


def write_telemetry_records(telemetry_data: dict, db_cursor: sqlite3.Cursor):
    """
    Scans telemetry_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param telemetry_data:
    :param db_cursor:
    :return:
    """
    name = None
    message_id = None
    macro = None
    symbol_id = None
    module_id = None

    for module_name in telemetry_data['modules']:
        module_id = get_module_id(module_name, db_cursor)

        for message in telemetry_data['modules'][module_name]['telemetry']:
            message_dict = telemetry_data['modules'][module_name]['telemetry'][message]
            name = message
            message_id = message_dict['message_id']
            symbol_id = get_symbol_id(message_dict['symbol'],
                                      module_id, db_cursor)
            macro = message_dict['macro']

            # Write our telemetry record to the database.
            db_cursor.execute('INSERT INTO telemetry(name, message_id, macro, symbol ,module) '
                              'VALUES (?, ?, ?, ?, ?)',
                              (name, message_id, macro, symbol_id, module_id,))


def write_command_records(command_data: dict, db_cursor: sqlite3.Cursor):
    """
    Scans command_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param command_data:
    :param db_cursor:
    :return:
    """
    name = None
    message_id = None
    macro = None
    symbol_id = None
    module_id = None
    command_code = None

    for module_name in command_data['modules']:
        module_id = get_module_id(module_name, db_cursor)

        for command in command_data['modules'][module_name]['commands']:
            command_dict = command_data['modules'][module_name]['commands'][command]
            name = command
            message_id = command_dict['message_id']
            symbol_id = get_symbol_id(command_dict['symbol'],
                                      module_id, db_cursor)
            command_code = command_dict['command_code']
            macro = command_dict['macro']

            # Write our command record to the database.
            db_cursor.execute('INSERT INTO commands(name, command_code,message_id, macro, symbol ,module) '
                              'VALUES (?, ?, ?, ?, ?, ?)',
                              (name, command_code, message_id, macro, symbol_id, module_id,))


def write_event_records(event_data: dict, db_cursor: sqlite3.Cursor):
    """
    Scans event_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param event_data:
    :param db_cursor:
    :return:
    """
    event_id = None
    macro = None
    module_id = None

    for module_name in event_data['modules']:
        module_id = get_module_id(module_name, db_cursor)

        for event in event_data['modules'][module_name]['events']:
            event_dict = event_data['modules'][module_name]['events'][event]
            event_id = event
            macro = event_dict['macro']

            # Write our event record to the database.
            db_cursor.execute('INSERT INTO events(event_id, macro, module) '
                              'VALUES (?, ?, ?)',
                              (event_id, macro, module_id,))


def write_configuration_records(config_data: dict, db_cursor: sqlite3.Cursor):
    """
    Scans config_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param config_data:
    :param db_cursor:
    :return:
    """
    name = None
    macro = None
    module_id = None
    value = None

    for module_name in config_data['modules']:
        module_id = get_module_id(module_name, db_cursor)

        for config in config_data['modules'][module_name]['configurations']:
            config_dict = config_data['modules'][module_name]['configurations'][config]
            name = config
            macro = config_dict['macro']
            value = config_dict['value']

            # Write our event record to the database.
            db_cursor.execute('INSERT INTO configurations(name, value, macro ,module) '
                              'VALUES (?, ?, ?, ?)',
                              (name, value, macro, module_id))


def write_perf_id_records(perf_id_data: dict, db_cursor: sqlite3.Cursor):
    """
    Scans perf_id_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param perf_id_data:
    :param db_cursor:
    :return:
    """
    name = None
    macro = None
    module_id = None
    perf_id = None

    for module_name in perf_id_data['modules']:
        module_id = get_module_id(module_name, db_cursor)

        for perf_name in perf_id_data['modules'][module_name]['perf_ids']:
            perf_dict = perf_id_data['modules'][module_name]['perf_ids'][perf_name]
            name = perf_name
            macro = perf_dict['macro']
            perf_id = perf_dict['perf_id']

            # Write our event record to the database.
            db_cursor.execute('INSERT INTO perf_ids(name, perf_id, macro ,module) '
                              'VALUES (?, ?, ?, ?)',
                              (name, perf_id, macro, module_id))


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

    add_tables(db_cursor)

    yaml_data = read_yaml(args.yaml_path)

    # Write all the data to the database.
    write_telemetry_records(yaml_data, db_cursor)
    write_command_records(yaml_data, db_cursor)
    write_event_records(yaml_data, db_cursor)
    write_configuration_records(yaml_data, db_cursor)
    write_perf_id_records(yaml_data, db_cursor)

    # Save our changes to the database.
    db_handle.commit()


if __name__ == '__main__':
    main()
