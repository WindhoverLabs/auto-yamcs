from xml.etree import ElementTree as ET
import src.xtce_generator.xtce as xtce
import argparse
import sqlite3
from enum import Enum


class BaseType(int, Enum):
    """
    Used by XTCEManager to distinguish what kind of argument or parameter types to add to Space Systems.
    This is especially useful for adding base(or instrinsic) types to a space system.
    """
    INTEGER = 0
    STRUCT = 1
    CHAR = 2


class XTCEManager:
    def __init__(self, root_space_system: str, file_path: str):
        """
        Instantiates a XTCEManager instance. An XTCEManager is a class that manages a xtce class internally
        and provides utilities such as serialization tools(through the write_to_file method) and a functionality
        to add namespaces, basetypes, etc to our spacesystem.
        :param root_space_system:
        :param file_path:
        """
        self.root = xtce.SpaceSystemType(name=root_space_system)
        self.telemetry_metadata = xtce.TelemetryMetaDataType()
        self.command_metadata = xtce.CommandMetaDataType()
        self.paramter_type_set = xtce.ParameterTypeSetType()
        self.output_file = open(file_path, 'w+')

        self.telemetry_metadata.set_ParameterTypeSet(self.paramter_type_set)
        self.root.set_TelemetryMetaData(self.telemetry_metadata)
        self.root.set_CommandMetaData(self.command_metadata)

    @staticmethod
    def get_param_type(symbol: tuple, is_little_endian: bool) -> tuple((xtce.BaseDataType, BaseType)):
        """
        Constructs and returns a *ParameterType, which may be of StringDataType or IntegerDataType,
        based on the information gathered from symbol.
        :param is_little_endian:
        :param symbol: a symbol record in the database. Note the symbol is assumed to be in the form of
        (id, module, name, byte_size)
        :return: A tuple of the form (*ParamType, BaseType).
        """
        symbol_name = symbol[2]
        symbol_bit_size = str(int(symbol[3]) * 8)
        param_type = None
        base_type_name = None
        base_type_data_encoding = None
        base_type_encoding = None
        base_type = None

        # size_in_bits for strings
        size_in_bits = None

        base_type_bit_order = xtce.BitOrderType.LEAST_SIGNIFICANT_BIT_FIRST if is_little_endian \
            else xtce.BitOrderType.MOST_SIGNIFICANT_BIT_FIRST
        base_type_byte_order = xtce.ByteOrderCommonType.LEAST_SIGNIFICANT_BYTE_FIRST if is_little_endian \
            else xtce.ByteOrderCommonType.MOST_SIGNIFICANT_BYTE_FIRST

        if symbol_name == 'int' or symbol_name == 'short int' or symbol_name == 'long int' \
                or symbol_name == 'long long int':
            base_type_name = symbol_name + symbol_bit_size + '_t_' + 'LE' if is_little_endian else 'BE'
            param_type = xtce.IntegerParameterType(name=base_type_name, signed=True)

            base_type_data_encoding = xtce.IntegerDataEncodingType(sizeInBits=symbol_bit_size,
                                                                   bitOrder=base_type_bit_order,
                                                                   byteOrder=base_type_byte_order,
                                                                   encoding=xtce.IntegerEncodingType.TWOS_COMPLEMENT
                                                                   )
            param_type.set_IntegerDataEncoding(base_type_data_encoding)
            base_type = BaseType.INTEGER

        elif symbol_name == 'unsigned int' or symbol_name == 'short unsigned int' or symbol_name == 'long unsigned int' \
                or symbol_name == 'long long unsigned int':
            base_type_name = symbol_name + symbol_bit_size + '_t_' + 'LE' if is_little_endian else 'BE'
            param_type = xtce.IntegerParameterType(name=base_type_name, signed=False)

            base_type_data_encoding = xtce.IntegerDataEncodingType(sizeInBits=symbol_bit_size,
                                                                   bitOrder=base_type_bit_order,
                                                                   byteOrder=base_type_byte_order,
                                                                   encoding=xtce.IntegerEncodingType.UNSIGNED)

            base_type_data_encoding.set_encoding('unsigned')
            param_type.set_IntegerDataEncoding(base_type_data_encoding)

            base_type = BaseType.INTEGER

        elif symbol_name == 'int8_t' or \
                symbol_name == 'int16_t' or \
                symbol_name == 'int32_t' or \
                symbol_name == 'int64_t':

            base_type_name = symbol_name + '_' + 'LE' if is_little_endian else 'BE'
            param_type = xtce.IntegerParameterType(name=base_type_name, signed=True)

            base_type_data_encoding = xtce.IntegerDataEncodingType(sizeInBits=symbol_bit_size,
                                                                   bitOrder=base_type_bit_order,
                                                                   byteOrder=base_type_byte_order,
                                                                   encoding=xtce.IntegerEncodingType.TWOS_COMPLEMENT
                                                                   )
            param_type.set_IntegerDataEncoding(base_type_data_encoding)
            base_type = BaseType.INTEGER

        elif symbol_name == 'uint8_t' or \
                symbol_name == 'uint16_t' or \
                symbol_name == 'uint64_t' or \
                symbol_name == 'uint64_t':

            base_type_name = symbol_name + '_' + 'LE' if is_little_endian else 'BE'
            param_type = xtce.IntegerParameterType(name=base_type_name, signed=False)

            base_type_data_encoding = xtce.IntegerDataEncodingType(sizeInBits=symbol_bit_size,
                                                                   bitOrder=base_type_bit_order,
                                                                   byteOrder=base_type_byte_order,
                                                                   encoding=xtce.IntegerEncodingType.UNSIGNED
                                                                   )
            param_type.set_IntegerDataEncoding(base_type_data_encoding)
            base_type = BaseType.INTEGER


        elif symbol_name == 'char':
            base_type_name = symbol_name + symbol_bit_size + '_t_' + 'LE' if is_little_endian else 'BE'
            param_type = xtce.StringParameterType(name=base_type_name)
            size_in_bits = xtce.SizeInBitsType(xtce.FixedType(FixedValue=int(symbol_bit_size)))

            base_type_data_encoding = xtce.StringDataEncodingType(SizeInBits=size_in_bits,
                                                                  bitOrder=base_type_bit_order,
                                                                  byteOrder=base_type_byte_order,
                                                                  encoding=xtce.StringEncodingType.UTF_8
                                                                  )
            param_type.set_StringDataEncoding(base_type_data_encoding)
            base_type = BaseType.CHAR

        elif symbol_name == 'signed char':
            base_type_name = 'char8_t_' + 'LE' if is_little_endian else 'BE'
            param_type = xtce.IntegerParameterType(name=base_type_name, signed=True)

            base_type_data_encoding = xtce.IntegerDataEncodingType(sizeInBits=symbol_bit_size,
                                                                   bitOrder=base_type_bit_order,
                                                                   byteOrder=base_type_byte_order,
                                                                   # Not sure if we need this TWOS_COMPLEMENT encoding
                                                                   encoding=xtce.IntegerEncodingType.TWOS_COMPLEMENT
                                                                   )
            param_type.set_IntegerDataEncoding(base_type_data_encoding)
            base_type = BaseType.INTEGER

        elif symbol_name == 'unsigned char':
            base_type_name = 'uchar8_t_' + 'LE' if is_little_endian else 'BE'
            param_type = xtce.IntegerParameterType(name=base_type_name, signed=False)

            base_type_data_encoding = xtce.IntegerDataEncodingType(sizeInBits=symbol_bit_size,
                                                                   bitOrder=base_type_bit_order,
                                                                   byteOrder=base_type_byte_order,
                                                                   # Not sure if we need this TWOS_COMPLEMENT encoding
                                                                   encoding=xtce.IntegerEncodingType.TWOS_COMPLEMENT
                                                                   )
            param_type.set_IntegerDataEncoding(base_type_data_encoding)
            base_type = BaseType.INTEGER

        return param_type, base_type

    def add_base_types(self, db_cursor: sqlite3.Cursor, telemetry_metadata: xtce.TelemetryMetaDataType):
        """
        Get all base types from the database and add it to telemetry_metadata.
        This function adds a ParamaterTypeSet to telemetry_metadata. It is assumed that telemetry_metadata has no
        ParameterTypeSet.
        :param self:
        :param db_cursor:
        :param telemetry_metadata:
        :return:
        """
        base_set = xtce.ParameterTypeSetType()

        base_set.get_IntegerParameterType()

        for symbol in db_cursor.execute('SELECT * FROM symbols').fetchall():
            symbol_base_type = self.get_param_type(symbol, True)
            param_type = symbol_base_type[0]
            base_type = symbol_base_type[1]

            if not (param_type is None):
                # If our base_type is an integer and param_type does NOT exist in this set, we add it.
                #TODO: We need to compare each parameter type based on solely on the name
                if base_type == BaseType.INTEGER and not(param_type in base_set.get_IntegerParameterType() +
                                                         base_set.get_StringParameterType()):
                    base_set.add_IntegerParameterType(param_type)
                elif base_type == BaseType.CHAR and not (param_type in base_set.get_IntegerParameterType() +
                                                         base_set.get_StringParameterType() ):
                    base_set.add_StringParameterType(param_type)

        telemetry_metadata.set_ParameterTypeSet(base_set)

    def add_namespace(self, namespace_name: str):
        self.root.add_SpaceSystem(namespace_name)

    def write_to_file(self):
        """
        Writes the current xtce spacesystem to a file.
        :return:
        """
        self.root.export(self.output_file, 0)


def parse_cli() -> argparse.Namespace:
    """
    Parses cli argyments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in path to sqlite database.')
    parser.add_argument('--sqlite_path', type=str,
                        help='The file path to the sqlite database', required=True)
    parser.add_argument('--spacesystem', type=str, default='airliner',
                        help='The name of the root spacesystem of the xtce file. Note that spacesystem is a synonym '
                             'for namespace')

    return parser.parse_args()


def main():
    args = parse_cli()
    db_handle = sqlite3.connect(args.sqlite_path)
    db_cursor = db_handle.cursor()

    xtce_obj = XTCEManager(args.spacesystem, 'new_xml.xml')
    xtce_obj.add_base_types(db_cursor, xtce_obj.telemetry_metadata)
    xtce_obj.write_to_file()


if __name__ == '__main__':
    main()
