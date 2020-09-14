from xml.etree import ElementTree as ET
import src.xtce_generator.xtce as xtce
import argparse
import sqlite3


class XTCEManager:
    def __init__(self, root_space_system: str):
        self.root = xtce.SpaceSystemType(root_space_system)
        self.telemetry_metadata = xtce.TelemetryMetaDataType()
        self.command_metadata = xtce.CommandMetaDataType()
        self.paramter_type_set = xtce.ParameterTypeSetType()

        self.telemetry_metadata.set_ParameterTypeSet(self.paramter_type_set)
        self.root.set_TelemetryMetaData(self.telemetry_metadata)
        self.root.set_CommandMetaData(self.command_metadata)


    def isBaseType(self, symbol: str):
        return 'int' == symbol or 'uint8_t' == symbol


    def addBaseTypes(self, db_cursor: sqlite3.Cursor, telemetry_metadata: xtce.TelemetryMetaDataType):
        """
        Get all base types from the database and add it to telemetry_metadata.
        This function adds a ParamaterTypeSet to telemetry_metadata. It is assumed that telemetry_metadata has no
        ParameterTypeSet.
        :param db_cursor:
        :param telemetry_metadata:
        :return:
        """
        baseSet = xtce.ParameterTypeSetType()
        baseSet.add
        for symbol in db_cursor.execute('SELECT name FROM symbols').fetchall():
            if self.isBaseType(symbol[0]):
                # TODO: If our type is of integer type, gather the data about it, construct it and add it to the baseset
                baseType = xtce.IntegerParameterType()




    def add_namespace(self, namespace_name: str):
        self.root.add_SpaceSystem(namespace_name)

    def write_to_file(self, filename):
        """
        Writes the current xtce spcesystem to a file.
        :return:
        """
        self.root.export(open(filename, 'w+'), 0)


def parse_cli() -> argparse.Namespace:
    """
    Parses cli argyments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in path to sqlite database.')
    parser.add_argument('--sqlite_path', type=str,
                        help='The file path to the sqlite database', required=True)

    return parser.parse_args()


def main():
    args = parse_cli()
    db_handle = sqlite3.connect(args.sqlite_path)
    db_cursor = db_handle.cursor()

    xtce_obj = XTCEManager('airliner')
    xtce_obj.addBaseTypes(db_cursor, xtce_obj.telemetry_metadata)
    # xtce_obj.write_to_file('new_xml.xml')


if __name__ == '__main__':
    main()
