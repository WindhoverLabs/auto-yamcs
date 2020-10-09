import sqlite3
import argparse
import yaml
import logging


def add_tables(db_cursor: sqlite3.Cursor):
    """
    Creates the telemetry and commands tables needed for the database.
    :param db_cursor: The cursor database handle.
    :return:
    """
    db_cursor.execute('create table if not exists modules('
                      'id INTEGER primary key,'
                      'name TEXT UNIQUE NOT NULL);')

    db_cursor.execute('create table if not exists telemetry('
                      'id INTEGER primary key, '
                      'name TEXT UNIQUE NOT NULL, '
                      'message_id INTEGER NOT NULL, '
                      'macro TEXT,'
                      'symbol INTEGER NOT NULL, '
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (symbol) REFERENCES symbols(id), '
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, message_id, module)'
                      ');')

    db_cursor.execute('create table if not exists commands('
                      'id INTEGER primary key,'
                      'name TEXT NOT NULL,'
                      'command_code INTEGER NOT NULL,'
                      'message_id INTEGER NOT NULL,'
                      'macro TEXT,'
                      'symbol INTEGER NOT NULL, '
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (symbol) REFERENCES symbols(id),'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, command_code, module, message_id));')

    db_cursor.execute('create table if not exists events('
                      'id INTEGER primary key,'
                      'event_id INTEGER,'
                      'name TEXT,'
                      'module INTEGER,'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (event_id, module));')

    db_cursor.execute('create table if not exists configurations('
                      'id INTEGER primary key,'
                      'name TEXT NOT NULL,'
                      'value INTEGER,'
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, module));')

    db_cursor.execute('create table if not exists performance_ids('
                      'id INTEGER primary key,'
                      'name TEXT,'
                      'perf_id INTEGER NOT NULL,'
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, perf_id, module));')


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def get_module_id(module_name: str, db_cursor: sqlite3.Cursor) -> tuple:
    """
    Fetches the id of the module whose name module_name
    :param module_name: The name of the module as it appears in the database.
    :param db_cursor: The cursor that points to the databse.
    :return: The module id.
    """
    module_id = db_cursor.execute('SELECT * FROM modules where name =?',
                                  (module_name,))

    # FIXME: This is a possible approach to take when the module does not exist. Will re-address in the future.
    # if module_id is None:
    #     db_cursor.execute('INSERT INTO modules(name) '
    #                       'values(?)',
    #                       (module_name,))
    #     logging.warning(f'{module_name} module was added to the database.')

    # module_id = db_cursor.execute('SELECT * FROM modules where name =?',
    #                               (module_name,)).fetchone()

    return module_id.fetchone()


def get_symbol_id(symbol_name: str, db_cursor: sqlite3.Cursor) -> tuple:
    """
    Fetches the id of the symbol whose name symbol_name
    :param symbol_name: The name of the module as it appears in the database.
    :param db_cursor: The cursor that points to the databse.
    :return: The module id.
    """
    symbol_id = db_cursor.execute('SELECT * FROM symbols where name =?',
                                  (symbol_name,))
    return symbol_id.fetchone()


def write_module_records(module_data: dict, db_cursor: sqlite3.Cursor):
    """
    Scans module_data and writes each module to the database..
    :param module_data:
    :param db_cursor:
    :return:
    """
    if 'core' in module_data:
        for module in module_data['core']['cfe'].keys():
            if module != 'config':
                db_cursor.execute('insert into modules(name) values(?)', (module,))

        for module in module_data['modules'].keys():
            print(f'current module:{module}')
            db_cursor.execute('insert into modules(name) values(?)', (module,))


