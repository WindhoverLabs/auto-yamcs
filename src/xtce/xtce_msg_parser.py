"""
Parses messages based on a path such as "/cfs/simlink/apps/to/HK.cmd_cnt"
"""
import math
import struct
from abc import ABC, abstractmethod
from typing import Union, List

from bitarray import bitarray
from bitarray.util import pprint, ba2int, ba2hex
from xtce import xtce, xtce_generator
from xtce.xtce_generator import XTCEManager
from enum import Enum

from pyliner.app import App
import logging

logging.basicConfig(level=logging.INFO)

END = 0xc0
ESC = 0xdb
ESC_END = 0xdc
ESC_ESC = 0xdd


def extract_bits_from_base_container(container: dict, comparison: xtce.ComparisonType, container_size: int) -> bitarray:
    extracted_bits = bitarray(endian='big')
    container_key = list(container[XTCEParser.BASE_CONTAINER_KEY].keys())[0]
    comp_value_ref: str = comparison.get_parameterRef()
    msg_id = int(comparison.get_value())

    # Zero-fill the bitarray up to container size
    for i in range(container_size):
        extracted_bits.insert(i, 0)

    if xtce_generator.XTCEManager.NAMESPACE_SEPARATOR in comp_value_ref:
        comp_value_ref = comp_value_ref.split(xtce_generator.XTCEManager.NAMESPACE_SEPARATOR)[-1]

    offset = get_offset_container(container[XTCEParser.BASE_CONTAINER_KEY][container_key][XTCEParser.PARAMS_KEY],
                                  comp_value_ref)

    value_size = get_param_bit_size(container[XTCEParser.BASE_CONTAINER_KEY][container_key][XTCEParser.PARAMS_KEY],
                                    comp_value_ref)

    # FIXME:hard-coded for now
    length_offset = get_offset_container(container[XTCEParser.BASE_CONTAINER_KEY][container_key][XTCEParser.PARAMS_KEY],
                                         "ccsds-length")
    length_size = get_param_bit_size(container[XTCEParser.BASE_CONTAINER_KEY][container_key][XTCEParser.PARAMS_KEY],
                                     "ccsds-length")

    length_offset += 8

    # A strategy might be just reading these mids from the YAML
    CFE_MSG_CPU_BASE = 0x0200
    CFE_TLM_MID_BASE = 0x0800
    # msg_id = CFE_MSG_CPU_BASE + CFE_TLM_MID_BASE + msg_id
    msg_id = bytearray(struct.pack('>H', msg_id))
    # msg_id[0] = msg_id[0] & 0x0A
    # TODO: Big/Little endian is inside XTCE
    bits = bitarray(endian='big')
    bits.frombytes(bytes(msg_id))

    # FIXME:For some reason, if we start writing in the middle of the byte it zeroes out the header.
    # i = offset
    i = 0
    for bit in bits:
        extracted_bits[i] = bit
        i += 1

    # # TODO: Big/Little endian is inside XTCE
    size_in_bytes = math.ceil(length_size / 8)
    length_bits = bitarray(endian='big')
    # FIXME:CFS-specific logic should go into a post/pre-processor of some kind
    packet_length = int((container_size - 56) / (8))

    packet_length = struct.pack('>H', packet_length)
    length_bits.frombytes(packet_length)

    i = length_offset
    for bit in length_bits[:length_size]:
        extracted_bits[i] = bit
        i += 1

    return extracted_bits


# TODO:Use these inside the dict.
class IntrinsicDataType(Enum):
    INT = 0
    FLOAT = 1
    STRING = 2
    AGGREGATE = 3
    INTRINSIC = 4


