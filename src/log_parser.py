""""
Reads in a binary file created by the ds application and outputs its contents into csv files. The ds application is an
application which is part of airliner. You can check it out at [1].
[1]:https://github.com/WindhoverLabs/airliner/tree/develop/apps/ds/fsw/src
"""
import argparse
import sqlite_utils
import yaml
from struct import unpack, calcsize
import csv
from enum import Enum
from pathlib import Path
import os
import logging


class LengthSource(int, Enum):
    DATABASE = 1
    STREAM = 2


"""
A mapping between intrinsic types in the database such as int, char, short, etc
and the format strings specified on [1]. This mapping does NOT include strings. String handling does not rely on
this mapping.
[1]:https://docs.python.org/3/library/struct.html?highlight=struct#format-strings
"""
symbol_to_struct_format_map = \
    {
        'int': 'i',
        'int8': 'b',  # Maps to the same thing as 'signed char' type
        'char': 'c',
        'int16': 'h',
        'int32': 'i',
        'enum': 'i',
        'int64': 'l',
        'uint8': 'B',
        'uint16': 'H',
        'uint32': 'I',
        'uint64': 'Q',
        'short': 'h',
        'unsigned short': 'H',
        'long': 'l',
        'unsigned long': 'L',
        'long long': 'q',
        'unsigned long long': 'Q',
        'double': 'd',
        'bool': '?',
        "boolean": '?',
        'float': 'f',
        'osalbool': 'B',
        '_padding8': 'c',
        '_padding16': '2c',
        '_padding24': '3c',
        '_padding32': '4c',  # NOTE: I think it might be best to generate these padding types from a function
    }


def is_enum(symbol_id: int, db_handle: sqlite_utils.Database):
    is_symbol_enum = len(list(db_handle['enumerations'].rows_where('symbol=?', [symbol_id]))) > 0

    return is_symbol_enum


def get_struct_format_string(symbol_id: int, header_size: int, db_handle: sqlite_utils.Database, depth: int = 0):
    """
    Returns a string that can be used by the struct module to unpack a C-style struct from a binary stream.
    Please note that the ccsds header is ignored. So the string that is returned is the
    payload of the message, meaning the struct that has holds the data in code.
    :param db_handle:
    :param header_size:
    :param symbol_id:
    :return:The string which represents the structure according to the specification at [1]. Note that if the
    structure does not have a payload, meaning all it has is a header(such as Noop commands), an empty string is returned.
    [1]:https://docs.python.org/3/library/struct.html?highlight=struct#format-characters
    """
    fields = list(db_handle['fields'].rows_where('symbol=?', [symbol_id], order_by='byte_offset'))

    format_string = ''
    # Filter out the ccsds headers
    if depth == 0:
        filtered_fields = list(filter(lambda record: record['byte_offset'] >= header_size, fields))
        if filtered_fields:
            little_endian = '<' if filtered_fields[0]['little_endian'] == 1 else '>'
            format_string = little_endian
    else:
        filtered_fields = fields

    for field in filtered_fields:
        if is_enum(field['type'], db_handle):
            type_name = 'enum'

        else:
            type_name = list(db_handle['symbols'].rows_where('id=?', [field['type']]))[0]['name']

        if type_name not in symbol_to_struct_format_map:
            child_symbol_id = list(db_handle['symbols'].rows_where('name=?', [type_name]))[0]['id']
            format_string += get_struct_format_string(child_symbol_id, header_size, db_handle, depth + 1)

        else:
            if field['multiplicity'] == 0:
                format_string += symbol_to_struct_format_map[type_name]

            else:
                # FIXME: If multiplicity is greater than 0 and the type_name is char, we assume this is a string, for now.
                if type_name == 'char':
                    format_string += str(field['multiplicity'])
                    format_string += 's'
                else:
                    format_string += str(field['multiplicity'])
                    format_string += symbol_to_struct_format_map[type_name]

    return format_string


class TimeFormat(Enum):
    CFE_SB_TIME_32_16_SUBS = 0
    CFE_SB_TIME_32_32_SUBS = 1
    CFE_SB_TIME_32_32_M_20 = 2


class PacketType(Enum):
    TELEMETRY = 0
    COMMAND = 1


def get_structure_names(yaml_dict: dict):
    structures = []
    for s in yaml_dict['structures']:
        structures.append(s['name'])

    return structures


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def is_secondary_header_present(stream_id: int):
    """
    Checks if the secondary header is present. How this is checked is documented by 'ccsds.h'
    on the airliner codebase at 'airliner/core/cfe/fsw/src/inc/ccsds.h'.
    :param stream_id:
    :return:
    """
    return stream_id >> 11 & 1 == 1


