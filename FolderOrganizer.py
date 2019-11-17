import configparser
import json
import logging
import os
import pathlib
import sys
import shutil

import requests

VER = '1.0.0'

ID = "id"
FOLDER_NAME = "folderName"
PATH = "path"
QUALITY = "quality"
CUSTOM_FORMATS = "customFormats"
DEFAULT_MAPPING = "__default"

IMPORTED_EVENT_TYPE = "downloadFolderImported"
GRABBED_EVENT_TYPE = "grabbed"
DOWNLOAD_ID = "downloadId"
EVENT_TYPE = "eventType"

# Flags
MOVE_DEFAULT_FLAG = 'MOVE_DEFAULT'
LOG_LEVEL = "LOG_LEVEL"


def config_section_map(section):
    dict1 = {}
    options = config_parser.options(section)
    for option in options:
        try:
            dict1[option] = config_parser.get(section, option)
            if dict1[option] == -1:
                logger.debug("skip: {}".format(option))
        except Exception:
            logger.error("exception on {}!".format(option))
            dict1[option] = None
    return dict1


def get_custom_format_names(movie_info):
    if "movieFile" not in movie_info.keys():
        return list()
    return list(map(lambda e: e["name"], movie_info["movieFile"]["quality"]["customFormats"]))


def decide_path(movie_info, format_mappings):
    movie_custom_formats = get_custom_format_names(movie_info)
    movie_title = movie_info['title']
    logger.debug('Movie "{}" has custom formats: {}'.format(movie_title, movie_custom_formats))
    if len(movie_custom_formats) > 0:
        for format_name in filter(lambda e: DEFAULT_MAPPING != e, format_mappings.keys()):
            if format_name in movie_custom_formats:
                format_path = format_mappings[format_name]
                logger.debug(
                    'MATCHED FORMAT!! Movie "{}": format {} is in movie custom formats {}. Its correct path is {} !!'.format(
                        movie_title, format_name,
                        movie_custom_formats, format_path))
                return format_path
            else:
                logger.debug(
                    'Movie "{}": format {} is not in movie custom formats {}. Checking other potential formats'.format(
                        movie_title,
                        format_name,
                        movie_custom_formats))
    if should_move_default:
        default_path = format_mappings[DEFAULT_MAPPING]
        logger.debug(
            'NO MATCHED FORMAT!! Movie "{}": didn\'t match any mapped format. {} flag value is enabled so its correct path is {} !!'.format(
                movie_title, MOVE_DEFAULT_FLAG, default_path))
        return default_path
    logger.debug('NO MATCHED FORMAT!! Movie "{}": didn\'t match any mapped format. {} flag value is disabled so no new path is assigned !!'.format(
            movie_title, MOVE_DEFAULT_FLAG))
    return None


def get_current_path(movie_info):
    path = pathlib.Path(movie_info[PATH])
    return str(path.parent)


def normalize_path(path):
    normpath = os.path.normpath(path)
    return os.path.normcase(normpath)


def move_movie(movie_info, current_path, correct_path):
    movie_title = movie_info["title"]
    old_path = movie_info[PATH]
    new_path = old_path.replace(current_path, correct_path).rstrip("/\\")

    from_folder_name = movie_info[FOLDER_NAME]
    new_folder_name = from_folder_name.replace(current_path, correct_path).rstrip("/\\")
    try:
        if 'movieFile' in movie_info.keys():
            logger.debug('Trying to move movie "{}" files from "{}" to "{}"'.format(title, old_path, new_path))
            shutil.move(old_path, new_path)
            logger.info('Movie "{}" files moved from "{}" to "{}"'.format(title, old_path, new_path))
        else:
            logger.debug(
                'Movie "{}" has no files. Just updating Radarr (no files to move)'.format(title, old_path, new_path))
        change_movie_path_and_folder(movie_info, new_path, new_folder_name)
        refresh_movie(movie_info)
    except Exception as e:
        logger.error("Couldn't move movie {}; Exception: {}".format(movie_title, e))