# FIXME:Some App(perhaps XTCE_Communication) should watch a directory since these files will be loaded at runtime.
class XTCEParser:
    # FIXME: Maybe make these keys enums to avoid collisions
    PARAMS_KEY = 'params'
    SPACE_SYSTEM_KEY = 'space_system'
    CONTAINERS_KEY = 'containers'
    COMMANDS_KEY = 'commands'
    BASE_CONTAINER_KEY = 'base_container'
    BASE_COMMAND_KEY = 'base_command'
    BASE_CONTAINER_CRITERIA_KEY = 'criteria'
    BASE_COMNMAND_ARG_ASSIGNMENT_KEY = 'criteria'
    XTCE_OBJ_KEY = 'xtce_obj'
    INTRINSIC_KEY = 'intrinsic'
    ARRAY_TYPE_KEY = 'array_type'
    PARAM_NAME_KEY = 'name'
    ARG_NAME_KEY = 'name'
    AGGREGATE_TYPE = 'aggregate'
    OFFSET_KEY = 'offset'
    SIZE_KEY = 'size'
    STRUCT_SEPARATOR = "."
    HOST_PARAM = 'host'
    COMMAND_CONTAINER = "command_container"

    def __init__(self, xml_files: [str], root_space_system: str):
        # # Code should be inherited from XTCEManager. See https://github.com/WindhoverLabs/xtce_generator/issues/5
        self.high_level_roots = []
        self.root = xtce.parse(root_space_system, silence=True)
        self.high_level_roots.append(self.root)

        for file in xml_files:
            logging.info(f"Parsing:{file}")
            xtce_obj = xtce.parse(file, silence=True)
            self.root.add_SpaceSystem(xtce_obj)
            self.high_level_roots.append(xtce_obj)

        names: [str] = []
        self.__namespace_dict = {}
        self.__map_all_spacesystems(self.root, names)
        self.__map_all_containers()

    def set_qualified_names(self, root: xtce.SpaceSystemType, parent: str):
        q_name = ""
        if parent == xtce_generator.XTCEManager.NAMESPACE_SEPARATOR:
            q_name = xtce_generator.XTCEManager.NAMESPACE_SEPARATOR + root.get_name()
        else:
            q_name = parent + xtce_generator.XTCEManager.NAMESPACE_SEPARATOR + root.get_name()
        p: xtce.ParameterType

        root.set_qualified_name(q_name)
        if root.get_TelemetryMetaData() is not None:
            if root.get_TelemetryMetaData().get_ParameterTypeSet() is not None:
                for p in root.get_TelemetryMetaData().get_ParameterSet().get_Parameter():
                    p.set_qualified_name(root.get_qualified_name()
                                         + xtce_generator.XTCEManager.NAMESPACE_SEPARATOR
                                         + p.get_name()
                                         )

            if root.get_TelemetryMetaData().get_ContainerSet() is not None:
                for c in root.get_TelemetryMetaData().get_ContainerSet().get_SequenceContainer():
                    c.set_qualified_name(root.get_qualified_name()
                                         + xtce_generator.XTCEManager.NAMESPACE_SEPARATOR
                                         + c.get_name()
                                         )
        #        TODO:Add qualifed names for commands as well
        for s in root.get_SpaceSystem():
            self.set_qualified_names(s, s.get_name())

    def get_spacesystems_map(self) -> dict:
        return self.__namespace_dict

    def __child_names_to_qualified_name(self, names: [str]) -> str:
        return xtce_generator.XTCEManager.NAMESPACE_SEPARATOR + xtce_generator.XTCEManager.NAMESPACE_SEPARATOR.join(
            names)

    def __get_seq_containers_map(self, spacesystem: xtce.SpaceSystemType) -> dict:
        containers_dict = {}
        tlm = spacesystem.get_TelemetryMetaData()
        if tlm is not None:
            container_set = spacesystem.get_TelemetryMetaData().get_ContainerSet()
            if container_set is not None:
                container: xtce.SequenceContainerType
                for container in container_set.get_SequenceContainer():
                    containers_dict[container.get_name()] = {}
                    containers_dict[container.get_name()][self.XTCE_OBJ_KEY] = container
                    # container
                    containers_dict[container.get_name()][XTCEParser.PARAMS_KEY] = self.__get_param_map(container,
                                                                                                        spacesystem)
                    if container.get_BaseContainer() is None:
                        containers_dict[container.get_name()][self.BASE_CONTAINER_KEY] = None
                    else:
                        base_container: xtce.SequenceContainerType = self.__get_container_from_ref(
                            container.get_BaseContainer().containerRef, spacesystem)
                        container_spacesystem = self.__get_spacesystem_from_ref(
                            container.get_BaseContainer().containerRef,
                            spacesystem)

                        # containers_dict[container.get_name()][self.BASE_CONTAINER] = {}
                        # # Store Criteria Obj in dict
                        # containers_dict[container.get_name()][self.BASE_CONTAINER][
                        #     self.BASE_CONTAINER_CRITERIA] = container.get_BaseContainer().get_RestrictionCriteria()
                        # containers_dict[container.get_name()][self.BASE_CONTAINER][self.XTCE_OBJ] = base_container
                        containers_dict[container.get_name()][self.BASE_CONTAINER_KEY] = self.__get_seq_containers_map(
                            container_spacesystem)

                        # Store Criteria Obj in dict
                        containers_dict[container.get_name()][self.BASE_CONTAINER_KEY][
                            self.BASE_CONTAINER_CRITERIA_KEY] = container.get_BaseContainer().get_RestrictionCriteria()
                        containers_dict[container.get_name()][self.BASE_CONTAINER_KEY][
                            self.XTCE_OBJ_KEY] = base_container

        return containers_dict

    def __get_meta_commands_map(self, spacesystem: xtce.SpaceSystemType) -> dict:
        commands_dict = {}
        cmd = spacesystem.get_CommandMetaData()
        if cmd is not None:
            meta_command_set: xtce.MetaCommandSetType
            meta_command_set = spacesystem.get_CommandMetaData().get_MetaCommandSet()
            if meta_command_set is not None:
                meta_command: xtce.MetaCommandType
                for meta_command in meta_command_set.get_MetaCommand():
                    commands_dict[meta_command.get_name()] = {}
                    commands_dict[meta_command.get_name()][self.XTCE_OBJ_KEY] = meta_command
                    # container
                    commands_dict[meta_command.get_name()][self.COMMAND_CONTAINER] = meta_command.get_CommandContainer()
                    commands_dict[meta_command.get_name()][XTCEParser.PARAMS_KEY] = self.__get_arg_map(
                        meta_command.get_CommandContainer(),
                        spacesystem)
                    if meta_command.get_BaseMetaCommand() is None:
                        commands_dict[meta_command.get_name()][self.BASE_COMMAND_KEY] = None
                    else:
                        base_container: xtce.MetaCommandType = self.__get_command_from_ref(
                            meta_command.get_BaseMetaCommand().get_metaCommandRef(), spacesystem)
                        container_spacesystem = self.__get_spacesystem_from_ref(
                            meta_command.get_BaseMetaCommand().get_metaCommandRef(),
                            spacesystem)

                        # commands_dict[container.get_name()][self.BASE_CONTAINER] = {}
                        # # Store Criteria Obj in dict
                        # commands_dict[container.get_name()][self.BASE_CONTAINER][
                        #     self.BASE_CONTAINER_CRITERIA] = container.get_BaseContainer().get_RestrictionCriteria()
                        # commands_dict[container.get_name()][self.BASE_CONTAINER][self.XTCE_OBJ] = base_container
                        commands_dict[meta_command.get_name()][
                            self.BASE_COMMAND_KEY] = self.__get_meta_commands_map(
                            container_spacesystem)

                        # Store Criteria Obj in dict
                        commands_dict[meta_command.get_name()][self.BASE_COMMAND_KEY][
                            self.BASE_COMNMAND_ARG_ASSIGNMENT_KEY] = meta_command.get_BaseMetaCommand().get_ArgumentAssignmentList()
                        commands_dict[meta_command.get_name()][self.BASE_COMMAND_KEY][
                            self.XTCE_OBJ_KEY] = base_container

        return commands_dict

    def sanitize_type_ref(self, qualified_name: str):
        """
        Convert a qualified name such as "BaseType/string512_LE" to "string512_LE"
        """
        if xtce_generator.XTCEManager.NAMESPACE_SEPARATOR in qualified_name:
            return qualified_name.split(xtce_generator.XTCEManager.NAMESPACE_SEPARATOR)[-1]
        else:
            return qualified_name

    def __find_child_match(self, child_name, parent: xtce.SpaceSystemType):
        for c in parent.get_SpaceSystem():
            if c.get_name() == child_name:
                return c

    def __get_relative_space_system(self, root: xtce.SpaceSystemType, name: str) -> xtce.SpaceSystemType:
        if root is not None:
            if root.get_name() == name:
                return root
            for s in root.get_SpaceSystem():
                # self.__get_relative_space_system(root.get_parent(), name)
                if s.get_name() == name:
                    return s
                else:
                    match = self.__find_child_match(name, s)
                    if match is not None:
                        return match

            return self.__get_relative_space_system(root.get_parent(), name)

    def __get_closest_parent(self, parent_name: str, child: xtce.SpaceSystemType) -> xtce.SpaceSystemType:
        if child is None:
            return None
        if parent_name == child.get_name():
            return child
        else:
            for c in child.get_SpaceSystem():
                if c.get_name() == parent_name:
                    return c
        return self.__get_closest_parent(parent_name, child.get_parent())

    def __get_deepest_child(self, parent: xtce.SpaceSystemType, space_system_tokens: [str]):
        if len(space_system_tokens) == 1:
            if space_system_tokens[0] == parent.get_name():
                return parent
        else:
            child_name = space_system_tokens[0]
            for c in parent.get_SpaceSystem():
                if c.get_name() == child_name:
                    self.__get_deepest_child(c, space_system_tokens[1:])
                    break

    def __get_intrinsic_parm_type(self, tlm: xtce.TelemetryMetaDataType, param_type_ref: str) -> Union[
        None, xtce.BaseDataType]:
        result = None
        if tlm.get_ParameterTypeSet() is not None:
            if len(tlm.get_ParameterTypeSet().get_IntegerParameterType()) > 0:
                int_type: xtce.IntegerParameterType
                for int_type in tlm.get_ParameterTypeSet().get_IntegerParameterType():
                    if int_type.get_name() == self.sanitize_type_ref(param_type_ref):
                        result = int_type
            if len(tlm.get_ParameterTypeSet().get_FloatParameterType()) > 0:
                for float_type in tlm.get_ParameterTypeSet().get_FloatParameterType():
                    if float_type.get_name() == self.sanitize_type_ref(param_type_ref):
                        result = float_type
            if len(tlm.get_ParameterTypeSet().get_StringParameterType()) > 0:
                for string_type in tlm.get_ParameterTypeSet().get_StringParameterType():
                    if string_type.get_name() == self.sanitize_type_ref(param_type_ref):
                        result = string_type
            if len(tlm.get_ParameterTypeSet().get_EnumeratedParameterType()) > 0:
                for enum_type in tlm.get_ParameterTypeSet().get_EnumeratedParameterType():
                    if enum_type.get_name() == self.sanitize_type_ref(param_type_ref):
                        result = enum_type
            if len(tlm.get_ParameterTypeSet().get_BooleanParameterType()) > 0:
                for boolean_type in tlm.get_ParameterTypeSet().get_BooleanParameterType():
                    if boolean_type.get_name() == self.sanitize_type_ref(param_type_ref):
                        result = boolean_type
        return result

    def __get_spacesystem_from_ref(self, param_ref: str, root: xtce.SpaceSystemType) -> xtce.SpaceSystemType:
        # Only relative references are supported at the moment
        if xtce_generator.XTCEManager.NAMESPACE_SEPARATOR in param_ref:
            space_system_tokens = param_ref.split(xtce_generator.XTCEManager.NAMESPACE_SEPARATOR)[:-1]
            parent = self.__get_closest_parent(space_system_tokens[0], root)
            if len(space_system_tokens) == 1:
                return parent
            else:
                return self.__get_deepest_child(parent, space_system_tokens[:1])
        else:
            # This ref is local to this spacesystem
            return root

    def __get_container_from_ref(self, param_ref: str, root: xtce.SpaceSystemType) -> Union[
        xtce.ContainerType, xtce.SequenceContainerType]:
        # Only relative references are supported at the moment
        s: xtce.SpaceSystemType = self.__get_spacesystem_from_ref(param_ref, root)
        c: xtce.SequenceContainerType
        container_name = param_ref.split(xtce_generator.XTCEManager.NAMESPACE_SEPARATOR)[-1]
        for c in s.get_TelemetryMetaData().get_ContainerSet().get_SequenceContainer():
            if c.get_name() == container_name:
                return c

    def __get_command_from_ref(self, command_ref: str, root: xtce.SpaceSystemType) -> Union[
        xtce.MetaCommandType]:
        # Only relative references are supported at the moment
        s: xtce.SpaceSystemType = self.__get_spacesystem_from_ref(command_ref, root)
        c: xtce.MetaCommandType
        container_name = command_ref.split(xtce_generator.XTCEManager.NAMESPACE_SEPARATOR)[-1]
        for c in s.get_CommandMetaData().get_MetaCommandSet().get_MetaCommand():
            if c.get_name() == container_name:
                return c

    def __get_intrinsic_arg_type(self, cmd: xtce.CommandMetaDataType, arg_type_ref: str) -> Union[
        None, xtce.BaseDataType]:
        result = None
        if cmd.get_ArgumentTypeSet() is not None:
            if len(cmd.get_ArgumentTypeSet().get_IntegerArgumentType()) > 0:
                int_type: xtce.IntegerArgumentType
                for int_type in cmd.get_ArgumentTypeSet().get_IntegerArgumentType():
                    if int_type.get_name() == self.sanitize_type_ref(arg_type_ref):
                        result = int_type
            if len(cmd.get_ArgumentTypeSet().get_FloatArgumentType()) > 0:
                for float_type in cmd.get_ArgumentTypeSet().get_FloatArgumentType():
                    if float_type.get_name() == self.sanitize_type_ref(arg_type_ref):
                        result = float_type
            if len(cmd.get_ArgumentTypeSet().get_StringArgumentType()) > 0:
                for string_type in cmd.get_ArgumentTypeSet().get_StringArgumentType():
                    if string_type.get_name() == self.sanitize_type_ref(arg_type_ref):
                        result = string_type
            if len(cmd.get_ArgumentTypeSet().get_EnumeratedArgumentType()) > 0:
                for enum_type in cmd.get_ArgumentTypeSet().get_EnumeratedArgumentType():
                    if enum_type.get_name() == self.sanitize_type_ref(arg_type_ref):
                        result = enum_type
            if len(cmd.get_ArgumentTypeSet().get_BooleanArgumentType()) > 0:
                for boolean_type in cmd.get_ArgumentTypeSet().get_BooleanArgumentType():
                    if boolean_type.get_name() == self.sanitize_type_ref(arg_type_ref):
                        result = boolean_type
        return result

    # TODO: Get xtce.ParameterType(Aggregate in this case) from spacesystem
    def __get_param_type(self, param_type_ref: str, spacesystem: xtce.SpaceSystemType,
                         host_param: str = None, out_dict: dict = {}):
        """
        For now it is assumed that param_type_ref points to a AggregateParameterType
        """
        tlm = spacesystem.get_TelemetryMetaData()
        if tlm is not None:
            if tlm.get_ParameterTypeSet() is not None:
                param_type = self.__get_intrinsic_parm_type(tlm, param_type_ref)
                if param_type is not None:
                    out_dict[XTCEParser.INTRINSIC_KEY] = param_type
                else:
                    if len(tlm.get_ParameterTypeSet().get_ArrayParameterType()) > 0:
                        array_type: xtce.ArrayParameterType
                        for array_type in tlm.get_ParameterTypeSet().get_ArrayParameterType():
                            if array_type.get_name() == self.sanitize_type_ref(param_type_ref):
                                dim: xtce.DimensionType
                                out_dict[XTCEParser.ARRAY_TYPE_KEY] = []
                                # TODO:Add support for multi-dimensional array
                                for dim in array_type.get_DimensionList().get_Dimension():
                                    for i in range(dim.get_StartingIndex().get_FixedValue(),
                                                   dim.get_EndingIndex().get_FixedValue() + 1):
                                        ref_spacesystem = self.__get_spacesystem_from_ref(array_type.get_arrayTypeRef(),
                                                                                          spacesystem)

                                        item_param_type = self.__get_intrinsic_parm_type(
                                            ref_spacesystem.get_TelemetryMetaData(), array_type.get_arrayTypeRef())
                                        if item_param_type is not None:
                                            out_dict[XTCEParser.ARRAY_TYPE_KEY].append(item_param_type)
                                        else:
                                            # FIXME:Array of structs
                                            out_dict[XTCEParser.ARRAY_TYPE_KEY].append(item_param_type)
                                return
                    if len(tlm.get_ParameterTypeSet().get_AggregateParameterType()) > 0:
                        # FIXME: Check for intrinsic types and make this function recursive
                        aggregate: xtce.AggregateParameterType
                        for aggregate in tlm.get_ParameterTypeSet().get_AggregateParameterType():
                            if self.sanitize_type_ref(param_type_ref) == "CFE_ES_OneAppTlm_t":
                                print("break")
                            if aggregate.get_name() == self.sanitize_type_ref(param_type_ref):
                                member: xtce.MemberType
                                out_dict["fields"] = dict()
                                out_dict[IntrinsicDataType.AGGREGATE] = IntrinsicDataType.AGGREGATE
                                out_dict[XTCEParser.HOST_PARAM] = host_param
                                out_dict[XTCEParser.PARAM_NAME_KEY] = aggregate.get_name()
                                for member in aggregate.get_MemberList().get_Member():
                                    # TODO:Parse fields
                                    out_dict["fields"][member.get_name()] = dict()
                                    out_dict["fields"][member.get_name()][XTCEParser.PARAM_NAME_KEY] = member.get_name()
                                    ref_spacesystem = self.__get_spacesystem_from_ref(member.get_typeRef(), spacesystem)
                                    self.__get_param_type(member.get_typeRef(),
                                                          ref_spacesystem,
                                                          member.get_name(),
                                                          out_dict["fields"][member.get_name()])
                                return

            else:
                for s in spacesystem.get_SpaceSystem():
                    tlm = s.get_TelemetryMetaData()
                    if tlm is not None:
                        if tlm.get_ParameterTypeSet() is not None:
                            param_type = self.__get_intrinsic_parm_type(tlm, param_type_ref)
                            if param_type is not None:
                                out_dict[self.INTRINSIC_KEY] = param_type
                            else:
                                if len(tlm.get_ParameterTypeSet().get_ArrayParameterType()) > 0:
                                    for array_type in tlm.get_ParameterTypeSet().get_ArrayParameterType():
                                        if array_type.get_name() == self.sanitize_type_ref(param_type_ref):
                                            dim: xtce.DimensionType
                                            out_dict[XTCEParser.ARRAY_TYPE_KEY] = []
                                            # TODO:Add support for multi-dimensional array
                                            for dim in array_type.get_DimensionList().get_Dimension():
                                                for i in range(dim.get_StartingIndex().get_FixedValue(),
                                                               dim.get_EndingIndex().get_FixedValue() + 1):
                                                    ref_spacesystem = self.__get_spacesystem_from_ref(
                                                        array_type.get_arrayTypeRef(),
                                                        spacesystem)
                                                    item_param_type = self.__get_intrinsic_parm_type(
                                                        ref_spacesystem.get_TelemetryMetaData(),
                                                        array_type.get_arrayTypeRef())
                                                    if item_param_type is not None:
                                                        out_dict[XTCEParser.ARRAY_TYPE_KEY].append(item_param_type)
                                                    else:
                                                        # FIXME:Array of structs
                                                        out_dict[XTCEParser.ARRAY_TYPE_KEY].append(item_param_type)
                                            return
                                if len(tlm.get_ParameterTypeSet().get_AggregateParameterType()) > 0:
                                    # FIXME: Check for intrinsic types and make this function recursive
                                    aggregate: xtce.AggregateParameterType
                                    for aggregate in tlm.get_ParameterTypeSet().get_AggregateParameterType():
                                        if self.sanitize_type_ref(param_type_ref) == "CFE_ES_OneAppTlm_t":
                                            print("break")
                                        if aggregate.get_name() == self.sanitize_type_ref(param_type_ref):
                                            member: xtce.MemberType
                                            out_dict["fields"] = dict()
                                            out_dict[IntrinsicDataType.AGGREGATE] = IntrinsicDataType.AGGREGATE
                                            out_dict[XTCEParser.PARAM_NAME_KEY] = aggregate.get_name()
                                            out_dict[XTCEParser.HOST_PARAM] = host_param
                                            for member in aggregate.get_MemberList().get_Member():
                                                # TODO:Parse fields
                                                # out_dict[member.get_name()] = dict()
                                                # self.__get_param_type(member.get_typeRef(), spacesystem,
                                                #                       out_dict[member.get_name()])

                                                out_dict["fields"][member.get_name()] = dict()
                                                out_dict["fields"][member.get_name()][
                                                    XTCEParser.PARAM_NAME_KEY] = member.get_name()

                                                ref_spacesystem = self.__get_spacesystem_from_ref(
                                                    member.get_typeRef(), spacesystem)
                                                self.__get_param_type(member.get_typeRef(),
                                                                      ref_spacesystem,
                                                                      member.get_name(),
                                                                      out_dict["fields"][member.get_name()])
                                            return

    # TODO: Get xtce.ParameterType(Aggregate in this case) from spacesystem
    def __get_arg_type(self, param_type_ref: str, spacesystem: xtce.SpaceSystemType,
                       host_param: str = None, out_dict: dict = {}):
        """
        For now it is assumed that param_type_ref points to a AggregateParameterType
        """
        cmd = spacesystem.get_CommandMetaData()
        if cmd is not None:
            if cmd.get_ArgumentTypeSet() is not None:
                arg_type = self.__get_intrinsic_arg_type(cmd, param_type_ref)
                if arg_type is not None:
                    out_dict[XTCEParser.INTRINSIC_KEY] = arg_type
                else:
                    if len(cmd.get_ArgumentTypeSet().get_ArrayArgumentType()) > 0:
                        array_type: xtce.ArrayParameterType
                        for array_type in cmd.get_ArgumentTypeSet().get_ArrayArgumentType():
                            if array_type.get_name() == self.sanitize_type_ref(param_type_ref):
                                dim: xtce.DimensionType
                                out_dict[XTCEParser.ARRAY_TYPE_KEY] = []
                                # TODO:Add support for multi-dimensional array
                                for dim in array_type.get_DimensionList().get_Dimension():
                                    for i in range(dim.get_StartingIndex().get_FixedValue(),
                                                   dim.get_EndingIndex().get_FixedValue() + 1):
                                        ref_spacesystem = self.__get_spacesystem_from_ref(array_type.get_arrayTypeRef(),
                                                                                          spacesystem)

                                        item_param_type = self.__get_intrinsic_parm_type(
                                            ref_spacesystem.get_TelemetryMetaData(), array_type.get_arrayTypeRef())
                                        if item_param_type is not None:
                                            out_dict[XTCEParser.ARRAY_TYPE_KEY].append(item_param_type)
                                        else:
                                            # FIXME:Array of structs
                                            out_dict[XTCEParser.ARRAY_TYPE_KEY].append(item_param_type)
                                return
                    if len(cmd.get_ArgumentTypeSet().get_AggregateArgumentType()) > 0:
                        # FIXME: Check for intrinsic types and make this function recursive
                        aggregate: xtce.AggregateArgumentType
                        for aggregate in cmd.get_ArgumentTypeSet().get_AggregateArgumentType():
                            if aggregate.get_name() == self.sanitize_type_ref(param_type_ref):
                                member: xtce.MemberType
                                out_dict["fields"] = dict()
                                out_dict[IntrinsicDataType.AGGREGATE] = IntrinsicDataType.AGGREGATE
                                out_dict[XTCEParser.HOST_PARAM] = host_param
                                out_dict[XTCEParser.ARG_NAME_KEY] = aggregate.get_name()
                                for member in aggregate.get_MemberList().get_Member():
                                    # TODO:Parse fields
                                    out_dict["fields"][member.get_name()] = dict()
                                    out_dict["fields"][member.get_name()][XTCEParser.ARG_NAME_KEY] = member.get_name()
                                    ref_spacesystem = self.__get_spacesystem_from_ref(member.get_typeRef(), spacesystem)
                                    self.__get_param_type(member.get_typeRef(),
                                                          ref_spacesystem,
                                                          aggregate.get_name(),
                                                          out_dict["fields"][member.get_name()])
                                return

            else:
                for s in spacesystem.get_SpaceSystem():
                    cmd = s.get_CommandMetaData()
                    if cmd is not None:
                        if cmd.get_ArgumentTypeSet() is not None:
                            arg_type = self.__get_intrinsic_arg_type(cmd, param_type_ref)
                            if arg_type is not None:
                                out_dict[self.INTRINSIC_KEY] = arg_type
                            else:
                                if len(cmd.get_ArgumentTypeSet().get_ArrayArgumentType()) > 0:
                                    for array_type in cmd.get_ArgumentTypeSet().get_ArrayArgumentType():
                                        if array_type.get_name() == self.sanitize_type_ref(param_type_ref):
                                            dim: xtce.DimensionType
                                            out_dict[XTCEParser.ARRAY_TYPE_KEY] = []
                                            # TODO:Add support for multi-dimensional array
                                            for dim in array_type.get_DimensionList().get_Dimension():
                                                for i in range(dim.get_StartingIndex().get_FixedValue(),
                                                               dim.get_EndingIndex().get_FixedValue() + 1):
                                                    ref_spacesystem = self.__get_spacesystem_from_ref(
                                                        array_type.get_arrayTypeRef(),
                                                        spacesystem)
                                                    item_param_type = self.__get_intrinsic_parm_type(
                                                        ref_spacesystem.get_TelemetryMetaData(),
                                                        array_type.get_arrayTypeRef())
                                                    if item_param_type is not None:
                                                        out_dict[XTCEParser.ARRAY_TYPE_KEY].append(item_param_type)
                                                    else:
                                                        # FIXME:Array of structs
                                                        out_dict[XTCEParser.ARRAY_TYPE_KEY].append(item_param_type)
                                            return
                                if len(cmd.get_ArgumentTypeSet().get_AggregateArgumentType()) > 0:
                                    # FIXME: Check for intrinsic types and make this function recursive
                                    aggregate: xtce.AggregateArgumentType
                                    for aggregate in cmd.get_ArgumentTypeSet().get_AggregateArgumentType():

                                        if aggregate.get_name() == self.sanitize_type_ref(param_type_ref):
                                            member: xtce.MemberType
                                            out_dict["fields"] = dict()
                                            out_dict[IntrinsicDataType.AGGREGATE] = IntrinsicDataType.AGGREGATE
                                            out_dict[XTCEParser.ARG_NAME_KEY] = aggregate.get_name()
                                            out_dict[XTCEParser.HOST_PARAM] = host_param
                                            for member in aggregate.get_MemberList().get_Member():
                                                # TODO:Parse fields
                                                # out_dict[member.get_name()] = dict()
                                                # self.__get_param_type(member.get_typeRef(), spacesystem,
                                                #                       out_dict[member.get_name()])

                                                out_dict["fields"][member.get_name()] = dict()
                                                out_dict["fields"][member.get_name()][
                                                    XTCEParser.ARG_NAME_KEY] = member.get_name()

                                                ref_spacesystem = self.__get_spacesystem_from_ref(
                                                    member.get_typeRef(), spacesystem)
                                                self.__get_param_type(member.get_typeRef(),
                                                                      ref_spacesystem,
                                                                      aggregate.get_name(),
                                                                      out_dict["fields"][member.get_name()])
                                            return

    def __get_param_type_map(self, param_ref: str, spacesystem: xtce.SpaceSystemType):
        parameter_type_dict = dict()
        tlm = spacesystem.get_TelemetryMetaData()
        if tlm is not None:
            if tlm.get_ParameterSet() is not None:
                param: xtce.ParameterType
                for param in tlm.get_ParameterSet().get_Parameter():
                    if param_ref == param.get_name():
                        parameter_type_dict[param.get_name()] = dict()
                        parameter_type_dict[param.get_name()][XTCEParser.PARAM_NAME_KEY] = param.get_name()
                        self.__get_param_type(param.get_parameterTypeRef(), spacesystem, param.get_name(),
                                              parameter_type_dict[param.get_name()])

        return parameter_type_dict

    def __get_param_map(self, container: xtce.SequenceContainerType, spacesystem: xtce.SpaceSystemType):
        entry: xtce.ParameterRefType
        param_dict = {}
        # TODO:Use ordered dict for params
        # In python 3.7+, ordered dicts are law:https://mail.python.org/pipermail/python-dev/2017-December/151283.html
        for entry in container.get_EntryList().get_ParameterRefEntry():
            ref = entry.get_parameterRef()
            if ref == 'PX4_POSITION_SETPOINT_TRIPLET_MID':
                print('PX4_POSITION_SETPOINT_TRIPLET_MID')
            # TODO:Query the ParameterSet
            param_dict[ref] = self.__get_param_type_map(ref, spacesystem)
            param_dict[ref][XTCEParser.PARAM_NAME_KEY] = ref
            set_offset(param_dict[ref][ref])

        return param_dict

    def __get_arg_type_map(self, arg_ref: str, command: xtce.CommandContainerType, spacesystem: xtce.SpaceSystemType):
        argument_type_dict = dict()
        # cmd = spacesystem.get_CommandMetaData()
        if command is not None:
            if command.get_EntryList() is not None:
                arg: xtce.ArgumentArgumentRefEntryType
                for arg in command.get_EntryList():
                    # get_ArgumentRefEntry().get_argumentRef()
                    if arg_ref == arg.ArgumentArgumentRefEntryType:
                        argument_type_dict[arg.get_name()] = dict()
                        argument_type_dict[arg.get_name()][XTCEParser.ARG_NAME_KEY] = arg.get_name()
                        self.__get_arg_type(arg.get_argumentTypeRef(), spacesystem, arg.get_name(),
                                            argument_type_dict[arg.get_name()])

        return argument_type_dict

    def __get_arg_map(self, command: xtce.CommandContainerType, spacesystem: xtce.SpaceSystemType):
        entry: xtce.ArgumentArgumentRefEntryType
        arg_dict = {}
        # TODO:Use ordered dict for params
        # In python 3.7+, ordered dicts are law:https://mail.python.org/pipermail/python-dev/2017-December/151283.html
        for entry in command.get_EntryList().get_ArgumentRefEntry():
            ref = entry.get_argumentRef()
            # TODO:Query the ParameterSet
            arg_dict[ref] = self.__get_arg_type_map(ref, command, spacesystem)
            arg_dict[ref][XTCEParser.ARG_NAME_KEY] = ref

        return arg_dict

    def __map_all_containers(self):
        """
        Maps all of the containers inside XTCE. {'CI_HK_TLM_MID': {'CI_HK_TLM_MID': {'name': 'CI_HK_TLM_MID',
        'usCmdCnt': {'name': 'usCmdCnt', 'intrinsic': <xtce.xtce.IntegerParameterType object at 0x7f60d08eebe0>},
        'usCmdErrCnt': {'name': 'usCmdErrCnt', 'intrinsic': <xtce.xtce.IntegerParameterType object at
        0x7f60d08eebe0>}, 'padding': {'name': 'padding', 'array_type': [<xtce.xtce.IntegerParameterType object at
        0x7f60d08eebe0>, <xtce.xtce.IntegerParameterType object at 0x7f60d08eebe0>]}, 'IngestMsgCount': {'name':
        'IngestMsgCount', 'intrinsic': <xtce.xtce.IntegerParameterType object at 0x7f60d08eebe0>},
        'IngestErrorCount': {'name': 'IngestErrorCount', 'intrinsic': <xtce.xtce.IntegerParameterType object at
        0x7f60d08eebe0>}}, 'name': 'CI_HK_TLM_MID'}}
        """
        self.__map_tlm_containers()
        # self.__map_commands()

    def __map_tlm_containers(self):
        qualified_name: str
        spacesystem: xtce.SpaceSystemType
        for qualified_name in self.__namespace_dict.keys():
            logging.info(f"Parsing containers for'{qualified_name}'")
            if self.__namespace_dict[qualified_name][self.SPACE_SYSTEM_KEY] is not None:
                self.__namespace_dict[qualified_name][XTCEParser.CONTAINERS_KEY] = self.__get_seq_containers_map(
                    self.__namespace_dict[qualified_name][self.SPACE_SYSTEM_KEY])

    def __map_commands(self):
        # FIXME:Update for commands
        qualified_name: str
        spacesystem: xtce.SpaceSystemType
        for qualified_name in self.__namespace_dict.keys():
            logging.info(f"Parsing containers for'{qualified_name}'")
            if self.__namespace_dict[qualified_name][self.SPACE_SYSTEM_KEY] is not None:
                self.__namespace_dict[qualified_name][XTCEParser.COMMANDS_KEY] = self.__get_meta_commands_map(
                    self.__namespace_dict[qualified_name][self.SPACE_SYSTEM_KEY])

    def __map_all_spacesystems(self, root: xtce.SpaceSystemType, out: list, depth: int = 0):
        """
        Map all of the subsystems names under root.
        """
        # FIXME:This function should be simplified. Don't like how complex this is.
        out = out[:depth]
        out.append(root.get_name())
        spacesystem_qualifiedname = self.__child_names_to_qualified_name(out)
        self.__namespace_dict[spacesystem_qualifiedname] = dict()
        # FIXME: Move these magical keys to const variables
        self.__namespace_dict[spacesystem_qualifiedname][XTCEParser.SPACE_SYSTEM_KEY] = root
        if len(root.get_SpaceSystem()) > 0:
            s: xtce.SpaceSystemType
            for s in root.get_SpaceSystem():
                s.set_parent(root)
                self.__map_all_spacesystems(s, out, depth + 1)
        else:
            spacesystem_qualifiedname = self.__child_names_to_qualified_name(out)
            self.__namespace_dict[spacesystem_qualifiedname] = dict()
            self.__namespace_dict[spacesystem_qualifiedname][XTCEParser.SPACE_SYSTEM_KEY] = root

    def __get_namespace(self, namespace_name: str) -> dict:
        """
        Returns a namespace SpaceSystemType object that has the name of namespace_name.
        :param namespace_name:
        :return:
        """
        namespace_name = namespace_name.rstrip(XTCEManager.NAMESPACE_SEPARATOR)
        return self.__namespace_dict[namespace_name]

    def __query_spacesystem_from_qualified_name(self, qualified_name: str) -> dict:
        """
        Return a SpaceSystemType from a query string such as "/cfs/cpd/apps/px4lib/PX4_VEHICLE_GLOBAL_POSITION_MID.Lat".
        """
        qualified_name = qualified_name.strip(XTCEManager.NAMESPACE_SEPARATOR)
        current_name = ""
        spacesystem = None
        for space_system_name in qualified_name.split(XTCEManager.NAMESPACE_SEPARATOR):
            current_name += XTCEManager.NAMESPACE_SEPARATOR + space_system_name
            if current_name in self.__namespace_dict:
                spacesystem = self.__get_namespace(current_name)

        return spacesystem

    def query_container_from_qualified_name(self, qualified_name: str) -> dict:
        """
        Return a ContainerType from a query string such as "/cfs/cpd/apps/px4lib/PX4_VEHICLE_GLOBAL_POSITION_MID.Lat".
        If the container is not found, None is returned.
        """
        result_container: xtce.ContainerType = None
        system: dict = self.__query_spacesystem_from_qualified_name(qualified_name)
        # FIXME: Add error-checking here
        tokens = qualified_name.split(xtce_generator.XTCEManager.NAMESPACE_SEPARATOR)
        if XTCEParser.STRUCT_SEPARATOR in qualified_name:
            container_name = tokens[-1].split(".")[0]
        else:
            container_name = tokens[-1]
        seq_container: xtce.SequenceContainerType
        result_container = system[self.CONTAINERS_KEY][container_name]

        return result_container

    def query_param_from_paramref(self, param_ref: str) -> Union[xtce.ParameterType]:
        # TODO:Handle the case where are no slashes in param_ref
        result: xtce.ParameterType = None
        s: xtce.SpaceSystemType
        s = self.__query_spacesystem_from_qualified_name(param_ref)[self.SPACE_SYSTEM_KEY]
        param_name = param_ref.split(xtce_generator.XTCEManager.NAMESPACE_SEPARATOR)[-1]
        p: xtce.ParameterType
        for p in s.get_TelemetryMetaData().get_ParameterSet().get_Parameter():
            if p.get_name() == param_name:
                result = p
        return result

    def __get_param_name(self, qualified_name: str):
        # FIXME: At the moment nested structs are not supported
        return qualified_name.split(xtce_generator.XTCEManager.NAMESPACE_SEPARATOR)[-1]


    def get_value_from_bits(self, value_bits: bitarray, params_map: dict, param_name: str):
        i_type = get_param_intrinsic_type(params_map, param_name)
        value = None
        if type(i_type) == xtce.IntegerParameterType:
            value = ba2int(value_bits)
        elif type(i_type) == xtce.FloatParameterType:
            # >> > struct.unpack('f', b)  # native byte order (little-endian on my machine)
            # (1.7230105268977664e+16,)
            # >> > struct.unpack('>f', b)  # big-endian
            # (-109.22724914550781,)
            value = struct.unpack('f', value_bits.tobytes())[0]  # little-endian

        elif type(i_type) == xtce.BooleanParameterType:
            value = bool(ba2int(value_bits))  # little-endian

        elif type(i_type) == xtce.StringParameterType:
            value = value_bits.tobytes().decode('utf-8')  # little-endian

        elif type(i_type) == xtce.EnumeratedParameterType:
            # FIXME:Implement properly
            value = ba2int(value_bits)  # little-endian
            for enum in i_type.get_EnumerationList().get_Enumeration():
                enum: xtce.ValueEnumerationType()

                if enum.get_value() == value:
                    value = enum.get_label()

        # elif type(i_type) == list:
        #     value = []
        #     value = ba2int(value_bits)
        #     for item in i_type:
        #         value.append(item)
        return value

    def validate_packet(self, packet: bytes, path: str):
        """
        Returns the value inside of the packet that path points to, but only if packet is valid.
        The packet is validated based on XTCE rules such as criteria for containers.
        If the packet is not valid, None is returned.
        """
        value = None
        bits = bitarray(endian='big')
        bits.frombytes(packet)
        container_map = self.query_container_from_qualified_name(path)
        criteria: xtce.RestrictionCriteriaType
        criteria = container_map[self.BASE_CONTAINER_KEY][self.BASE_CONTAINER_CRITERIA_KEY]
        comparison_list: xtce.ComparisonListType
        comparison_list = criteria.get_ComparisonList()
        is_valid = True
        if len(comparison_list.get_Comparison()) > 0:
            for comparison in comparison_list.get_Comparison():
                v = ValueEvaluator()
                if v.evaluate(container_map, comparison, packet) is not True:
                    is_valid = False
                    break
        if is_valid:
            # TODO: Extract endian from the params
            container_bits = bitarray(endian='little')
            container_bits.frombytes(packet)
            base_container_key = list(container_map[self.BASE_CONTAINER_KEY].keys())[0]

            base_container_size = get_bit_size_from_container(
                container_map[self.BASE_CONTAINER_KEY][base_container_key][XTCEParser.PARAMS_KEY])
            container_size = get_bit_size_from_container(container_map[XTCEParser.PARAMS_KEY])
            param_name = self.__get_param_name(path)
            param_offset = get_offset_aggregate(container_map[XTCEParser.PARAMS_KEY],
                                                param_name)

            param_value_size = get_param_bit_size(
                container_map[XTCEParser.PARAMS_KEY],
                param_name)

            # FIXME: Need to handle the case when the param is an array.
            value_bits = container_bits[
                         base_container_size + param_offset:base_container_size + param_offset + param_value_size]

            value = self.get_value_from_bits(value_bits, container_map[XTCEParser.PARAMS_KEY], param_name)

        return value

    def craft_tlm_command(self, path: str, args: dict) -> bytes:
        """
        Returns a new packet based on path and args. This packet(though queried from XTCE telemetry),
        may be used as a command that can be sent to the vehicle.
        """
        value = None
        # TODO: Query endian from XTCE
        # payload_bits = bitarray(endian='little')
        base_container_bits = bitarray(endian='big')
        # FIXME:There is a bit of an implicit assumption here in that this container maps to a param. Add some error
        #  checking here
        container_map = self.query_container_from_qualified_name(path)
        # TODO: Extract endian from the params
        # container_bits = bitarray(endian='little')
        # container_bits.frombytes(packet)
        base_container_key = list(container_map[self.BASE_CONTAINER_KEY].keys())[0]

        base_container_size = get_bit_size_from_container(
            container_map[self.BASE_CONTAINER_KEY][base_container_key][XTCEParser.PARAMS_KEY])
        container_size = get_bit_size_from_container(container_map[XTCEParser.PARAMS_KEY])

        container_map = self.query_container_from_qualified_name(path)
        criteria: xtce.RestrictionCriteriaType
        criteria = container_map[self.BASE_CONTAINER_KEY][self.BASE_CONTAINER_CRITERIA_KEY]
        comparison_list: xtce.ComparisonListType
        comparison_list = criteria.get_ComparisonList()
        if len(comparison_list.get_Comparison()) > 0:
            # FIXME:At the moment it is assumed that there is only 1 comparison
            for comparison in comparison_list.get_Comparison():
                base_container_bits = extract_bits_from_base_container(container_map, comparison,
                                                                       base_container_size + container_size)
                break

        payload_bits = base_container_bits.copy()

        param_name = self.__get_param_name(path)

        current_bit_cursor = base_container_size

        for arg in args:
            arg_bits = bitarray(endian='little')
            arg_value = args[arg]
            param_offset = get_offset_aggregate(container_map[XTCEParser.PARAMS_KEY],
                                                param_name + "." + arg)
            print(f"param offset:offset:{param_offset}")

            param_value_size = get_param_bit_size(
                container_map[XTCEParser.PARAMS_KEY],
                param_name + "." + arg)

            # FIXME: Need to handle the case when the param is an array.
            i_type = get_param_intrinsic_type(container_map[XTCEParser.PARAMS_KEY], param_name + "." + arg)
            # FIXME:Check byte order
            if type(i_type) == xtce.IntegerParameterType:
                # FIXME:This won't work with partials
                size_in_bytes = int(i_type.get_IntegerDataEncoding().get_sizeInBits() / 8)
                bytes_data = int(arg_value).to_bytes(size_in_bytes, 'little')

                arg_bits.frombytes(bytes_data)
                for bit in arg_bits:
                    payload_bits[current_bit_cursor] = bit
                    current_bit_cursor += 1

                # bits[param_offset: param_value_size] = arg_value
                # print(f"param_value_size:size:{param_value_size}")
                # value = ba2int(value_bits)
            elif type(i_type) == xtce.FloatParameterType:
                # arg_bits.frombytes(bytes_data)
                # bits.insert()
                # >> > struct.unpack('f', b)  # native byte order (little-endian on my machine)
                # (1.7230105268977664e+16,)
                # >> > struct.unpack('>f', b)  # big-endian
                # (-109.22724914550781,)
                arg_bits.frombytes(bytes(bytearray(struct.pack('f', arg_value))))

                for bit in arg_bits:
                    payload_bits[current_bit_cursor] = bit
                    current_bit_cursor += 1

                value = struct.pack('f', arg_value)[0]  # little-endian
        #
        #     elif type(i_type) == xtce.BooleanParameterType:
        #         pass
        #         # value = bool(ba2int(value_bits))  # little-endian
        #
        #     elif type(i_type) == xtce.StringParameterType:
        #         pass
        #         # value = value_bits.tobytes().decode('utf-8')  # little-endian
        #
        #     elif type(i_type) == xtce.EnumeratedParameterType:
        #         pass
        #         # FIXME:Implement properly
        #         # value = ba2int(value_bits)  # little-endian
        #         # for enum in i_type.get_EnumerationList().get_Enumeration():
        #         #     enum: xtce.ValueEnumerationType()
        #         #
        #         #     if enum.get_value() == value:
        #         #         value = enum.get_label()
        #
        #     elif type(i_type) == List[xtce.BaseDataType]:
        #         value = []
        #         for item in i_type:
        #             pass
        #     else:
        #         logging.warning(f"The packet for {path} is valid, but no type for it was found.")
        output_bytes = self.slip_encode(payload_bits.tobytes(), 12)

        print(f"length of message:{output_bytes}")
        return output_bytes

    def slip_encode(self, packet: bytes, header_size: int):
        payload = bytearray()
        cursor = 0
        for character in packet:
            c_hex = hex(character)
            print(c_hex)
            if cursor < header_size:
                value = struct.unpack('>B', character.to_bytes(1, "big"))[0]  # big-endian
            else:
                value = struct.unpack('B', character.to_bytes(1, "little"))[0]  # little-endian
            if value == END:
                value = END
                payload.append(value)
                value = ESC_END
                payload.append(value)
            elif value == ESC:
                value = ESC
                payload.append(value)
                value = ESC_ESC
                payload.append(value)
                payload.append(character)
            else:
                payload.append(character)
            cursor += 1

        payload.append(END)
        return bytes(payload)


