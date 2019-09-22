import configparser
import radarr_folder_organizer.helper.ConfigSectionHelper

def test_should_return_mapping():
    config_parser = configparser.ConfigParser()
    config_parser.optionxform = str
    config_parser.read("tests/testConfig.txt")
    radarr = radarr_folder_organizer.helper.ConfigSectionHelper.load_section(config_parser, 'Radarr')
    mappings = radarr_folder_organizer.helper.ConfigSectionHelper.load_section(config_parser, 'CustomFormatMappings')
    assert radarr['url'] == 'urlValue'
    assert radarr['key'] == 'keyValue'
    assert mappings['__default'] == '/default/folder'
    assert mappings['custom_format1'] == '/custom/format/1/folder'