def get_time(time_format: TimeFormat, bits: bin):
    # FIXME: Add support for other time formats
    if time_format == TimeFormat.CFE_SB_TIME_32_16_SUBS:
        seconds, = unpack('I', bits[:4])

    return str(seconds)


def get_packet_type(stream_id: int):
    """
    Get the type of packet this message is; it could be a telemetry packet or command packet.
    The definition for command and telemetry packet can be found on airliner's codebase at
    [1].
    [1]:https://github.com/WindhoverLabs/airliner/blob/develop/core/cfe/fsw/src/inc/ccsds.h#L92
    :param stream_id:
    :param primary_header:
    :return:
    """

    packet_type_bit = stream_id >> 12 & 1
    packet_type = None

    if packet_type_bit == 0:
        packet_type = PacketType.TELEMETRY
    else:
        packet_type = PacketType.COMMAND

    return packet_type


def message_id_exists(db_handle: sqlite_utils.Database, message_id: int):
    """
    Checks if message_id exists either in the telemetry table.
    :param db_handle:
    :param message_id:
    :return:
    """
    message_id = list(db_handle['telemetry'].rows_where('message_id=?', [message_id]))
    out_message_id_exists = False
    if len(message_id) > 0:
        out_message_id_exists = True

    return out_message_id_exists


def message_id_and_command_code_exists(db_handle: sqlite_utils.Database, message_id: int, command_code: int):
    """
    Checks if the record with message_id and command_code exists in the commands table.
    :param command_code:
    :param db_handle:
    :param message_id:
    :return:
    """
    command_record = list(
        db_handle['commands'].rows_where('message_id=? and command_code=?', [message_id, command_code]))
    record_exists = False
    if len(command_record) > 0:
        record_exists = True

    return record_exists


# FIXME:Ignore ccsds headers. Move this function to another function where the get_struct_format_string gets called along with this function
def get_field_names_from_struct(symbol_id: int, header_size: int, db_handle: sqlite_utils.Database, depth: int = 0):
    field_labels = []
    fields = list(db_handle['fields'].rows_where('symbol=?', [symbol_id], order_by='byte_offset'))

    # Filter out the ccsds headers
    if depth == 0:
        filtered_fields = list(filter(lambda field_record: field_record['byte_offset'] >= header_size, fields))

    else:
        filtered_fields = fields

    type_to_symbol_name = {}

    for symbol_field in filtered_fields:
        field_type_name = list(db_handle['symbols'].rows_where('id=?', [symbol_field['type']]))[0]['name']
        type_to_symbol_name[symbol_field['type']] = field_type_name

    for record in filtered_fields:
        if type_to_symbol_name[record['type']] in symbol_to_struct_format_map:
            field_labels.append(record['name'])
        else:
            children_fields = get_field_names_from_struct(record['type'], header_size, db_handle, depth + 1)
            field_labels += children_fields

    return field_labels


def write_telemetry_row_to_csv(message_macro: str, message_id: int, symbol_name: str, fields: list, filed_values: tuple,
                               time_in_seconds: int):
    file_name = message_macro + '.csv'
    my_file = Path(file_name)
    does_file_exist = (my_file.exists() and my_file.is_file())

    with open(file_name, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)

        if does_file_exist is False:
            writer.writerow(['message_id', 'time in seconds', 'symbol_name'] + fields)

        writer.writerow([message_id, time_in_seconds, symbol_name] + list(filed_values))


def write_command_row_to_csv(message_macro: str, command_code: int, message_id: int, symbol_name: str, fields: list,
                             filed_values: tuple):
    file_name = message_macro + '_CC_' + str(command_code) + '.csv'
    my_file = Path(file_name)
    does_file_exist = (my_file.exists() and my_file.is_file())

    with open(file_name, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)

        if does_file_exist is False:
            writer.writerow(['message_id', 'symbol_name'] + fields)

        writer.writerow([message_id, symbol_name] + list(filed_values))


def get_symbol_name(symbol_id: int, db_handle: sqlite_utils.Database):
    symbol_name = list(db_handle['symbols'].rows_where('id=?', [symbol_id]))[0]['name']
    return symbol_name


def get_symbol_id_from_message_id(message_id: int, db_handle: sqlite_utils.Database) -> int:
    """
    Returns the symbol id that is mapped to message_id.
    Be sure to call does_message_id_exist before calling this function.
    :return:
    """
    symbol_record = list(db_handle['telemetry'].rows_where('message_id=?', [message_id]))

    symbol_key = symbol_record[0]['symbol']

    return symbol_key


