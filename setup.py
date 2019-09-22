#!/usr/bin/env python

import distutils.core.setup

install_requires = [
    'requests==2.22.0',
    'configparser==4.0.2'
    ]

tests_require = [
    'pytest'
    ]

distutils.core.setup(name='RadarrFolderOrganizer',
      version='0.9.0',
      description='Automatically organize Radarr folders given custom formats ',
      author='Ruben Pahino Verdugo',
      author_email='rubasodin18@gmail.com',
      url='https://github.com/rubasace/radarr-folder-organizer',
      packages=['radarr_folder_organizer'],
      install_requires=install_requires,
      tests_require=tests_require

     )