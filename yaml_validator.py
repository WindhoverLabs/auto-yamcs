import cerberus
import yaml
import argparse
import sys


def parse_cli() -> argparse.Namespace:
    """
    Parses cli argyments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in path to sqlite database.')

    parser.add_argument('--yaml_document', type=str, required=True,
                        help='The document which to validate.')
    parser.add_argument('--yaml_schema', type=str, required=True,
                        help='The yaml schema which will be used to validate the document.')

    return parser.parse_args()


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def val():
    args = parse_cli()

    schema = read_yaml(args.yaml_schema)
    document = read_yaml(args.yaml_document)

    V = cerberus.Validator(schema)
    if V.validate(document) is True:
        print(f'The document "{args.yaml_document}" has passed validation with no errors.')
    else:
        print(f'The document "{args.yaml_document}" has failed validation because of the following errors:'
              f'\n'
              f'{V.errors}')


val()