class Evaluator(ABC):
    # @abstractmethod
    # def evaluate(self) -> bool:
    pass


def get_bit_size(intrinsic_type: Union[list, xtce.BaseDataType]):
    bit_size = 0
    if isinstance(intrinsic_type, xtce.IntegerParameterType):
        bit_size = intrinsic_type.get_IntegerDataEncoding().get_sizeInBits()
    elif isinstance(intrinsic_type, list):
        for item in intrinsic_type:
            bit_size += get_bit_size(item)

    elif isinstance(intrinsic_type, xtce.FloatParameterType):
        bit_size += intrinsic_type.get_sizeInBits()

    elif isinstance(intrinsic_type, xtce.BooleanParameterType):
        # FIXME: It is perfectly legal to have something else other than Integer encoding for boolean types
        bit_size += intrinsic_type.get_IntegerDataEncoding().get_sizeInBits()

    elif isinstance(intrinsic_type, xtce.StringParameterType):
        bit_size += intrinsic_type.get_StringDataEncoding().get_SizeInBits().get_Fixed().get_FixedValue()

    elif isinstance(intrinsic_type, xtce.EnumeratedParameterType):
        bit_size += intrinsic_type.get_IntegerDataEncoding().get_sizeInBits()

    return bit_size


def get_offset_aggregate(params, param_name) -> int:
    """"
    It is assumed that the params are sequential.
    """
    offset = 0
    if XTCEParser.INTRINSIC_KEY in params:
        if params[XTCEParser.PARAM_NAME_KEY] == param_name:
            offset = params[XTCEParser.OFFSET_KEY] - get_bit_size(params[XTCEParser.INTRINSIC_KEY])

    elif XTCEParser.ARRAY_TYPE_KEY in params and params[XTCEParser.PARAM_NAME_KEY] == param_name:
        for p in params[XTCEParser.ARRAY_TYPE_KEY]:
            # FIXME:This assumes all elements in list are intrinsic
            offset += get_bit_size(p)

    else:
        if type(params) is dict:
            if IntrinsicDataType.AGGREGATE in params:
                if XTCEParser.STRUCT_SEPARATOR in param_name:
                    name_path = param_name.split(XTCEParser.STRUCT_SEPARATOR)
                    aggregate_name = name_path[0]

                    if aggregate_name == params[XTCEParser.HOST_PARAM]:
                        new_name = XTCEParser.STRUCT_SEPARATOR.join(name_path[1:])
                        for field in params["fields"]:
                            offset = get_offset_aggregate(params["fields"][field], new_name)
                            if offset > 0:
                                break
                    else:
                        logging.error(f"Could not find aggregate name {aggregate_name}")
                # else:
                #     if params[XTCEParser.PARAM_NAME_KEY] == param_name:
                #         name_path = param_name.split(XTCEParser.STRUCT_SEPARATOR)
                #         # This is a field. Subscribing to structs is not supported at the moment
                #         field_name = name_path[-1]
                #         for field in params["fields"]:
                #             if field == field_name:
                #                 break
                #             offset += get_offset(params["fields"][field], field_name)

            else:
                for p in params:
                    if type(params[p]) is dict:
                        offset += get_offset_aggregate(params[p], param_name)
                        if offset > 0:
                            break
    return offset


