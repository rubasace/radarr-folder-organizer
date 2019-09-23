# Radarr Folder Organizer

[![docker-data](https://images.microbadger.com/badges/image/rubasace/radarr-folder-organizer.svg)](https://microbadger.com/images/rubasace/radarr-folder-organizer "Get your own image badge on microbadger.com")

[![Code Quality](https://api.codacy.com/project/badge/Grade/81401147bff34a15b092ca86f7c0beb9)](https://www.codacy.com/manual/rubasace/radarr-folder-organizer?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=rubasace/radarr-folder-organizer&amp;utm_campaign=Badge_Grade)
## Description
Radarr Folder Organizer assignes folders to movies given their custom formats, moving the files to the desired folder and updating Radarr to reflect such changes.

## Why
Radarr custom formats are very useful for use cases such as downloading a movie in original version as soon as it's available and upgrading it once a Dual version is released.
Radarr doesn't support the assignment of alternative folders for custom formats. This script solves that, checking the custom formats of each downloaded movie in the Radarr library and changing it's folder to the desired one.

## Configuration
### Example Config.txt
```ini
[Radarr]
url = http://changeme.com:3333
key = 4384803r2808rvsvj023r9fjvvd0fjv3
[CustomFormatMappings]
__default = /the/default/folder 
custom_format1 = /custom/format/1/folder
custom_format2 = /custom/format/2/folder
```
### Configuration steps
 1. Copy the `Config.example.txt` file into `Config.txt` file under the same directory
 2. Edit the `Config.txt` file and replace your servers URL and API key for Radarr under the ``[Radarr]`` section.
 3. Edit the `Config.txt` file and replace the ``__default`` mapping with the default folder for Radarr movies under the ``[CustomFormatMappings]`` section (mandatory).
 4. Edit the `Config.txt` file and add any other mapping for the custom formats just bellow the ``__default`` one, where the key is the custom format name (case sensitive) and the value is the desired folder for such format. Both key and value allow spaces.

## How to Run
### Standalone
Recomended to run using cron every 15 minutes or an interval of your preference.
```bash
pip install -r requirements.txt
python FolderOrganizer.py
```
If running on Windows and getting the error `ImportError : no module named 'requests'` you'll need to install the requirements via the `python` command.
```bash
python -m pip install -r requirements.txt
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
        -e LOG_LEVEL=INFO \
        rubasace/radarr-folder-organizer
```
## Unknown Folders
This script will only affect movies that are located in folders explicitly included in the `Config.txt`. In case any movie is found in another folder you'll receive the message `Current path ${Path} from movie ${MovieName} is not in the configuration file. Skipping to avoid possible errors`.

If you want those movies to be moved by the script you can add another for it (the custom format doesn't need to exist). 

### Example
Assuming the example  `Config.txt` file, if receive the message `Current path /media/cool_movies from movie Deadpool (2016) is not in the configuration file. Skipping to avoid possible errors`, you can add a line for the new folder, such as:
```ini
[CustomFormatMappings]
__default = /the/default/folder 
custom_format1 = /custom/format/1/folder
custom_format2 = /custom/format/2/folder
whatever_you_want = /media/cool_movies
```

## Requirements
* Python 3.4 or greater
* Radarr server

## Troubleshooting
Log level is set to INFO by default, with the bare minimum information logged. In case of an issue it's recommended to set the log level to DEBUG. Feel free to open an issue if something is not working as expected.

## Notes
* Radarr Folder Organizer will try to move your files and abort the movie update if it can't, so it should have access to the movies library files.
* When using Docker, be sure that the mounted volume is the same as the Radarr one