def write_telemetry_records(telemetry_data: dict, modules_dict: dict, db_cursor: sqlite3.Cursor):
    """
    Scans telemetry_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param telemetry_data:
    :param db_cursor:
    :param modules_dict: A dictionary of the form {module_id: module_name}
    :return:
    """
    name = None
    message_id = None
    macro = None
    symbol_id = None

    for module_name in telemetry_data['modules']:
        for message in telemetry_data['modules'][module_name]['telemetry']:
            message_dict = telemetry_data['modules'][module_name]['telemetry'][message]
            name = message
            message_id = message_dict['msgID']
            symbol = get_symbol_id(message_dict['struct'], db_cursor)

            # If the symbol does not exist, we skip it
            if symbol:
                symbol_id = symbol[0]

                # FIXME: Not sure if we'll read the macro in this step of the chain
                # macro = message_dict['macro']

                # Write our telemetry record to the database.
                db_cursor.execute('INSERT INTO telemetry(name, message_id, symbol ,module) '
                                  'VALUES (?, ?, ?, ?)',
                                  (name, message_id, symbol_id, modules_dict[module_name],))

    if 'core' in telemetry_data:
        for module in telemetry_data['core']['cfe'].keys():
            if module != 'config':
                for message in telemetry_data['core']['cfe'][module]['telemetry']:
                    message_dict = telemetry_data['core']['cfe'][module]['telemetry'][message]
                    name = message
                    message_id = message_dict['msgID']
                    symbol = get_symbol_id(message_dict['struct'], db_cursor)

                    # If the symbol does not exist, we skip it
                    if symbol:
                        symbol_id = symbol[0]

                        # FIXME: Not sure if we'll read the macro in this step of the chain
                        # macro = message_dict['macro']

                        # Write our telemetry record to the database.
                        db_cursor.execute('INSERT INTO telemetry(name, message_id, symbol ,module) '
                                          'VALUES (?, ?, ?, ?)',
                                          (name, message_id, symbol_id, modules_dict[module],))


def write_command_records(command_data: dict, modules_dict: dict, db_cursor: sqlite3.Cursor):
    """
    Scans command_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param command_data:
    :param db_cursor:
    :return:
    """
    for module_name in command_data['modules']:
        for command in command_data['modules'][module_name]['commands']:
            command_dict = command_data['modules'][module_name]['commands'][command]
            message_id = command_dict['msgID']
            sub_commands = command_data['modules'][module_name]['commands']

            for sub_command in sub_commands[command]['commands']:
                sub_command_dict = sub_commands[command]['commands']
                name = sub_command

                symbol = get_symbol_id(sub_command_dict[name]['struct'], db_cursor)

                # If the symbol does not exist, we skip it
                if symbol:
                    symbol_id = symbol[0]
                    command_code = sub_command_dict[name]['cc']

                    # FIXME: Not sure if we'll read the macro in step of the chain
                    # macro = command_dict['macro']

                    # Write our command record to the database.
                    db_cursor.execute('INSERT INTO commands(name, command_code, message_id, symbol ,module) '
                                      'VALUES (?, ?, ?, ?, ?)',
                                      (name, command_code, message_id, symbol_id, modules_dict[module_name],))

    if 'core' in command_data:
        for module_name in command_data['core']['cfe'].keys():
            if module_name != 'config':
                for command in command_data['core']['cfe'][module_name]['commands']:
                    command_dict = command_data['core']['cfe'][module_name]['commands'][command]
                    message_id = command_dict['msgID']
                    sub_commands = command_data['core']['cfe'][module_name]['commands']

                    for sub_command in sub_commands[command]['commands']:
                        sub_command_dict = sub_commands[command]['commands']
                        name = sub_command

                        symbol = get_symbol_id(sub_command_dict[name]['struct'], db_cursor)

                        # If the symbol does not exist, we skip it
                        if symbol:
                            symbol_id = symbol[0]
                            command_code = sub_command_dict[name]['cc']

                            # FIXME: Not sure if we'll read the macro in step of the chain
                            # macro = command_dict['macro']

                            # Write our command record to the database.
                            db_cursor.execute('INSERT INTO commands(name, command_code, message_id, symbol ,module) '
                                              'VALUES (?, ?, ?, ?, ?)',
                                              (name, command_code, message_id, symbol_id, modules_dict[module_name],))