def get_symbol_id_from_message_id_and_command_code(message_id: int, command_code: int,
                                                   db_handle: sqlite_utils.Database) -> int:
    """
    Returns the symbol id that is mapped to message_id and command_code in the commands table.
    Be sure to call does_message_id_exist before calling this function.
    :return:
    """
    symbol_key = \
        list(db_handle['commands'].rows_where('message_id=? and command_code=?', [message_id, command_code]))[0][
            'symbol']
    return symbol_key


def get_telemetry_message_macro(message_id: int, db_handle: sqlite_utils.Database):
    macro = list(db_handle['telemetry'].rows_where('message_id=?', [message_id]))[0]['macro']
    return macro


def get_command_macro(message_id: int, command_code: int, db_handle: sqlite_utils.Database):
    macro = list(db_handle['commands'].rows_where('message_id=? and command_code=?', [message_id, command_code]))[0][
        'macro']
    return macro


def get_command_code(command_header: int):
    """
    Calculates the command code as per specification at [1].
    [1]:https://github.com/WindhoverLabs/airliner/blob/8f8df92f3af0875600d15783f77be593d34c1430/core/cfe/fsw/src/inc/ccsds.h#L134
    :param command_header:
    :return:
    """
    return int("{0:{fill}16b}".format(command_header, fill='0')[8:15], 2)


# FIXME: Cleanup code

def parse_file(file_path: str, sqlite_path: str, structures: [str], time_format: TimeFormat,
               length_source: LengthSource):
    """
    Parses the file at file_path, extracts all data from it and outputs it into a csv.
    :param length_source:
    :param file_path:
    :param sqlite_path:
    :param structures:
    :param time_format:
    :return:
    """
    db = sqlite_utils.Database(sqlite_path)
    file_size = os.path.getsize(file_path)
    f = open(file_path, "rb")
    bytes_buffer = f.read()

    file_header_size = 0
    for structure in structures:
        file_header_size += list(db['symbols'].rows_where('name=?', [structure]))[0]['byte_size']

    message_data = bytes_buffer[file_header_size:]

    current_message_index = 0
    number_of_messages = len(message_data)

    struct_string = None
    struct_size = 0
    symbol_id = None

    # These map work like a cache for our symbols so we don't have to have redundant queries that slow down our code
    telemetry_symbol_map = {}
    commands_symbol_map = {}

    symbol_field_labels = None
    time_in_seconds = 0

    ccsds_header_length = 0

    while current_message_index < file_size - file_header_size:
        # We assume that the primary header is always a ccsds primary header
        primary_header = message_data[current_message_index: current_message_index + 6]
        stream_id, sequence, length = unpack('!HHH', primary_header)

        if get_packet_type(stream_id) == PacketType.TELEMETRY:
            if message_id_exists(db, stream_id) is False:
                logging.warning(f'Message id {stream_id} was not found in the database.'
                                f'Aborting parser.')
                return
            ccsds_header_length = 6
            if is_secondary_header_present(stream_id):
                secondary_header = message_data[current_message_index + 6: current_message_index + 12]
                ccsds_header_length = 12
                time_in_seconds = get_time(time_format, secondary_header)

            # Keep track of previous message ids to optimize; otherwise the script could take minutes to finish
            if not (stream_id in telemetry_symbol_map):
                symbol_id = get_symbol_id_from_message_id(stream_id, db)
                symbol_name = get_symbol_name(symbol_id, db)
                struct_string = get_struct_format_string(symbol_id, ccsds_header_length, db)
                symbol_field_labels = get_field_names_from_struct(symbol_id, ccsds_header_length, db)
                struct_size = calcsize(struct_string)
                message_macro = get_telemetry_message_macro(stream_id, db)

                # NOTE: Please note that symbol and struct are synonyms in this context; they mean the same thing.
                telemetry_symbol_map.update({stream_id:
                                                 {'symvol_id': symbol_id,
                                                  'struct_string': struct_string,
                                                  'symbol_field_labels': symbol_field_labels,
                                                  'struct_size': struct_size,
                                                  'symbol_name': symbol_name,
                                                  'message_macro': message_macro}
                                             })
            # current_message_index += ccsds_header_length

            write_telemetry_row_to_csv(telemetry_symbol_map[stream_id]['message_macro'], stream_id,
                                       telemetry_symbol_map[stream_id]['symbol_name'],
                                       telemetry_symbol_map[stream_id]['symbol_field_labels'],
                                       unpack(telemetry_symbol_map[stream_id]['struct_string'],
                                              message_data[
                                              current_message_index + ccsds_header_length:current_message_index + ccsds_header_length +
                                                                                          telemetry_symbol_map[
                                                                                              stream_id][
                                                                                              'struct_size']]),
                                       time_in_seconds)

            if length_source == LengthSource.STREAM:
                current_message_index += length + 7

            elif length_source == LengthSource.DATABASE:
                current_message_index += ccsds_header_length + telemetry_symbol_map[stream_id]['struct_size']

        elif get_packet_type(stream_id) == PacketType.COMMAND:
            ccsds_header_length = 6
            if is_secondary_header_present(stream_id):
                command_secondary_header = message_data[current_message_index + 6: current_message_index + 8]
                ccsds_header_length = 8
                command, = unpack('!H', command_secondary_header)
                command_code = get_command_code(command)

                if message_id_and_command_code_exists(db, stream_id, command_code) is False:
                    logging.warning(f'Message id {stream_id} with command_code {command_code} was not found in the '
                                    f'database. '
                                    f'Aborting parser.')
                    return

                if not ((stream_id, command_code) in commands_symbol_map):
                    symbol_id = get_symbol_id_from_message_id_and_command_code(stream_id, command_code, db)
                    symbol_name = get_symbol_name(symbol_id, db)
                    struct_string = get_struct_format_string(symbol_id, ccsds_header_length, db)
                    symbol_field_labels = get_field_names_from_struct(symbol_id, ccsds_header_length, db)
                    struct_size = calcsize(struct_string)
                    command_macro = get_command_macro(stream_id, command_code, db)

                    # NOTE: Please note that symbol and struct are synonyms in this context; they mean the same thing.
                    commands_symbol_map.update({(stream_id, command_code):
                                                    {'symvol_id': symbol_id,
                                                     'struct_string': struct_string,
                                                     'symbol_field_labels': symbol_field_labels,
                                                     'struct_size': struct_size,
                                                     'symbol_name': symbol_name,
                                                     'command_macro': command_macro,
                                                     'command_code': command_code}
                                                })

                # current_message_index += ccsds_header_length

            write_command_row_to_csv(commands_symbol_map[(stream_id, command_code)]['command_macro'], command_code,
                                     stream_id,
                                     commands_symbol_map[(stream_id, command_code)]['symbol_name'],
                                     commands_symbol_map[(stream_id, command_code)]['symbol_field_labels'],
                                     unpack(commands_symbol_map[(stream_id, command_code)]['struct_string'],
                                            message_data[
                                            current_message_index + ccsds_header_length:current_message_index + ccsds_header_length +
                                                                                        commands_symbol_map[
                                                                                            (stream_id, command_code)][
                                                                                            'struct_size']]))
            if length_source == LengthSource.STREAM:
                current_message_index += length + 7

            elif length_source == LengthSource.DATABASE:
                current_message_index += ccsds_header_length + commands_symbol_map[(stream_id, command_code)][
                    'struct_size']
        else:
            logging.warning(f"Unknown packet type."
                            f"Aborting parser.")
            return