def get_offset_container(params, param_name) -> int:
    """"
    It is assumed that the params are sequential.
    """
    offset = 0
    if XTCEParser.INTRINSIC_KEY in params:
        if params[XTCEParser.PARAM_NAME_KEY] != param_name:
            offset = get_bit_size(params[XTCEParser.INTRINSIC_KEY])

    elif XTCEParser.ARRAY_TYPE_KEY in params and params[XTCEParser.PARAM_NAME_KEY] != param_name:
        for p in params[XTCEParser.ARRAY_TYPE_KEY]:
            # FIXME:This assumes all elements in list are intrinsic
            offset += get_bit_size(p)

    else:
        if type(params) is dict:
            for p in params:
                if p == param_name:
                    break
                if type(params[p]) is dict:
                    offset += get_offset_container(params[p], param_name)
    return offset


def set_offset(params, start_offset: int = 0) -> int:
    """"
    It is assumed that the params are sequential.
    """
    offset = 0
    if XTCEParser.INTRINSIC_KEY in params:
        offset = get_bit_size(params[XTCEParser.INTRINSIC_KEY])
        params[XTCEParser.OFFSET_KEY] = offset + start_offset

    elif XTCEParser.ARRAY_TYPE_KEY in params:
        for p in params[XTCEParser.ARRAY_TYPE_KEY]:
            # FIXME:This assumes all elements in list are intrinsic
            offset += get_bit_size(p)

    elif IntrinsicDataType.AGGREGATE in params:
        field_offset = start_offset
        for field in params["fields"]:
            field_offset += set_offset(params["fields"][field], field_offset)
        offset = field_offset - start_offset
    return offset


