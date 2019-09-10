import os
import logging
import requests
import pathlib
import json
import configparser
import sys
import itertools

PATH = "path"

DEFAULT_MAPPING = "__default"

QUALITY = "quality"

CUSTOM_FORMATS = "customFormats"

VER = '0.0.1'

IMPORTED_EVENT_TYPE = "downloadFolderImported"
GRABBED_EVENT_TYPE = "grabbed"
DOWNLOAD_ID = "downloadId"
EVENT_TYPE = "eventType"

def ConfigSectionMap(section):
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


def getCustomFormatNames(movie_info):
    return list(map(lambda e: e["name"], movie_info["movieFile"]["quality"]["customFormats"]))


def decidePath(movie_format_names, custom_format_mappings):
    for format_name in filter(lambda e: DEFAULT_MAPPING != e, custom_format_mappings):
        if(format_name in movie_format_names):
            return custom_format_mappings[format_name]
    return custom_format_mappings[DEFAULT_MAPPING]

def getCurrentPath(movie_info):
    path = pathlib.Path(movie_info[PATH])
    return str(path.parent)
def moveMovie(movie_info, current_path, correct_path):
    logger.debug("Movie {} should go to {}".format(movie["title"], correct_path))


########################################################################################################################
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

fileHandler = logging.FileHandler("./log.txt")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
########################################################################################################################

print(os.environ)


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

radarr_url = ConfigSectionMap("Radarr")['url']
radarr_key = ConfigSectionMap("Radarr")['key']

custom_format_mappings = ConfigSectionMap("CustomFormatMappings")
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

moviesWithFile = filter(lambda e: e.get("movieFile") is not None, radarrMovies.json())

for movie in moviesWithFile:
    movie_format_names = getCustomFormatNames(movie)
    correct_path = decidePath(movie_format_names, custom_format_mappings)
    current_path = getCurrentPath(movie)
    if current_path not in custom_format_mappings.values():
        logger.error("Current path {} from movie {} is not in the configuration file. Skipping to avoid possible errors".format(current_path, movie["title"]))
        continue
    if current_path != correct_path:
        moveMovie(movie, current_path, correct_path)


