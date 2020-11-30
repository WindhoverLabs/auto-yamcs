"""
Override types of fields in the symbols table. This is extremely useful for cases like strings
that are not captured by juicer as "strings", but rather as arrays of "char" type. Also useful
for enumerations that are represented as MACROS in code.
"""

import argparse
import logging
from typing import Union
from random import randint
import yaml
import sqlite_utils


def generate_random_name(name_length: int):
    """
    Generates a random string that has name_length amount of characters in it.
    :param name_length:
    :return: Randomly generated string.
    The characters generated are chosen randomly between 65 and 90 ASCII characters; meaning upper case letters A-Z.
    """
    str_characters = []
    for name_character in range(name_length):
        # Add a random character to our list
        str_characters.append(chr(randint(65, 90)))
    return "".join(str_characters)


def symbol_exists(symbol_name: str, db_handle: sqlite_utils.Database):
    """
    Checks if the symbol record with name symbol_name exists in the database.
    :param symbol_name:
    :param db_handle:
    :return: True if symbol exists, False otherwise.
    """
    does_symbol_exists = True
    symbol_record = list(db_handle['symbols'].rows_where('name=?', [symbol_name]))

    if len(symbol_record) == 0:
        does_symbol_exists = False

    return does_symbol_exists


def add_type_to_database(type_name: str, elf_name: str, byte_size: int,
                         db_handle: sqlite_utils.Database) -> Union[dict, None]:
    """
    Adds a new type with the name of type_name size of byte_size and mapped to the elf with name of elf_name. It is
    assumed that the type does NOT exist in the database.
    :param type_name: The nam of the new type.
    :param elf_name: The name of the elf file in the database.
    :param byte_size: The size of the new type. Must be a number greater than zero.
    :param db_handle: The database handle which will be used to write record to database.
    :return: None if the elf record with name of elf_name does not exist. Otherwise a dict is returned representing
    the new symbol record that was written to the database.
    """
    new_type_record = {}
    elf_key = list(db_handle['elfs'].rows_where('name=?', [elf_name]))
    if len(elf_key) < 1:
        logging.error(f"The elf record with name of {elf_name} was not found on the database")
        return None
    new_type_record['elf'] = elf_key[0]['id']
    new_type_record['name'] = type_name
    new_type_record['byte_size'] = byte_size

    last_row_id = db_handle['symbols'].insert(new_type_record).last_rowid

    new_type_record['id'] = last_row_id

    return new_type_record


def add_random_type_to_database(elf_name: str, byte_size: int, db_handle: sqlite_utils.Database) -> Union[dict, None]:
    """
    Adds a new type to the symbols table with a random name.
    This function ensures that the new type does not exist in the database.
    :param elf_name:
    :param byte_size:
    :param db_handle:
    :return: Returns the new symbol record that was added to the database. If the elf record with name of elf_name
    does not exist, then None is returned.
    """
    new_type_record = {}
    elf_key = list(db_handle['elfs'].rows_where('name=?', [elf_name]))
    if len(elf_key) < 1:
        logging.error(f"The elf record with name of {elf_name} was not found on the database.")
        return None

    new_type_record['elf'] = elf_key[0]['id']
    random_type_name = generate_random_name(5)
    while symbol_exists(random_type_name, db_handle):
        random_type_name = generate_random_name(5)

    new_type_record['name'] = random_type_name
    new_type_record['byte_size'] = byte_size

    last_row_id = db_handle['symbols'].insert(new_type_record).last_rowid

    new_type_record['id'] = last_row_id

    return new_type_record


def add_enumeration_to_data_base(symbol_name: str, enum_map: dict, db_handle: sqlite_utils.Database) -> Union[
                                 dict, None]:
    """
    Adds new enumeration records to database.
    :param symbol_name: A foreign key to a symbol record in the symbols table.
    :param enum_map: A dictionary of the form {ENUM_NAME:VALUE} that represents all of the names and values that
    are part of this enumeration.
    :param db_handle:
    :return: The last enumeration record that was inserted if the records were added successfully. None is returned if the symbol
    with name of symbol_name does not exist.
    """
    if symbol_exists(symbol_name, db_handle) is False:
        logging.error(f'The symbol record with name of {symbol_name} does not exist.')
        return None

    enumeration_record = {}

    enumeration_record['symbol'] = list(db_handle['symbols'].rows_where('name=?', [symbol_name]))[0]['id']

    last_row_id = None

    for name, value in enum_map.items():
        enumeration_record['name'] = name
        enumeration_record['value'] = value
        last_row_id = db_handle['enumerations'].insert(enumeration_record).last_rowid

    enumeration_record['id'] = last_row_id

    return enumeration_record


def get_field_record(symbol_name: str, field_name: str, db_handle: sqlite_utils.Database) -> Union[dict, None]:
    """
    Return a field record from the database that is part of symbol symbol_name and has the name of filed_name.
    :param db_handle:
    :param symbol_name:
    :param field_name:
    :return:
    """
    field_record = None

    if symbol_exists(symbol_name, db_handle) is False:
        return field_record

    symbol_id = list(db_handle['symbols'].rows_where('name=?', [symbol_name]))[0]['id']

    field_record = list(db_handle['fields'].rows_where('symbol=? and name=?', [symbol_id, field_name]))

    if len(field_record) == 0:
        return None

    return field_record[0]


