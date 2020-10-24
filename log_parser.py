""""
Reads in a binary file created by the ds application and outputs its contents into csv files. The ds application is an
application which is part of airliner. You can check it out at [1].
[1]:https://github.com/WindhoverLabs/airliner/tree/develop/apps/ds/fsw/src
"""
import argparse
import sqlite_utils
import yaml
from struct import pack, unpack, calcsize
import csv
from enum import Enum
from pathlib import Path

import os

"""
A mapping between intrinsic types in the database such as int, char, short, etc
and the format strings specified on [1]. This mapping does NOT include strings. String handling does not rely on
this mappping.
[1]:https://docs.python.org/3/library/struct.html?highlight=struct#format-strings
"""
symbol_to_struct_format_map = \
    {
        'int': 'i',
        'int8': 'b',  # Maps to the same thing as 'signed char' type
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
        'float': 'f'
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
    :return:s
    """
    fields = list(db_handle['fields'].rows_where('symbol=?', [symbol_id], order_by='byte_offset'))

    # Filter out the ccsds headers
    if depth == 0:
        filtered_fields = list(filter(lambda record: record['byte_offset'] >= header_size, fields))
    else:
        filtered_fields = fields

    little_endian = '<' if filtered_fields[0]['little_endian'] == 1 else '>'

    format_string = little_endian

    for field in filtered_fields:
        if is_enum(field['type'], db_handle):
            type_name = 'enum'

        else:
            type_name = list(db_handle['symbols'].rows_where('id=?', [field['type']]))[0]['name']

        if type_name not in symbol_to_struct_format_map:
            child_symbol_id = list(db_handle['symbols'].rows_where('name=?', [type_name]))[0]['id']
            format_string += get_struct_format_string(child_symbol_id, header_size, db_handle, depth+1)

        if field['multiplicity'] == 0:
            format_string += symbol_to_struct_format_map[type_name]

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


# FIXME: At the moment endianness is assumed to be network byte-order(Big Endian)
def map_structure_to_fields():
    pass


def is_secondary_header_present(stream_id: int):
    """
    Checks if the secondary header is present. How this is checked is documented by 'ccsds.h'
    on the airliner codebase at 'airliner/core/cfe/fsw/src/inc/ccsds.h'.
    :param stream_id:
    :return:
    """
    return stream_id >> 11 & 1 == 1


# getting your message as int
# i = int("140900793d002327", 16)
# getting bit at position 28 (counting from 0 from right)
# i >> 28 & 1
# getting bits at position 24-27
# bin(i >> 24 & 0b111)


def get_time(time_format: TimeFormat, bits: bin):
    if time_format == TimeFormat.CFE_SB_TIME_32_16_SUBS:
        seconds, = unpack('I', bits[:4])

    return str(seconds)


def get_packet_type(stream_id: int):
    """
    Get the type of packet this message is; it could be a telemetry packet or command packet.
    The definition for command and telemetry packet can be found on airliner's codebase at
    [1].
    [1]:https://github.com/WindhoverLabs/airliner/blob/develop/core/cfe/fsw/src/inc/ccsds.h#L92
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


# FIXME:Ignore ccsds headers. Move this function to another function where the get_struct_format_string gets called along with this function
def get_field_names_from_struct(symbol_id: int, db_handle: sqlite_utils.Database):
    field_labels = []
    for record in list(db_handle['fields'].rows_where('symbol=?', [symbol_id], order_by='byte_offset')):
        field_labels.append(record['name'])

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


def write_command_row_to_csv(message_macro: str, command_code: int, message_id: int, symbol_name: str, fields: list, filed_values: tuple,
                               time_in_seconds: int):
    file_name = message_macro + '_cc' + str(command_code) + '.csv'
    my_file = Path(file_name)
    does_file_exist = (my_file.exists() and my_file.is_file())

    with open(file_name, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)

        if does_file_exist is False:
            writer.writerow(['message_id', 'time in seconds', 'symbol_name'] + fields)

        writer.writerow([message_id, time_in_seconds, symbol_name] + list(filed_values))


def get_symbol_name(symbol_id: int, db_handle: sqlite_utils.Database):
    symbol_name = list(db_handle['symbols'].rows_where('id=?', [symbol_id]))[0]['name']
    return symbol_name


def get_symbol_id_from_message_id(message_id: int, db_handle: sqlite_utils.Database) -> dict:
    """
    Returns the symbol id that is mapped to message_id.
    :return:
    """
    symbol_key = list(db_handle['telemetry'].rows_where('message_id=?', [message_id]))[0]['symbol']
    return symbol_key


def get_telemetry_message_macro(message_id: int, db_handle: sqlite_utils.Database):
    macro = list(db_handle['telemetry'].rows_where('message_id=?', [message_id]))[0]['macro']

    return macro


def get_command_code(command_header: int):
    return command_header << 8 & 0XFF00

# FIXME: Cleanup code


def parse_file(file_path: str, sqlite_path: str, structures: [str], time_format: TimeFormat):
    """
    Parses the file at file_path, extracts all data from it and outputs it into a csv.
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

    structure = list(db['symbols'].rows_where('name=?', [structures[0]]))[0]

    structure_data = bytes_buffer[64:140]

    print(f'expected number of bytes:{calcsize("IIHH64B")}')

    content_type, sub_type, header_length, spacecraft_id, processor_id, application_id, time_seconds, time_subseconds, description \
        = unpack('!IIIIIIII32s', bytes_buffer[:64])

    close_seconds, close_subseconds, file_table_index, file_name_type, file_name = unpack('!IIHH64s', structure_data)

    print(f'stuff:{(close_seconds, close_subseconds, file_table_index, file_name_type, file_name)}')

    print(f'stuff2-->content_type:{sub_type}')
    file_header_size = 0
    for structure in structures:
        file_header_size += list(db['symbols'].rows_where('name=?', [structure]))[0]['byte_size']

    message_data = bytes_buffer[file_header_size:]

    current_message_index = 0
    number_of_messages = len(message_data)

    message_ids = set()
    struct_string = None
    struct_size = 0
    symbol_id = None

    # These map works like a cache for our symbols so we don't have to have redundant queries that slow down our code
    telemetry_symbol_map = {}
    commands_symbol_map = {}

    symbol_field_labels = None
    time_in_seconds = 0

    ccsds_header_length = 0

    while current_message_index < file_size - file_header_size:
        # We assume that the primary header is always a ccsds primary header
        primary_header = message_data[current_message_index: current_message_index + 6]
        stream_id, squence, length = unpack('!HHH', primary_header)

        if get_packet_type(stream_id) == PacketType.TELEMETRY:
            ccsds_header_length = 6
            if is_secondary_header_present(stream_id):
                secondary_header = message_data[current_message_index + 6: current_message_index + 12]
                ccsds_header_length = 12
                time_in_seconds = get_time(time_format, secondary_header)

            # Keep track of previous message ids to optimize; otherwise the script could take minutes to finish
            if not (stream_id in telemetry_symbol_map):
                #FIXME:For commands, get the symbol by command code AND message id
                symbol_id = get_symbol_id_from_message_id(stream_id, db)
                symbol_name = get_symbol_name(symbol_id, db)
                struct_string = get_struct_format_string(symbol_id, ccsds_header_length , db)
                symbol_field_labels = get_field_names_from_struct(symbol_id, db)
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
            current_message_index += ccsds_header_length

            write_telemetry_row_to_csv(telemetry_symbol_map[stream_id]['message_macro'] ,stream_id,
                                       telemetry_symbol_map[stream_id]['symbol_name'],
                                       telemetry_symbol_map[stream_id]['symbol_field_labels'],
                                       unpack(telemetry_symbol_map[stream_id]['struct_string'],
                                              message_data[current_message_index:current_message_index +
                                                                                 telemetry_symbol_map[stream_id][
                                                                                     'struct_size']]),
                                       time_in_seconds)

            current_message_index += telemetry_symbol_map[stream_id]['struct_size']


        # FIXME: Commands have not been verified yet
        elif get_packet_type(stream_id) == PacketType.COMMAND:
            ccsds_header_length = 6
            if is_secondary_header_present(stream_id):
                command_secondary_header = message_data[current_message_index + 6: current_message_index + 8]
                ccsds_header_length = 8
                command, = unpack('H', command_secondary_header)
                command_code = get_command_code(command)
            if not (stream_id in telemetry_symbol_map):
                symbol_id = get_symbol_id_from_message_id(stream_id, db)
                symbol_name = get_symbol_name(symbol_id, db)
                struct_string = get_struct_format_string(symbol_id, db)
                symbol_field_labels = get_field_names_from_struct(symbol_id, db)
                struct_size = calcsize(struct_string)
                message_macro = get_telemetry_message_macro(stream_id, db)

                # NOTE: Please note that symbol and struct are synonyms in this context; they mean the same thing.
                commands_symbol_map.update({(stream_id, command_code):
                                                 {'symvol_id': symbol_id,
                                                  'struct_string': struct_string,
                                                  'symbol_field_labels': symbol_field_labels,
                                                  'struct_size': struct_size,
                                                  'symbol_name': symbol_name,
                                                  'message_macro': message_macro,
                                                  'command_code': command_code}
                                             })
            current_message_index += ccsds_header_length

            write_command_row_to_csv(commands_symbol_map[stream_id]['message_macro'] ,stream_id,
                                       commands_symbol_map[stream_id]['symbol_name'],
                                       commands_symbol_map[stream_id]['symbol_field_labels'],
                                       unpack(telemetry_symbol_map[stream_id]['struct_string'],
                                              message_data[current_message_index:current_message_index +
                                                                                 commands_symbol_map[stream_id][
                                                                                     'struct_size']]),
                                       time_in_seconds)

            current_message_index += commands_symbol_map[stream_id]['struct_size']


        message_ids.add(stream_id)

        # print(f'Streamid:{stream_id}')

        # print(f'current_message_index:{current_message_index}')


str_to_time_enum = \
    {
        'CFE_SB_TIME_32_16_SUBS': TimeFormat.CFE_SB_TIME_32_16_SUBS,
        'CFE_SB_TIME_32_32_SUBS': TimeFormat.CFE_SB_TIME_32_32_SUBS,
        'CFE_SB_TIME_32_32_M_20': TimeFormat.CFE_SB_TIME_32_32_M_20
    }


def parse_cli() -> argparse.Namespace:
    """
    Parses cli argyments.
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

    return parser.parse_args()


def main():
    args = parse_cli()

    yaml_structs = read_yaml(args.structures_yaml)
    parse_file(args.input_file, args.sqlite_path, get_structure_names(yaml_structs), str_to_time_enum[args.time_format])


if __name__ == '__main__':
    main()
