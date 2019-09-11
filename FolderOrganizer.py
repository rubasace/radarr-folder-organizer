import configparser
import json
import logging
import os
import pathlib
import sys
import shutil

import requests

VER = '0.0.1'

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


def config_section_map(section):
    dict1 = {}
    options = configParser.options(section)
    for option in options:
        try:
            dict1[option] = configParser.get(section, option)
            if dict1[option] == -1:
                logger.debug("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


def get_custom_format_names(movie_info):
    if "movieFile" not in movie_info.keys():
        return list()
    return list(map(lambda e: e["name"], movie_info["movieFile"]["quality"]["customFormats"]))


def decide_path(movie_format_names, custom_format_mappings):
    for format_name in filter(lambda e: DEFAULT_MAPPING != e, custom_format_mappings):
        if (format_name in movie_format_names):
            return custom_format_mappings[format_name]
    return custom_format_mappings[DEFAULT_MAPPING]


def get_current_path(movie_info):
    path = pathlib.Path(movie_info[PATH])
    return str(path.parent)


def move_movie(movie_info, current_path, correct_path):
    title = movie_info["title"]
    old_path = movie_info[PATH]
    new_path = old_path.replace(current_path, correct_path).rstrip("/")

    from_folder_name = movie_info[FOLDER_NAME]
    new_folder_name = from_folder_name.replace(current_path, correct_path).rstrip("/")
    try:
        if "movieFile" in movie_info.keys():
            shutil.move(old_path, new_path)
            logger.debug("Movie {} files moved from {} to {}".format(title, old_path, new_path))
        change_movie_path_and_folder(movie_info, new_path, new_folder_name)
        refresh_movie(movie_info)
    except Exception as e:
        logger.error("Couldn't move movie {}; Exception: {}".format(title, e))


def change_movie_path_and_folder(movie_info, new_path, new_folder_name):
    movie_id = movie_info[ID]
    old_path = movie_info[PATH]
    movie_info[PATH] = new_path
    movie_info[FOLDER_NAME] = new_folder_name
    update_response = radarrSession.put('{0}/api/movie/{1}?apikey={2}'.format(radarr_url, movie_id, radarr_key),
                                        data=json.dumps(movie_info))
    if update_response.status_code < 300:
        logger.debug(
            "Movie updated succesfully: {} was moved from {} to {}".format(movie_info["title"], old_path, new_path))
    else:
        logger.error("Error while trying to update: {0}".format(movie_info["title"]))


def refresh_movie(movie_info):
    movie_id = movie_info[ID]
    title = movie_info["title"]
    command = {"movieId": movie_id, "name": "refreshMovie"}
    refresh_response = radarrSession.post("{0}/api/command?apikey={1}".format(radarr_url, radarr_key),
                                          data=json.dumps(command))
    if refresh_response.status_code < 300:
        logger.debug("Movie {} refreshed succesfully".format(title))
    else:
        logger.error("Error while refreshing movie: {}".format(title))


########################################################################################################################
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

os.mkdir("./logs")
fileHandler = logging.FileHandler("./logs/organizer.log")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
########################################################################################################################

logger.debug('CustomFormatSync Version {}'.format(VER))

configParser = configparser.ConfigParser()
configParser.optionxform = str

# Loads an alternate config file so that I can work on my servers without uploading config to github
if "DEV" in os.environ:
    settingsFilename = os.path.join(os.getcwd(), 'dev/'
                                                 'Config.txt')
else:
    settingsFilename = os.path.join(os.getcwd(), 'Config.txt')
configParser.read(settingsFilename)

radarr_url = config_section_map("Radarr")['url']
radarr_key = config_section_map("Radarr")['key']

custom_format_mappings = config_section_map("CustomFormatMappings")
if DEFAULT_MAPPING not in custom_format_mappings:
    logger.error('A default mapping should be provided!!')
    sys.exit(0)

radarrSession = requests.Session()
# TODO check if needed
radarrSession.trust_env = False
radarrMovies = radarrSession.get('{0}/api/movie?apikey={1}'.format(radarr_url, radarr_key))
if radarrMovies.status_code >= 300:
    logger.error('Movies retrieve returned status code {}'.format(radarrMovies.status_code))
    sys.exit(0)

movies_moved = 0
for movie in radarrMovies.json():
    movie_format_names = get_custom_format_names(movie)
    correct_path = decide_path(movie_format_names, custom_format_mappings)
    current_path = get_current_path(movie)
    if current_path not in custom_format_mappings.values():
        logger.warning(
            "Current path {} from movie {} is not in the configuration file. Skipping to avoid possible errors".format(
                current_path, movie["title"]))
        continue
    if current_path != correct_path:
        move_movie(movie, current_path, correct_path)
        movies_moved += 1

logger.info("Movies moved: {}".format(movies_moved))
