# Radarr Folder Organizer

[![docker-data](https://images.microbadger.com/badges/image/rubasace/radarr-folder-organizer.svg)](https://microbadger.com/images/rubasace/radarr-folder-organizer "Get your own image badge on microbadger.com")

## Description
Radarr Folder Organizer assignes folders to movies given their custom formats, moving the files to the desired folder and updating Radarr to reflect such changes.

## Why?
Radarr custom formats are very useful for use cases such as downloading a movie in original version as soon as it's available and upgrading it once a Dual version is released.
Radarr doesn't support the assignment of alternative folders for custom formats. This script solves that, checking the custom formats of each downloaded movie in the Radarr library and changing it's folder to the desired one.

## Configuration
### Example Config.txt:
```ini
[Radarr]
url = http://changeme.com:3333
key = 4384803r2808rvsvj023r9fjvvd0fjv3
[CustomFormatMappings]
__default = /the/default/folder #Default folder if movie doesn't have other custom format especified here (mandatory)
custom_format1 = /custom/format/1/folder #movies with custom_format1 will go to folder  /custom/format/1/folder
custom_format2 = /custom/format/2/folder #movies with custom_format2 will go to folder  /custom/format/2/folder
```
### Configuration steps:
1. Edit the Config.txt file and replace your servers URL and API key for Radarr under the ``[Radarr]`` section.
2. Edit the Config.txt file and replace the ``__default`` mapping with the default folder for Radarr movies under the ``[Radarr]`` section (mandatory).
3. Edit the Config.txt file and add any other mapping for the custom formats just bellow the ``__default``, where the key is the custom format name (case sensitive and spaces not allowed) and the value is the desired folder for such format.

## How to Run
### Standalone
Recomended to run using cron every 15 minutes or an interval of your preference.
```bash
pip install -r requirements.txt
python FolderOrganizer.py
```
### Docker
```bash
docker run -d --name radarr-folder-organizer \
        --restart=unless-stopped \
        -v /path/to/Config.txt:/Config.txt \
        -v /path/to/logs:/logs \
        -v /your/media/folder:/same/media/folder/as/radarr:shared \
        -e DELAY=15m \
        rubasace/radarr-folder-organizer
```
## Requirements
 * Python 3.4 or greater
 * Radarr server

## Notes
 * Radarr Folder Organizer will try to move your files and abort the movie update if it can't, so it should have access to the movies library files.