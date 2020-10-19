import os

import pytest

@pytest.fixture()
def get_tests_path():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), '')


@pytest.fixture()
def get_data_path():
    """
    :return: The absolute path of our data directory. The data directory is files used for testing are stored.
    """
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')

