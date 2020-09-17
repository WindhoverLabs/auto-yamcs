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
    STRING = 2


class XTCEManager:
    def __init__(self, root_space_system: str, file_path: str):
        """
        Instantiates a XTCEManager instance. An XTCEManager is a class that manages a xtce class internally
        and provides utilities such as serialization tools(through the write_to_file method) and a functionality
        to add namespaces, BaseType, etc to our root spacesystem.
        :param root_space_system:
        :param file_path:
        """
        self.root = xtce.SpaceSystemType(name=root_space_system)
        self.telemetry_metadata = xtce.TelemetryMetaDataType()
        self.command_metadata = xtce.CommandMetaDataType()
        self.paramter_type_set = xtce.ParameterTypeSetType()
        self.output_file = open(file_path + '.xml', 'w+')

        self.telemetry_metadata.set_ParameterTypeSet(self.paramter_type_set)
        self.root.set_TelemetryMetaData(self.telemetry_metadata)
        self.root.set_CommandMetaData(self.command_metadata)

        self.__namespace_dict = dict({root_space_system: self.root})

    def __get_int_paramtype(self, bit_size: int, little_endian: bool) -> xtce.IntegerDataType:
        """
        Factory function to construct a IntegerParameterType.
        :param bit_size:
        :param little_endian:
        :return:
        """
        base_type_name = 'int' + str(bit_size) + ('_LE' if little_endian else '_BE')

        param_type = xtce.IntegerParameterType(name=base_type_name, signed=True)
        bit_size = bit_size
        bit_order = xtce.BitOrderType.LEAST_SIGNIFICANT_BIT_FIRST if little_endian else \
            xtce.BitOrderType.MOST_SIGNIFICANT_BIT_FIRST

        byte_order = xtce.ByteOrderCommonType.LEAST_SIGNIFICANT_BYTE_FIRST if little_endian else \
            xtce.ByteOrderCommonType.MOST_SIGNIFICANT_BYTE_FIRST

        base_type_data_encoding = xtce.IntegerDataEncodingType(sizeInBits=bit_size,
                                                               bitOrder=bit_order,
                                                               byteOrder=byte_order,
                                                               encoding=xtce.IntegerEncodingType.TWOS_COMPLEMENT
                                                               )

        param_type.set_IntegerDataEncoding(base_type_data_encoding)

        return param_type

    def __get_int_argtype(self, bit_size: int, little_endian: bool) -> xtce.IntegerDataType:
        """
        Factory function to construct a IntegerArgumentType.
        :param bit_size:
        :param little_endian:
        :return:
        """
        base_type_name = 'int' + str(bit_size) + ('_LE' if little_endian else '_BE')

        arg_type = xtce.IntegerArgumentType(name=base_type_name, signed=True)
        bit_size = bit_size
        bit_order = xtce.BitOrderType.LEAST_SIGNIFICANT_BIT_FIRST if little_endian else \
            xtce.BitOrderType.MOST_SIGNIFICANT_BIT_FIRST

        byte_order = xtce.ByteOrderCommonType.LEAST_SIGNIFICANT_BYTE_FIRST if little_endian else \
            xtce.ByteOrderCommonType.MOST_SIGNIFICANT_BYTE_FIRST

        base_type_data_encoding = xtce.IntegerDataEncodingType(sizeInBits=bit_size,
                                                               bitOrder=bit_order,
                                                               byteOrder=byte_order,
                                                               encoding=xtce.IntegerEncodingType.TWOS_COMPLEMENT
                                                               )

        arg_type.set_IntegerDataEncoding(base_type_data_encoding)

        return arg_type

    def __get_uint_paramtype(self, bit_size: int, little_endian: bool) -> xtce.IntegerDataType:
        """
        Factory function to construct a IntegerParameterType.
        :param bit_size:
        :param little_endian:
        :return:
        """
        base_type_name = 'uint' + str(bit_size) + ('_LE' if little_endian else '_BE')

        param_type = xtce.IntegerParameterType(name=base_type_name, signed=False)
        bit_size = bit_size
        bit_order = xtce.BitOrderType.LEAST_SIGNIFICANT_BIT_FIRST if little_endian else \
            xtce.BitOrderType.MOST_SIGNIFICANT_BIT_FIRST

        byte_order = xtce.ByteOrderCommonType.LEAST_SIGNIFICANT_BYTE_FIRST if little_endian else \
            xtce.ByteOrderCommonType.MOST_SIGNIFICANT_BYTE_FIRST

        base_type_data_encoding = xtce.IntegerDataEncodingType(sizeInBits=bit_size,
                                                               bitOrder=bit_order,
                                                               byteOrder=byte_order,
                                                               encoding=xtce.IntegerEncodingType.UNSIGNED
                                                               )

        param_type.set_IntegerDataEncoding(base_type_data_encoding)

        return param_type

    def __get_float_paramtype(self, bit_size: int, little_endian: bool) -> xtce.FloatDataType:
        """
        Factory function to construct a IntegerParameterType.
        :param bit_size:
        :param little_endian:
        :return:
        """
        base_type_name = 'float' + str(bit_size) + ('_LE' if little_endian else '_BE')
        bit_size = bit_size
        bit_order = xtce.BitOrderType.LEAST_SIGNIFICANT_BIT_FIRST if little_endian else \
            xtce.BitOrderType.MOST_SIGNIFICANT_BIT_FIRST

        byte_order = xtce.ByteOrderCommonType.LEAST_SIGNIFICANT_BYTE_FIRST if little_endian else \
            xtce.ByteOrderCommonType.MOST_SIGNIFICANT_BYTE_FIRST

        encoding = xtce.FloatDataEncodingType(sizeInBits=str(bit_size),
                                              bitOrder=bit_order,
                                              byteOrder=byte_order)

        param_type = xtce.FloatDataType(name=base_type_name, sizeInBits=str(bit_size))
        param_type.set_FloatDataEncoding(encoding)

        return param_type

    def __add_telemetry_base_types(self):
        """
        Adds all supported base types for our ground system to the TelemetryMetaData element of
        the namespace 'BaseType', which is created to hold all of the base types. Base types are the types tha are not
        user-defined such as int16, int32, etc. Check our docs for more details on base types. Please note that these
        base types are stored as *ParameterTypes on the xtce.
        :return:
        """
        base_set = xtce.ParameterTypeSetType()
        base_space_system = self['BaseType']
        base_space_system.set_TelemetryMetaData(xtce.TelemetryMetaDataType())

        # Add int types
        for bit in range(1, 65):
            if bit > 1:
                base_set.add_IntegerParameterType(self.__get_int_paramtype(bit, True))
                base_set.add_IntegerParameterType(self.__get_int_paramtype(bit, False))

            base_set.add_IntegerParameterType(self.__get_uint_paramtype(bit, True))
            base_set.add_IntegerParameterType(self.__get_uint_paramtype(bit, False))

        # NOTE: For right now, only singed little-endian 32-bit floating types are supported
        # Add floating types
        base_set.add_FloatParameterType(self.__get_float_paramtype(32, True))

        # Add char types
        # #FIXME: We have to decide what to do about strings
        # for bit in range(1, 160):
        #     # Add big Endian
        #     base_type_name = 'char' + str(bit)
        #     param_type = xtce.StringParameterType(name=base_type_name, signed=True)
        #     bit_size = bit
        #
        #     base_type_data_encoding = xtce.StringDataEncodingType(
        #         byteOrder=xtce.ByteOrderCommonType.MOST_SIGNIFICANT_BYTE_FIRST
        #         if bit < 8
        #         else xtce.ByteOrderCommonType.LEAST_SIGNIFICANT_BYTE_FIRST,
        #         SizeInBits=xtce.SizeInBitsType(Fixed=xtce.FixedType(FixedValue=bit)))
        #
        #     param_type.set_StringDataEncoding(base_type_data_encoding)
        #
        #     base_set.add_IntegerParameterType(param_type)

        base_space_system.get_TelemetryMetaData().set_ParameterTypeSet(base_set)

    def __add_commands_base_types(self):
        """
        Adds all supported base types for our ground system to the CommandMetaData element of
        the namespace 'BaseType', which is created to hold all of the base types. Base types are the types tha are not
        user-defined such as int16, int32, etc. Check our docs for more details on base types. Please note that these
        base types are stored as *ArgumentTypes on the xtce.
        :return:
        """
        base_set = xtce.ArgumentTypeSetType()
        base_space_system = self['BaseType']
        base_space_system.set_CommandMetaData(xtce.CommandMetaDataType())

        # Add int types
        for bit in range(1, 65):
            if bit > 1:
                base_set.add_IntegerArgumentType(self.__get_int_argtype(bit, True))
                # base_set.add_IntegerArgumentType(self.__get_int_paramtype(bit, False))

            # base_set.add_IntegerParameterType(self.__get_uint_paramtype(bit, True))
            # base_set.add_IntegerParameterType(self.__get_uint_paramtype(bit, False))

        # NOTE: For right now, only singed little-endian 32-bit floating types are supported
        # Add floating types
        # base_set.add_FloatParameterType(self.__get_float_paramtype(32, True))

        # Add char types
        # #FIXME: We have to decide what to do about strings
        # for bit in range(1, 160):
        #     # Add big Endian
        #     base_type_name = 'char' + str(bit)
        #     param_type = xtce.StringParameterType(name=base_type_name, signed=True)
        #     bit_size = bit
        #
        #     base_type_data_encoding = xtce.StringDataEncodingType(
        #         byteOrder=xtce.ByteOrderCommonType.MOST_SIGNIFICANT_BYTE_FIRST
        #         if bit < 8
        #         else xtce.ByteOrderCommonType.LEAST_SIGNIFICANT_BYTE_FIRST,
        #         SizeInBits=xtce.SizeInBitsType(Fixed=xtce.FixedType(FixedValue=bit)))
        #
        #     param_type.set_StringDataEncoding(base_type_data_encoding)
        #
        #     base_set.add_IntegerParameterType(param_type)

        base_space_system.get_CommandMetaData().set_ArgumentTypeSet(base_set)

    def add_base_types(self):
        """
        Create a namespace BaseType and add all base types to it. Please refer to the docs for how we define a base type
        in our ground system.
        :return:
        """
        self.add_namespace('BaseType')
        self.__add_telemetry_base_types()
        self.__add_commands_base_types()


    def __get_aggregate_paramtype(self, telemetry_id:str, db_cursor: sqlite3.Cursor, ):
        """
        Add a new telemetry container with the name of telemetry_id.
        :param telemetry_id:
        :return:
        """
    #     FIXME: Implement


    def add_namespace(self, namespace_name: str):
        """
        Add a namespace to the root SpaceSystem. Please note that namespace is a synonym for SpaceSystem;
        they are the same thing in the xtce-speak.
        :param namespace_name: The name of the new namespace.
        :return:
        """
        new_namespace = xtce.SpaceSystemType(name=namespace_name)
        self.root.add_SpaceSystem(new_namespace)

        self.__namespace_dict[namespace_name] = new_namespace

    def get_namespace(self, namespace_name: str) -> xtce.SpaceSystemType:
        """
        Returns a namespace SpaceSystemType object that has the name of namespace_name.
        :param namespace_name:
        :return:
        """
        return self.__namespace_dict[namespace_name]

    def __getitem__(self, key: str) -> xtce.SpaceSystemType:
        """
        Returns a reference to the namespace with the name of key.
        :param key: The name of the namespace.
        :return:
        """
        return self.get_namespace(key)

    def write_to_file(self):
        """
        Writes the current xtce spacesystem to a file.
        :return:
        """
        self.root.export(self.output_file, 0, namespacedef_='xmlns:xtce="http://www.omg.org/spec/XTCE/20180204"',
                         namespaceprefix_='xtce:')


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

    xtce_obj = XTCEManager(args.spacesystem, args.spacesystem)

    xtce_obj.add_base_types()

    xtce_obj.write_to_file()


if __name__ == '__main__':
    main()