str_to_time_enum = \
    {
        'CFE_SB_TIME_32_16_SUBS': TimeFormat.CFE_SB_TIME_32_16_SUBS,
        'CFE_SB_TIME_32_32_SUBS': TimeFormat.CFE_SB_TIME_32_32_SUBS,
        'CFE_SB_TIME_32_32_M_20': TimeFormat.CFE_SB_TIME_32_32_M_20
    }


def parse_cli() -> argparse.Namespace:
    """
    Parses cli arguments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in paths to yaml file and sqlite database.')
    parser.add_argument('--structures_yaml', type=str,
                        help='The file path to the YAML file which contains the names of the structures that come before '
                             'the telemetry data. Please note that the order in which the structures are defined in the '
                             'yaml file matters.',
                        required=True)
    parser.add_argument('--sqlite_path', type=str,
                        help='The file path to the sqlite database', required=True)

    parser.add_argument('--input_file', type=str,
                        help='The file path to the file that contains the telemetry/command data.', required=True)

    parser.add_argument('--time_format', type=str, default='CFE_SB_TIME_32_16_SUBS',
                        choices=['CFE_SB_TIME_32_16_SUBS', 'CFE_SB_TIME_32_32_SUBS', 'CFE_SB_TIME_32_32_M_20'],
                        help='The time format for the ccsds header.')

    parser.add_argument('--message_length_source', type=int, choices=[1, 2], default=2,
                        help='Which source should the parser use as the source of truth for the length of a message.'
                             'This length is used as an offset to move to the next message in the stream.'
                             'Use 1 for database. 2 for the length inside the input file.')

    return parser.parse_args()


def main():
    args = parse_cli()

    yaml_structs = read_yaml(args.structures_yaml)
    parse_file(args.input_file, args.sqlite_path, get_structure_names(yaml_structs), str_to_time_enum[args.time_format],
               LengthSource(args.message_length_source))


if __name__ == '__main__':
    main()
