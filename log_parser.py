""""
Reads in a binary file created by the ds application.
"""
import argparse
import sqlite_utils
import yaml
from struct import pack, unpack, calcsize
import csv
from enum import Enum


class TimeFornat(Enum):
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


def map_structure_to_fields():
    pass


def is_secondary_header_present(stream_id: int):
    """
    Checks if the secondary header is present. How this is checked is documented by 'ccsds.h'
    on the airliner codebase at 'airliner/core/cfe/fsw/src/inc/ccsds.h'.
    :param stream_id:
    :return:
    """
    return bin(stream_id)[11] == '1'


def get_time(time_format: TimeFornat, bits:bin):
    if time_format == TimeFornat.CFE_SB_TIME_32_16_SUBS:
        seconds = int(bits[:32])

    return str(seconds)


def get_packet_type(stream_id: int):
    """
    Get the type of packet this message is; it could be a telemetry packet or command packet.
    The definition for command and telemetry packet can be found on airliner's codebase at
    'airliner/core/cfe/fsw/src/inc/ccsds.h'
    :param stream_id:
    :return:
    """
    packet_type_stream =  bin(stream_id)
    return PacketType.TELEMETRY if bin(stream_id)[12]==0 else PacketType.COMMAND



def parse_file(file_path: str, sqlite_path: str, structures: [str], time_format: TimeFornat):
    db = sqlite_utils.Database(sqlite_path)
    f = open(file_path, "rb")
    bytes_buffer = f.read()

    structure = list(db['symbols'].rows_where('name=?', [structures[0]]))[0]

    struct_fields = list(db['fields'].rows_where('symbol=?', [structure['id']], order_by='byte_offset'))

    struct_size = structure['byte_size']

    structure_data = bytes_buffer[64:140]

    print(f'expected number of bytes:{calcsize("IIHH64B")}')

    content_type, sub_type, header_length, spacecraft_id, processor_id, application_id, time_seconds, time_subseconds, description\
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

    for message in range(int(len(message_data)/12)):
        primary_header = message_data[current_message_index: current_message_index + 6]
        stream_id, squence, length = unpack('!HHH', primary_header)
        if get_packet_type(stream_id) == PacketType.TELEMETRY:
            if is_secondary_header_present(stream_id):
                print(f'time on packet:{get_time}')

                # Fetch secondary header


            print(f'ccsds header:{(stream_id, squence, length)}')

            current_message_index += 12
        else:
            current_message_index += 12


str_to_time_enum = \
    {
        'CFE_SB_TIME_32_16_SUBS': TimeFornat.CFE_SB_TIME_32_16_SUBS,
        'CFE_SB_TIME_32_32_SUBS': TimeFornat.CFE_SB_TIME_32_32_SUBS,
        'CFE_SB_TIME_32_32_M_20': TimeFornat.CFE_SB_TIME_32_32_M_20
    }

def parse_cli() -> argparse.Namespace:
    """
    Parses cli argyments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in paths to yaml file and sqlite database.')
    parser.add_argument('--structures_yaml', type=str,
                        help='The file path to the YAML file which contains the names of the structures that come before'
                             'the telemetry data. Please note that the order in which the structures are defined in the '
                             'yaml file matters.',
                        required=True)
    parser.add_argument('--sqlite_path', type=str,
                        help='The file path to the sqlite database', required=True)

    parser.add_argument('--input_file', type=str,
                        help='The file path to the file that contains the telemetry/command data.', required=True)

    parser.add_argument('--time_format', type=str, default='CFE_SB_TIME_32_16_SUBS',
                        choices=['CFE_SB_TIME_32_16_SUBS', 'CFE_SB_TIME_32_32_SUBS'
                                 'CFE_SB_TIME_32_32_M_20'],
                        help='The time format for the ccsds header.')


    return parser.parse_args()

def main():
    args = parse_cli()

    yaml_structs = read_yaml(args.structures_yaml)
    parse_file(args.input_file, args.sqlite_path, get_structure_names(yaml_structs), str_to_time_enum[args.time_format])


if __name__ == '__main__':
    main()