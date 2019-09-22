import radarr_folder_organizer.helper.PathHelper


def test_should_return_mapping():
    target_format = 'format2'
    target_folder = 'folder2'
    default_mapping = '__default'
    custom_format_mappings = {default_mapping: 'default_folder', 'format1': 'folder1',
                              target_format: target_folder}

    returned_folder = radarr_folder_organizer.helper.PathHelper.decide_path(create_movie([target_format]),
                                                                            custom_format_mappings,
                                                                            default_mapping)

    assert target_folder == returned_folder


def test_should_return_default_when_no_matching():
    default_mapping = '__default'
    default_folder = 'default_folder'
    custom_format_mappings = {default_mapping: default_folder, 'format1': 'folder1',
                              'format2': 'folder2'}

    returned_folder = radarr_folder_organizer.helper.PathHelper.decide_path(create_movie(['IDontExist']),
                                                                            custom_format_mappings,
                                                                            default_mapping)

    assert default_folder == returned_folder


def create_movie(custom_formats):
    return {
        'title': 'random title',
        'movieFile': {
            'quality': {
                'customFormats': map(lambda e: {'name': e}, custom_formats),
            }
        }
    }