def get_bit_size_from_container(params) -> int:
    """"
    It is assumed that the params are sequential.
    """
    offset = 0

    if XTCEParser.INTRINSIC_KEY in params:
        offset = get_bit_size(params[XTCEParser.INTRINSIC_KEY])

    # FIXME:Might be a good idea to wrap array types as "intrinsic" types as well.
    elif XTCEParser.ARRAY_TYPE_KEY in params:
        for p in params[XTCEParser.ARRAY_TYPE_KEY]:
            offset += get_bit_size(p)
    else:
        if type(params) is dict:
            for p in params:
                if type(params[p]) is dict:
                    offset += get_bit_size_from_container(params[p])
    return offset


#  FIXME:Add bool flag to know whether you have found the param or not. Or this is a possible solution
#  to having multiple keys with the same name across multiple levels of the dict.
def get_param_bit_size(params, param_name) -> int:
    """"
    It is assumed that the params are sequential.
    """
    size = 0
    # TODO:Handle this better as there may be a param name called "name" in the XTCE
    if XTCEParser.INTRINSIC_KEY in params and params[XTCEParser.PARAM_NAME_KEY] == param_name:
        size = get_bit_size(params[XTCEParser.INTRINSIC_KEY])
    elif XTCEParser.ARRAY_TYPE_KEY in params and params[XTCEParser.PARAM_NAME_KEY] == param_name:
        for p in params[XTCEParser.ARRAY_TYPE_KEY]:
            # FIXME:This assumes all elements in list are intrinsic
            size += get_bit_size(p)
    else:
        if type(params) is dict:
            if IntrinsicDataType.AGGREGATE in params:
                if XTCEParser.STRUCT_SEPARATOR in param_name:
                    name_path = param_name.split(XTCEParser.STRUCT_SEPARATOR)
                    aggregate_name = name_path[0]

                    if aggregate_name == params[XTCEParser.HOST_PARAM]:
                        # if aggregate_name == params[XTCEParser.HOST_PARAM]:
                        new_name = XTCEParser.STRUCT_SEPARATOR.join(name_path[1:])
                        if XTCEParser.STRUCT_SEPARATOR in new_name:
                            for field in params["fields"]:
                                size += get_param_bit_size(params["fields"][field], new_name)
                        else:
                            for field in params["fields"]:
                                size += get_param_bit_size(params["fields"][field], new_name)

                        # nested struct
                else:
                    if params[XTCEParser.PARAM_NAME_KEY] == param_name:
                        name_path = param_name.split(XTCEParser.STRUCT_SEPARATOR)
                        # This is a field. Subscribing to structs is not supported at the moment
                        field_name = name_path[-1]
                        for field in params["fields"]:
                            size += get_param_bit_size(params["fields"][field], field_name)
                            if field == field_name:
                                break

                # else:
                #     pass
                #     Should not happen. This will mean either there is a bug in our code or the path is incorrect.
                #     Throw exception
            else:
                for p in params:
                    # TODO:Handle this better as there may be a param name called "name" in the XTCE
                    if type(params[p]) is dict:
                        size += get_param_bit_size(params[p], param_name)
                    if p == param_name:
                        break
    return size