def change_movie_path_and_folder(movie_info, new_path, new_folder_name):
    movie_id = movie_info[ID]
    old_path = movie_info[PATH]
    movie_info[PATH] = new_path
    movie_info[FOLDER_NAME] = new_folder_name
    update_response = radarrSession.put('{0}/api/movie/{1}'.format(radarr_url, movie_id),
                                        data=json.dumps(movie_info))
    movie_title = movie_info["title"]
    if update_response.status_code < 300:
        logger.debug(
            "Movie updated succesfully: {} was moved from {} to {}".format(movie_title, old_path, new_path))
    else:
        logger.error("Error while trying to update: {0}".format(movie_title))


def refresh_movie(movie_info):
    movie_id = movie_info[ID]
    title = movie_info["title"]
    command = {"movieId": movie_id, "name": "refreshMovie"}
    refresh_response = radarrSession.post("{0}/api/command".format(radarr_url),
                                          data=json.dumps(command))
    if refresh_response.status_code < 300:
        logger.debug("Movie {} refreshed succesfully".format(title))
    else:
        logger.error("Error while refreshing movie: {}".format(title))


########################################################################################################################
logger = logging.getLogger()
log_level = os.getenv(LOG_LEVEL, "INFO")
logger.setLevel(log_level)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

os.makedirs("./logs", exist_ok=True)
fileHandler = logging.FileHandler("./logs/organizer.log")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
########################################################################################################################

logger.info('RadarrFolderOrganizer Version {} Started!!'.format(VER))

config_parser = configparser.ConfigParser()
config_parser.optionxform = str

# Loads an alternate config file so that I can work on my servers without uploading config to github
settingsFilename = os.path.join(os.getcwd(), 'Config.txt')
config_parser.read(settingsFilename)

radarr_url = config_section_map("Radarr")['url']
radarr_key = config_section_map("Radarr")['key']

# We normalize the path to avoid case inconsistencies when checking the mappings
custom_format_mappings = {key: normalize_path(value) for (key, value) in
                          config_section_map("CustomFormatMappings").items()}
if DEFAULT_MAPPING not in custom_format_mappings:
    logger.error('A default mapping named {} should be provided!!'.format(DEFAULT_MAPPING))
    sys.exit(0)

radarrSession = requests.Session()
radarrSession.headers.update({'x-api-key': radarr_key})
# TODO check if needed
radarrSession.trust_env = False
radarrMovies = radarrSession.get('{0}/api/movie'.format(radarr_url))
if radarrMovies.status_code >= 300:
    logger.error('Movies retrieve returned status code {}'.format(radarrMovies.status_code))
    sys.exit(0)

movies_json = radarrMovies.json()
logger.info('Received {} movies from Radarr'.format(len(movies_json)))
should_move_default = os.getenv(MOVE_DEFAULT_FLAG, 'false').lower() == 'true'
for movie in movies_json:
    title = movie["title"]
    logger.debug('########## Started processing movie: {} ##########'.format(title))
    current_path = get_current_path(movie)
    # We normalize the path to avoid case inconsistencies when checking the mappings
    normalized_current_path = normalize_path(current_path)
    if normalized_current_path not in custom_format_mappings.values():
        logger.warning(
            'Movie "{}" current path is "{}", normalized as "{}" and is not in the configuration file. Skipping to avoid possible errors'.format(
                title, movie['path'], normalized_current_path))
        continue
    correct_path = decide_path(movie, custom_format_mappings)
    if correct_path is None:
        logger.debug('Movie "{}" current path is "{}", correct path is not assigned (no custom format with a customized mapping). Skipping'.format(
                title, movie['path']))
        continue
    if normalized_current_path != correct_path:
        logger.debug(
            'Movie "{}" current path is "{}", normalized as "{}" and doesn\'t match the correct path "{}". Proceeding to move it'.format(
                title, movie['path'], normalized_current_path, correct_path))
        move_movie(movie, current_path, correct_path)
    else:
        logger.debug(
            'Movie "{}" current path is "{}" and matches the correct path "{}". Nothing to do here'.format(
                title,
                movie['path'],
                correct_path))
    logger.debug('########## Finished processing movie: {} ##########'.format(title))

logger.info("Done!!")