def write_event_records(event_data: dict, modules_dict: dict, db_cursor: sqlite3.Cursor):
    """
    Scans event_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param event_data:
    :param db_cursor:
    :return:
    """
    event_id = None
    macro = None

    for module_name in event_data['modules']:
        for event in event_data['modules'][module_name]['events']:
            event_dict = event_data['modules'][module_name]['events'][event]
            event_id = event

            # FIXME: Not sure if we'll read the macro in step of the chain
            # macro = event_dict['macro']

            # Write our event record to the database.
            db_cursor.execute('INSERT INTO events(event_id, module) '
                              'VALUES (?, ?)',
                              (event_id, modules_dict[module_name],))


def write_configuration_records(config_data: dict, modules_dict: dict, db_cursor: sqlite3.Cursor):
    """
    Scans config_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param config_data:
    :param db_cursor:
    :return:
    """
    name = None
    macro = None
    value = None

    for module_name in config_data['modules']:
        for config in config_data['modules'][module_name]['config']:
            config_dict = config_data['modules'][module_name]['config'][config]
            name = config
            # FIXME: Not sure if we'll read the macro in step of the chain
            # macro = event_dict['macro']
            value = config_dict['value']

            # Write our event record to the database.
            db_cursor.execute('INSERT INTO configurations(name, value ,module) '
                              'VALUES (?, ?, ?)',
                              (name, value, modules_dict[module_name]))


def write_perf_id_records(perf_id_data: dict, modules_dict: dict, db_cursor: sqlite3.Cursor):
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
        for perf_name in perf_id_data['modules'][module_name]['perfids']:
            perf_dict = perf_id_data['modules'][module_name]['perfids'][perf_name]
            name = perf_name
            # FIXME: Not sure if we'll read the macro in step of the chain
            # macro = event_dict['macro']
            perf_id = perf_dict['id']

            # Write our event record to the database.
            db_cursor.execute('INSERT INTO performance_ids(name, perf_id ,module) '
                              'VALUES (?, ?, ?)',
                              (name, perf_id, modules_dict[module_name]))


def write_tlm_cmd_data(yaml_data: dict, db_cursor: sqlite3.Cursor):
    write_module_records(yaml_data, db_cursor)

    # Get all modules needed now that they are on the database.
    modules_dict = {}
    for module_id, module_name in db_cursor.execute('select * from modules').fetchall():
        modules_dict[module_name] = module_id

    write_telemetry_records(yaml_data, modules_dict, db_cursor)
    write_command_records(yaml_data, modules_dict, db_cursor)
    write_event_records(yaml_data, modules_dict, db_cursor)
    write_configuration_records(yaml_data, modules_dict, db_cursor)
    write_perf_id_records(yaml_data, modules_dict, db_cursor)


def parse_cli() -> argparse.Namespace:
    """
    Parses cli argyments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in paths to yaml file and sqlite database.')
    parser.add_argument('--yaml_path', type=str,
                        help='The file path to the YAML file which contains telemetry and command metadata.',
                        required=True)
    parser.add_argument('--sqlite_path', type=str,
                        help='The file path to the sqlite database', required=True)

    return parser.parse_args()


def merge_all(database_path: str, yaml_file: str):
    db_handle = sqlite3.connect(database_path)
    db_cursor = db_handle.cursor()

    add_tables(db_cursor)

    yaml_data = read_yaml(yaml_file)

    # Write all the data to the database.
    write_tlm_cmd_data(yaml_data, db_cursor)

    # Save our changes to the database.
    db_handle.commit()


def main():
    args = parse_cli()
    merge_all(args.sqlite_path, args.yaml_path)


if __name__ == '__main__':
    main()
