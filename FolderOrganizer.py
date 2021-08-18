import configparser
import json
import logging
import os
import pathlib
import sys
import shutil
import time

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


def get_v2_custom_format_names(movie_info):
    return list(map(lambda e: e["name"], movie_info["movieFile"]["quality"]["customFormats"]))


def get_custom_format_names(movie_info, is_legacy_v2):
    if "movieFile" not in movie_info.keys():
        return list()
    if is_legacy_v2:
        return get_v2_custom_format_names(movie_info)
    movie_file_id = movie_info["movieFile"]["id"]
    movie_file_response = radarr_session.get('{0}/api/v3/movieFile/{1}'.format(radarr_url, movie_file_id))
    if movie_file_response.status_code >= 300:
        logger.error('Movie file retrieval for movie {} returned status code {}'.format(movie_info['title'],
                                                                                        radarr_movies.status_code))
        return list()
    movie_file = movie_file_response.json()
    return list(map(lambda e: e["name"], movie_file["customFormats"]))


def decide_path(movie_info, format_mappings, is_legacy_v2):
    movie_custom_formats = get_custom_format_names(movie_info, is_legacy_v2)
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
    logger.debug(
        'NO MATCHED FORMAT!! Movie "{}": didn\'t match any mapped format. {} flag value is disabled so no new path is assigned !!'.format(
            movie_title, MOVE_DEFAULT_FLAG))
    return None


def get_current_path(movie_info):
    path = pathlib.Path(movie_info[PATH])
    return str(path.parent)


def normalize_path(path):
    normpath = os.path.normpath(path)
    return os.path.normcase(normpath)


def move_movie(movie_info, current, new):
    movie_title = movie_info["title"]
    old_path = movie_info[PATH]
    new_path = old_path.replace(current, new).rstrip("/\\")

    from_folder_name = movie_info[FOLDER_NAME]
    new_folder_name = from_folder_name.replace(current, new).rstrip("/\\")
    try:
        if 'movieFile' in movie_info.keys():
            logger.debug('Trying to move movie "{}" files from "{}" to "{}"'.format(title, old_path, new_path))
            shutil.move(old_path, new_path)
            logger.info('Movie "{}" files moved from "{}" to "{}"'.format(title, old_path, new_path))
        else:
            logger.debug(
                'Movie "{}" has no files. Just updating Radarr (no files to move)'.format(title, old_path, new_path))
        change_movie_path_and_folder(movie_info, new_path, new_folder_name)
        logger.debug("Going to refresh movie {} twice, so Radarr picks up the changes to the folder".format(title))
        refresh_movie(movie_info)
        refresh_movie(movie_info)
    except Exception as e:
        logger.error("Couldn't move movie {}; Exception: {}".format(movie_title, e))


def change_movie_path_and_folder(movie_info, new_path, new_folder_name):
    movie_id = movie_info[ID]
    old_path = movie_info[PATH]
    movie_info[PATH] = new_path
    movie_info[FOLDER_NAME] = new_folder_name
    update_response = radarr_session.put('{0}/api/movie/{1}'.format(radarr_url, movie_id),
                                         data=json.dumps(movie_info))
    movie_title = movie_info["title"]
    if update_response.status_code < 300:
        logger.debug(
            "Movie updated succesfully: {} was moved from {} to {}".format(movie_title, old_path, new_path))
    else:
        logger.error("Error while trying to update: {0}".format(movie_title))


def refresh_movie(movie_info):
    movie_id = movie_info[ID]
    movie_title = movie_info["title"]
    command = {"movieId": movie_id, "name": "refreshMovie"}
    sleep_time = 10
    logger.debug(
        "Waiting {}s before refreshing movie {}, so Radarr has enough time to get the change".format(sleep_time,
                                                                                                     movie_title))
    time.sleep(sleep_time)
    refresh_response = radarr_session.post("{0}/api/command".format(radarr_url),
                                           data=json.dumps(command))
    if refresh_response.status_code < 300:
        logger.debug("Movie {} refreshed succesfully".format(movie_title))
    else:
        logger.error("Error while refreshing movie: {}".format(movie_title))


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
radarr_url = os.getenv("RADARR_URL")
radarr_key = os.getenv("RADARR_KEY")

if radarr_url is None:
    radarr_url = config_section_map("Radarr")['url']

if radarr_key is None:
    radarr_key = config_section_map("Radarr")['key']

# We normalize the path to avoid case inconsistencies when checking the mappings
custom_format_mappings = {key: normalize_path(value) for (key, value) in
                          config_section_map("CustomFormatMappings").items()}
if DEFAULT_MAPPING not in custom_format_mappings:
    logger.error('A default mapping named {} should be provided!!'.format(DEFAULT_MAPPING))
    sys.exit(1)

radarr_session = requests.Session()
radarr_session.headers.update({'x-api-key': radarr_key})
# TODO check if needed
radarr_session.trust_env = False
radarr_status = radarr_session.get('{0}/api/system/status'.format(radarr_url))
status_json = radarr_status.json()
version = status_json['version']
logger.info('Connected to radarr at version {}'.format(version))
isLegacyV2 = version[0] == '2'
if radarr_status.status_code >= 300:
    logger.error('Status retrieve returned status code {}'.format(radarr_status.status_code))
    sys.exit(2)
radarr_movies = radarr_session.get('{0}/api/movie'.format(radarr_url))
if radarr_movies.status_code >= 300:
    logger.error('Movies retrieve returned status code {}'.format(radarr_movies.status_code))
    sys.exit(3)

movies_json = radarr_movies.json()
logger.info('Received {} movies from Radarr'.format(len(movies_json)))
should_move_default = os.getenv(MOVE_DEFAULT_FLAG, 'false').lower() == 'true'
errors_happened = False
for movie in movies_json:
    try:
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
        correct_path = decide_path(movie, custom_format_mappings, isLegacyV2)
        if correct_path is None:
            logger.debug(
                'Movie "{}" current path is "{}", correct path is not assigned (no custom format with a customized mapping). Skipping'.format(
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
    except Exception as e:
        logger.error('An error happened while processing movie {}: {}'.format(movie["title"], repr(e)))
        logger.exception(e)
        errors_happened = True

if errors_happened:
    logger.info("Done with errors!!")
    sys.exit(4)
else:
    logger.info("Done!!")
