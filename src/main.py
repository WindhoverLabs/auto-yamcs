import sqlite3
import argparse


def add_tables(db_cursor: sqlite3.Cursor) :
    """
    :param db_cursor: The cursor datbase handle.
    :return:
    """
    db_cursor.execute('create table if not exists messages(' 
                      'id INTEGER primary key, '
                      'name TEXT UNIQUE NOT NULL, '
                      'apid INTEGER NOT NULL, '
                      'symbol INTEGER NOT NULL, '
                      'FOREIGN KEY (symbol) REFERENCES symbols(id), '
                      'UNIQUE (name, apid));')

    db_cursor.execute('create table if not exists commands('
                      'id primary key,'
                      'name TEXT UNIQUE NOT NULL,'
                      'command_code INTEGER NOT NULL,'
                      'symbol INTEGER NOT NULL, '
                      'FOREIGN KEY (symbol) REFERENCES symbols(id),'
                      'UNIQUE (name, command_code));')


def parse_cli() -> argparse.Namespace:
    """
    Parses cli argyments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes command and message files and writes them to a sqlite database.')
    # parser.add_argument('message_path', metavar='Message file path', type=str,
    #                     help='The file path to the json files that has the messages', required=False)
    parser.add_argument('-sqlite_path', '--sqlite_path', metavar='Sqlite datbase path', type=str,
                        help='The file path to the sqlite database')

    return parser.parse_args()


def main():
    args = parse_cli()
    db_handle = sqlite3.connect(args.sqlite_path)
    db_cursor = db_handle.cursor()
    add_tables(db_cursor)


if __name__ == '__main__':
    main()
