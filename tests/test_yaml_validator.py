import yaml_validator


def test_val(monkeypatch, get_data_path):
    monkeypatch.chdir(get_data_path)
    assert(yaml_validator.val('test_schema.yml', 'test_yaml.yml') is True)

