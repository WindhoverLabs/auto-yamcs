""""
This module modifies the database and adds a user-configurable sized header to every symbol that is mapped to message
and command.
"""
import argparse
import sqlite_utils
import yaml
import mod_sql


def remove_telemetry_symbol_headers(db_handle: sqlite_utils.Database, header_size: int):
    """
    Removes every field of every symbol mapped to telemetry records that has a byte_offset less than header_size.
    This function also commits the delete transactions so there is no need to commit by the caller.
    :param db_handle:
    :param header_size:
    :return:
    """
    for telemetry_record in db_handle['telemetry'].rows:
        db_handle['fields'].delete_where('byte_offset < ? and symbol=?', [header_size, telemetry_record['symbol']])

    db_handle.conn.commit()


def remove_commands_symbol_headers(db_handle: sqlite_utils.Database, header_size: int):
    """
    Removes every field of every symbol mapped to commands records that has a byte_offset less than header_size.
    This function also commits the delete transactions so there is no need to commit by the caller.
    :param db_handle:
    :param header_size:
    :return:
    """
    for command_record in db_handle['commands'].rows:
        db_handle['fields'].delete_where('byte_offset < ? and symbol=?', [header_size, command_record['symbol']])

    db_handle.conn.commit()

def add_telemetry_symbol_headers(db_handle: sqlite_utils.Database, header_symbol: str):
    field_record = dict()
    header_symbol_record = list(db_handle['symbols'].rows_where('name=?', [header_symbol]))[0]
    little_endian = list(db_handle['elfs'].rows_where('id=?', [header_symbol_record['elf']]))[0]['little_endian']

    for telemetry_record in db_handle['telemetry'].rows:
        telemetry_symbol_record = list(db_handle['symbols'].rows_where('id=?', [telemetry_record['symbol']]))[0]
        field_record['symbol'] = telemetry_symbol_record['id']
        field_record['name'] = 'TlmHeader'
        field_record['byte_offset'] = 0
        field_record['type'] = header_symbol_record['id']
        field_record['multiplicity'] = 0
        field_record['little_endian'] = little_endian
        field_record['bit_size'] = 0
        field_record['bit_offset'] = 0

        db_handle['fields'].insert(field_record, ignore=True)


def add_commands_symbol_headers(db_handle: sqlite_utils.Database, header_symbol: str):
    field_record = dict()
    header_symbol_record = list(db_handle['symbols'].rows_where('name=?', [header_symbol]))[0]
    little_endian = list(db_handle['elfs'].rows_where('id=?', [header_symbol_record['elf']]))[0]['little_endian']

    for telemetry_record in db_handle['commands'].rows:
        command_symbol_record = list(db_handle['symbols'].rows_where('id=?', [telemetry_record['symbol']]))[0]
        field_record['symbol'] = command_symbol_record['id']
        field_record['name'] = 'CmdHeader'
        field_record['byte_offset'] = 0
        field_record['type'] = header_symbol_record['id']
        field_record['multiplicity'] = 0
        field_record['little_endian'] = little_endian
        field_record['bit_size'] = 0
        field_record['bit_offset'] = 0

        db_handle['fields'].insert(field_record, ignore=True)


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def parse_cli() -> argparse.Namespace:
    """
    Parses cli argyments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes size of header and path to sqlite database.')
    parser.add_argument('--sqlite_path', type=str,
                        help='The file path to the sqlite database', required=True)
    parser.add_argument('--header_definitions', type=str,
                        help='Path to config file that has all definitions of headers that need to be added such as'
                             ' command and telemetry headers, including their sizes.',
                        required=True)

    return parser.parse_args()


def main():
    args = parse_cli()

    headers_yaml = read_yaml(args.header_definitions)

    db = sqlite_utils.Database(args.sqlite_path)

    remove_telemetry_symbol_headers(db, headers_yaml['telemetry_header']['size'])
    remove_commands_symbol_headers(db, headers_yaml['command_header']['size'])

    telemetry_data = {'symbols': headers_yaml['telemetry_header']['symbols'],
                      'fields': headers_yaml['telemetry_header']['fields']}
    commands_data = {'symbols': headers_yaml['command_header']['symbols'],
                     'fields': headers_yaml['command_header']['fields']}

    mod_sql.write_dict_to_database(telemetry_data, db)
    mod_sql.write_dict_to_database(commands_data, db)

    add_telemetry_symbol_headers(db, headers_yaml['telemetry_header']['header_symbol'])
    add_commands_symbol_headers(db, headers_yaml['command_header']['header_symbol'])


if __name__ == '__main__':
    main()
