"""
This module takes in a directory and yaml file. It scans the directory for jinja templates, renders and
outputs them to the file system with data from the YAML file. The destination directory to which the templates will be
written to must be specified by the user.
"""

import argparse
from jinja2.loaders import FileSystemLoader
from jinja2 import Environment
import yaml
from pathlib import Path
import logging
import os.path


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def get_output_name(template_name: str) -> str:
    """
    Reformats the template_name by removing the extension ".jinja" at the end of the file name.
    :param template_name: The name of the template. It is assumed that the string ends in ".jinja"
    :return: A string with everything in template_name except for the ".jinja" part. This is very useful for when
    dumping the rendered template into the filesystem.
    """
    out_name = template_name[0:template_name.find('jinja') - 1]
    return out_name


def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument('--template_dir', type=str, required=True,
                        help='The directory that has all of the templates.')
    parser.add_argument('--yaml_path', type=str, required=True,
                        help='The path to the yaml file that has the data.')

    parser.add_argument('--output_dir', type=str, required=True,
                        help='The destination directory to which the output files will be written to.')

    return parser.parse_args()


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    args = parse_cli()
    # Load the template data form YAML
    yaml_data = read_yaml(args.yaml_path)

    # Setup template environment
    fs_loader = FileSystemLoader(args.template_dir)
    env = Environment(loader=fs_loader)

    output_dir_path = Path(args.output_dir)

    if output_dir_path.is_dir() is False:
        logging.error(f'{output_dir_path} is not a directory. Terminating.')
        # FIXME: I don't know about returning from here. Violates single point of exit standard.
        # FIXME: It might be best to implement a validation pattern the entire codebase of auto-yamcs.
        # FIXME: If we had reliable validation, we wouldn't need these stick-in-the-mud types of checks.
        return -1

    for template in env.list_templates():
        template_path = Path(template)
        template_obj = env.get_template(template)

        output_filepath = get_output_name(template_path.name)

        absolute_output_filepath = os.path.join(output_dir_path, output_filepath)

        # I know this is not the most succinct way of doing this, but I rather be explicit.
        template_stream = template_obj.stream(yaml_data)

        # output rendered template to a file
        template_stream.dump(absolute_output_filepath)

    logging.info(f'Templates were written to {output_dir_path}')


if __name__ == '__main__':
    main()