def get_param_intrinsic_type(params, param_name) -> Union[xtce.BaseDataType, List[xtce.BaseDataType]]:
    """"
    It is assumed that the params are sequential.
    """
    i_type = None
    # FIXME:Add support for nested structs. Should be pretty easy now.
    if XTCEParser.INTRINSIC_KEY in params and params[XTCEParser.PARAM_NAME_KEY] == param_name:
        # TODO:Handle this better as there may be a param name called "name" in the XTCE
        if params[XTCEParser.PARAM_NAME_KEY] == param_name:
            i_type = params[XTCEParser.INTRINSIC_KEY]

    # FIXME:Might be a good idea to wrap array types as "intrinsic" types as well.
    elif XTCEParser.ARRAY_TYPE_KEY in params and params[XTCEParser.PARAM_NAME_KEY] == param_name:
        i_type = []
        for p in params[XTCEParser.ARRAY_TYPE_KEY]:
            # Replace with array type
            i_type.append(p)
    else:
        if type(params) is dict:
            if IntrinsicDataType.AGGREGATE in params:
                if XTCEParser.STRUCT_SEPARATOR in param_name:
                    name_path = param_name.split(XTCEParser.STRUCT_SEPARATOR)
                    aggregate_name = name_path[0]

                    # if aggregate_name == params[XTCEParser.HOST_PARAM]:
                    new_name = XTCEParser.STRUCT_SEPARATOR.join(name_path[1:])
                    if XTCEParser.STRUCT_SEPARATOR in new_name:
                        for field in params["fields"]:
                            new_type = get_param_intrinsic_type(params["fields"][field], new_name)
                            if new_type is not None:
                                i_type = new_type
                                break

                        # nested struct
                    else:
                        # This is a field. Subscribing to structs is not supported at the moment
                        field_name = name_path[-1]
                        for field in params["fields"]:
                            new_type = get_param_intrinsic_type(params["fields"][field], field_name)
                            if new_type is not None:
                                i_type = new_type
                                break
                            if field == field_name:
                                # Should not happen
                                logging.error(f"No type for field '{field}' found")
                                break

                    # else:
                    #     pass
                    #     Should not happen. This will mean either there is a bug in our code or the path is incorrect.
                    #     Throw exception
        for p in params:
            # TODO:Handle this better as there may be a param name called "name" in the XTCE
            if p == param_name:
                new_type = get_param_intrinsic_type(params[p], param_name)
                if new_type is not None:
                    i_type = new_type
                    break
            else:
                if type(params[p]) is dict:
                    new_type = get_param_intrinsic_type(params[p], param_name)
                    if new_type is not None:
                        i_type = new_type
                        break

    return i_type


