import configparser
import os
import pathlib
import sys
import shutil

import requests

from .helper import ConfigSectionHelper
from .helper import PathHelper
from .radarr import RadarrClient
from .log import Log

VER = '0.0.1'

DEFAULT_MAPPING = '__default'

########################################################################################################################
LOGGER = Log.setup_logger()


########################################################################################################################


def get_current_path(movie_info):
    path = pathlib.Path(movie_info['path'])
    return str(path.parent)


def normalize_path(path):
    normpath = os.path.normpath(path)
    return os.path.normcase(normpath)


def move_movie(movie_info, current_path, correct_path, radarr_url, radarr_session):
    title = movie_info['title']
    old_path = movie_info['path']
    new_path = old_path.replace(current_path, correct_path).rstrip('/\\')

    from_folder_name = movie_info['folderName']
    new_folder_name = from_folder_name.replace(current_path, correct_path).rstrip('/\\')
    try:
        if 'movieFile' in movie_info.keys():
            LOGGER.debug('Trying to move movie "{}" files from "{}" to "{}"'.format(title, old_path, new_path))
            shutil.move(old_path, new_path)
            LOGGER.info('Movie {} files moved from "{}" to "{}"'.format(title, old_path, new_path))
        else:
            LOGGER.debug('Movie "{}" has no files. Just updating Radarr (no files to move)'.format(title, old_path, new_path))
        RadarrClient.update_movie_folder(movie_info, new_path, new_folder_name,
                                                                        radarr_url, radarr_session)
        RadarrClient.refresh_movie(movie_info, radarr_url, radarr_session)
    except Exception as e:
        LOGGER.error('Couldn\'t move movie "{}" due to exception: {}'.format(title, e))


LOGGER.debug('CustomFormatSync Version {}'.format(VER))
LOGGER.info('Starting script')

config_parser = configparser.ConfigParser()
config_parser.optionxform = str

# Loads an alternate config file so that I can work on my servers without uploading config to github
if 'DEV' in os.environ:
    settingsFilename = os.path.join(os.getcwd(), '../dev/'
                                                 'Config.txt')
else:
    settingsFilename = os.path.join(os.getcwd(), '../Config.txt')
config_parser.read(settingsFilename)

radarr_section = ConfigSectionHelper.load_section(config_parser, 'Radarr')
radarr_url = radarr_section['url']
radarr_key = radarr_section['key']

# We normalize the paths to avoid case inconsistencies when checking the mappings
custom_format_mappings = {key: normalize_path(value) for (key, value) in
                          ConfigSectionHelper.load_section(config_parser,
                                                                                          'CustomFormatMappings').items()}
if DEFAULT_MAPPING not in custom_format_mappings:
    LOGGER.error('A default mapping should be provided!!')
    sys.exit(0)

radarr_session = requests.Session()
radarr_session.headers.update({'x-api-key': radarr_key})
# TODO check if needed
radarr_session.trust_env = False
radarr_movies = RadarrClient.get_movies(radarr_url, radarr_session)

LOGGER.info('Received {} movies from Radarr'.format(len(radarr_movies)))

for movie in radarr_movies:
    title = movie['title']
    LOGGER.debug('########## Started processing movie: {} ##########'.format(title))
    current_path = get_current_path(movie)
    # We normalize the path to avoid case inconsistencies when checking the mappings
    normalized_current_path = normalize_path(current_path)
    if normalized_current_path not in custom_format_mappings.values():
        LOGGER.warning(
            'Movie "{}" current path is "{}", normalized as {} and is not in the configuration file. Skipping to avoid possible errors'.format(
                title, movie['path'], normalized_current_path))
        continue
    correct_path = PathHelper.decide_path(movie, custom_format_mappings, DEFAULT_MAPPING)
    if normalized_current_path != correct_path:
        LOGGER.debug(
            'Movie "{}" current path is "{}", normalized as {} and doesn\'t match the correct path "{}". Proceeding to move it'.format(
                title, movie['path'], normalized_current_path, correct_path))
        move_movie(movie, current_path, correct_path, radarr_url, radarr_session)
    else:
        LOGGER.debug(
            'Movie "{}" current path is "{}" and matches the correct path "{}". Nothing to do here'.format(
                title,
                movie['path'],
                correct_path))
    LOGGER.debug('########## Finished processing movie: {} ##########'.format(title))

LOGGER.info('Script has finished')


