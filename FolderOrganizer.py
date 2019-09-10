import os
import logging
import requests
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
    return movie_info[PATH]


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
    path = decidePath(movie_format_names, custom_format_mappings)
    logger.debug("Movie {} should go to {}".format(movie["title"], path))

    # movieRecords = list(group)
    # # Not enough information so pointless to continue (at least we need one grabbed and one imported event)
    # if len(movieRecords) < 2:
    #     continue
    # downloadId = ""
    # grabbedCustomFormats = None
    # movieRecords.sort(key=lambda e: e["date"], reverse=True)
    # for movieRecord in movieRecords:
    #     recordDownloadId = movieRecord.get(DOWNLOAD_ID, "")
    #     if downloadId:
    #         if downloadId == recordDownloadId and GRABBED_EVENT_TYPE == movieRecord[EVENT_TYPE]:
    #             quality = movieRecord.get(QUALITY, {CUSTOM_FORMATS: None})
    #             grabbedCustomFormats = quality.get(CUSTOM_FORMATS, None)
    #             break
    #     elif IMPORTED_EVENT_TYPE == movieRecord[EVENT_TYPE]:
    #         downloadId = recordDownloadId
    #         quality = movieRecord.get(QUALITY, {CUSTOM_FORMATS: None})
    #         currentCustomFormats = quality.get(CUSTOM_FORMATS, None)
    # if grabbedCustomFormats is not None:
    #     movieInfo = movieIdInfoMap[movieId]
    #     currentFile = movieInfo.get("movieFile", None)
    #     if currentFile is None:
    #         logger.debug("Movie file not found for movie: {}".format(movieInfo["title"]))
    #     elif grabbedCustomFormats != currentFile["quality"]["customFormats"]:
    #         movieFile = movieInfo["movieFile"]
    #         movieFileId = movieFile["id"]
    #         movieFile["quality"]["customFormats"] = grabbedCustomFormats
    #         updateResponse = radarrSession.put('{0}/api/movieFile/{1}?apikey={2}'.format(radarr_url, movieFileId, radarr_key),
    #                                            data=json.dumps(movieFile))
    #         if updateResponse.status_code < 300:
    #             logger.debug("Movie {0} updated succesfully: {1}".format(movieInfo["title"], grabbedCustomFormats))
    #         else:
    #             logger.debug("Error while trying to update: {0}".format(movieInfo["title"]))