def get_field_type_record(symbol_name: str, field_name: str, db_handle: sqlite_utils.Database) -> Union[dict, None]:
    """
    Fetch the type of the field field_name that is inside the struct with name of symbol_name. Note that the record
    returned is a record from the symbols table.
    :param db_handle:
    :param symbol_name:
    :param field_name:
    :return: The new field record that was inserted into the database. None if the symbol record with name symbol_name
    does not exist.
    """
    symbol_record = None
    if symbol_exists(symbol_name, db_handle) is False:
        logging.error(f'The symbol name with name {symbol_name} does not exist.')
        return symbol_record

    field_symbol = list(db_handle['symbols'].rows_where('name=?', [symbol_name]))[0]['id']
    field_record = list(db_handle['fields'].rows_where('symbol=? and name=?', [field_symbol, field_name]))[0]

    symbol_record = list(db_handle['symbols'].rows_where('id=?', [field_record['type']]))[0]

    return symbol_record


def process_def_overrides(def_overrides: dict, db_handle: sqlite_utils.Database):
    """
    Apply overrides in def_overrides to database. Examples of these are strings that show up as char[] in sour code
    or enumerations that are represented
    :param def_overrides:
    :param db_handle:
    :return:
    """
    # Check for our core dict in airliner
    if 'core' in def_overrides:
        core_elf = def_overrides['core']['elf_files'][0]
        for app in def_overrides['core']['cfe']:
            if 'msg_def_overrides' in def_overrides['core']['cfe'][app]:
                for override in def_overrides['core']['cfe'][app]['msg_def_overrides']:
                    if override['type'] != 'enumeration':
                        type_record = get_field_type_record(override['parent'], override['member'], db_handle)
                        if type_record:
                            type_byte_size = type_record['byte_size']
                            new_type = add_type_to_database(override['type'], core_elf, type_byte_size, db_handle)
                            if new_type:
                                new_field_record = get_field_record(override['parent'], override['member'], db_handle)
                                if new_field_record:
                                    db_handle['fields'].delete_where('id=?', [new_field_record['id']])
                                    db_handle.conn.commit()
                                    new_field_record['type'] = new_type['id']
                                    db_handle['fields'].insert(new_field_record)

                        else:
                            continue
                    else:
                        type_record = get_field_type_record(override['parent'], override['member'], db_handle)
                        if type_record:
                            type_byte_size = type_record['byte_size']
                            new_type_record = add_random_type_to_database(core_elf, type_byte_size, db_handle)
                            if new_type_record:
                                new_enum_record = add_enumeration_to_data_base(new_type_record['name'],
                                                                               override['enumerations'],
                                                                               db_handle)
                                if new_enum_record:
                                    new_field_record = get_field_record(override['parent'],
                                                                        override['member'],
                                                                        db_handle)
                                    db_handle['fields'].delete_where('id=?', [new_field_record['id']])
                                    db_handle.conn.commit()
                                    new_field_record['type'] = new_type_record['id']
                                    db_handle['fields'].insert(new_field_record)
    if 'modules' in def_overrides:
        for module in def_overrides['modules']:
            module_elf = def_overrides['modules'][module]['elf_files'][0]
            if 'msg_def_overrides' in def_overrides['modules'][module]:
                for override in def_overrides['modules'][module]['msg_def_overrides']:
                    if override['type'] != 'enumeration':
                        type_record = get_field_type_record(override['parent'], override['member'], db_handle)
                        if type_record:
                            type_byte_size = type_record['byte_size']
                            new_type = add_type_to_database(override['type'], module_elf, type_byte_size, db_handle)
                            if new_type:
                                new_field_record = get_field_record(override['parent'], override['member'], db_handle)
                                if new_field_record:
                                    db_handle['fields'].delete_where('id=?', [new_field_record['id']])
                                    db_handle.conn.commit()
                                    new_field_record['type'] = new_type['id']
                                    db_handle['fields'].insert(new_field_record)
                        else:
                            continue
                    else:
                        type_record = get_field_type_record(override['parent'], override['member'], db_handle)
                        if type_record:
                            type_byte_size = type_record['byte_size']
                            new_type_record = add_random_type_to_database(module_elf, type_byte_size, db_handle)
                            if new_type_record:
                                new_enum_record = add_enumeration_to_data_base(new_type_record['name'],
                                                                               override['enumerations'],
                                                                               db_handle)
                                if new_enum_record:
                                    new_field_record = get_field_record(override['parent'],
                                                                        override['member'],
                                                                        db_handle)
                                    db_handle['fields'].delete_where('id=?', [new_field_record['id']])
                                    db_handle.conn.commit()
                                    new_field_record['type'] = new_type_record['id']
                                    db_handle['fields'].insert(new_field_record)


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def parse_cli() -> argparse.Namespace:
    """
    Parses cli arguments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in path to sqlite database.')

    parser.add_argument('--database', type=str, required=True, help='The path to the SQLITE database..')

    parser.add_argument('--yaml_path', type=str, required=True,
                        help='The yaml config file that has the overrides.')

    return parser.parse_args()


def main():
    args = parse_cli()

    db_handle = sqlite_utils.Database(args.database)
    yaml_override_data = read_yaml(args.yaml_path)

    process_def_overrides(yaml_override_data, db_handle)


if __name__ == '__main__':
    main()
