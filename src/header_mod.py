""""
This module modifies the database and adds a user-configurable sized header to every symbol that is mapped to message
and command.
"""
import argparse
import sqlite_utils
import yaml
import mod_sql
import logging


def remove_telemetry_symbol_headers(db_handle: sqlite_utils.Database, telemetry_symbol: int, header_size: int):
    """
    Removes field of symbol with id of telemetry_symbol that has a byte_offset less than header_size.
    This function also commits the delete transactions so there is no need to commit by the caller.
    :param telemetry_symbol:
    :param db_handle:
    :param header_size:
    :return:
    """
    db_handle['fields'].delete_where('byte_offset < ? and symbol=?', [header_size, telemetry_symbol])

    db_handle.conn.commit()


def remove_commands_symbol_headers(db_handle: sqlite_utils.Database, command_symbol: int, header_size: int):
    """
    Removes field of symbol with id of command_symbol that has a byte_offset less than header_size.
    This function also commits the delete transactions so there is no need to commit by the caller.
    :param command_symbol:
    :param db_handle:
    :param header_size:
    :return:
    """
    db_handle['fields'].delete_where('byte_offset < ? and symbol=?', [header_size, command_symbol])

    db_handle.conn.commit()


def add_telemetry_symbol_header(db_handle: sqlite_utils.Database, header_symbol_id: str,
                                telemetry_symbol_id: int,
                                header_field_name: str, little_endian: int):
    field_record = dict()
    field_record['symbol'] = telemetry_symbol_id
    field_record['name'] = header_field_name
    field_record['byte_offset'] = 0
    field_record['type'] = header_symbol_id
    field_record['multiplicity'] = 0
    field_record['little_endian'] = little_endian
    field_record['bit_size'] = 0
    field_record['bit_offset'] = 0

    db_handle['fields'].insert(field_record, ignore=True)


def add_commands_symbol_header(db_handle: sqlite_utils.Database, header_symbol_id: int, command_symbol_id: int,
                               header_field_name: str, little_endian: int):
    field_record = dict()

    field_record['symbol'] = command_symbol_id
    field_record['name'] = header_field_name
    field_record['byte_offset'] = 0
    field_record['type'] = header_symbol_id
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


def header_mod(db_handle: sqlite_utils.Database, headers_yaml: dict):
    """
    Replaces mis-representing fields with correct representation of haeaders(such as CCSDS) in database.
    :param db_handle:
    :param headers_yaml:
    :return:
    """
    # Write header symbols to database
    telemetry_data = {'symbols': headers_yaml['telemetry_header']['symbols'],
                      'fields': headers_yaml['telemetry_header']['fields']}
    commands_data = {'symbols': headers_yaml['command_header']['symbols'],
                     'fields': headers_yaml['command_header']['fields']}

    mod_sql.write_dict_to_database(telemetry_data, db_handle)
    mod_sql.write_dict_to_database(commands_data, db_handle)

    telemetry_symbol_size = headers_yaml['telemetry_header']['size']
    commands_header_size = headers_yaml['command_header']['size']

    header_telemetry_symbol_record = \
        list(db_handle['symbols'].rows_where('name=?', [headers_yaml['telemetry_header']['header_symbol']]))[0]

    header_commands_symbol_record = \
        list(db_handle['symbols'].rows_where('name=?', [headers_yaml['command_header']['header_symbol']]))[0]

    telemetry_little_endian = list(db_handle['elfs'].rows_where('id=?', [header_telemetry_symbol_record['elf']]))[0][
        'little_endian']

    commands_little_endian = list(db_handle['elfs'].rows_where('id=?', [header_commands_symbol_record['elf']]))[0][
        'little_endian']

    telemetry_header_symbol_id = header_telemetry_symbol_record['id']

    command_header_symbol_id = header_commands_symbol_record['id']

    # Cache stores to avoid redundant database lookups
    telemetry_symbols_processed = set()
    command_symbols_processed = set()

    for telemetry_record in db_handle['telemetry'].rows:
        if telemetry_record['symbol'] not in telemetry_symbols_processed:
            telemetry_symbols_processed.add(telemetry_record['symbol'])
            symbol_fields = list(db_handle['fields'].rows_where('symbol=?', [telemetry_record['symbol']]))

            field_name = list(filter(lambda field_record: field_record['byte_offset'] < telemetry_symbol_size,
                                     symbol_fields))

            # It is possible to have symbols that just don't have a header. In that case, we ignore them.
            if len(field_name) > 0:
                remove_telemetry_symbol_headers(db_handle, telemetry_record['symbol'],
                                                headers_yaml['telemetry_header']['size'])
                add_telemetry_symbol_header(db_handle, telemetry_header_symbol_id, telemetry_record['symbol'],
                                            field_name[0]['name'], telemetry_little_endian)

            else:
                logging.warning(f'The symbol {telemetry_record["symbol"]} does not have a header. It has been ignored.')

    for command_record in db_handle['commands'].rows:
        if command_record['symbol'] not in command_symbols_processed:
            command_symbols_processed.add(command_record['symbol'])

            symbol_fields = list(db_handle['fields'].rows_where('symbol=?', [command_record['symbol']]))

            field_name = list(filter(lambda field_record: field_record['byte_offset'] < telemetry_symbol_size,
                                     symbol_fields))

            # It is possible to have symbols that just don't have a header. In that case, we ignore them.
            if len(field_name) > 0:
                remove_commands_symbol_headers(db_handle, command_record['symbol'],
                                               commands_header_size)
                add_commands_symbol_header(db_handle, command_header_symbol_id, command_record['symbol'],
                                           field_name[0]['name'], commands_little_endian)


def main():
    args = parse_cli()

    headers_yaml = read_yaml(args.header_definitions)

    db = sqlite_utils.Database(args.sqlite_path)

    header_mod(db, headers_yaml)


if __name__ == '__main__':
    main()