# TODO:Move this to a different module.
# This will allow us to decouple ourselves from a specific protocol such as CCSDS, Mavlink.
class ValueEvaluator(Evaluator):
    def evaluate(self, container: dict, comparison: xtce.ComparisonType, packet: bytes) -> bool:
        valid = False
        container_key = list(container[XTCEParser.BASE_CONTAINER_KEY].keys())[0]
        # FIXME: The value of the comparison won't always be an int.
        comp_value = int(comparison.get_value())
        comp_value_ref: str = comparison.get_parameterRef()
        if xtce_generator.XTCEManager.NAMESPACE_SEPARATOR in comp_value_ref:
            comp_value_ref = comp_value_ref.split(xtce_generator.XTCEManager.NAMESPACE_SEPARATOR)[-1]

        offset = get_offset_container(container[XTCEParser.BASE_CONTAINER_KEY][container_key][XTCEParser.PARAMS_KEY],
                                      comp_value_ref)

        value_size = get_param_bit_size(container[XTCEParser.BASE_CONTAINER_KEY][container_key][XTCEParser.PARAMS_KEY],
                                        comp_value_ref)

        # TODO: Big/Little endian is inside XTCE
        bits = bitarray(endian='big')
        bits.frombytes(packet)

        extracted_bits = bits[offset:offset + value_size]
        val = ba2int(extracted_bits)

        if comp_value == val:
            valid = True
        return valid


class XTCEMsgParserApp(App):
    pass
