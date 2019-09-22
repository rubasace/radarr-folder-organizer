import logging

LOGGER = logging.getLogger('root')

def decide_path(movie, custom_format_mappings, default_mapping):
    movie_custom_formats = get_custom_format_names(movie)
    LOGGER.debug('Movie "{}" has custom formats: {}'.format(movie['title'], movie_custom_formats))
    if len(movie_custom_formats) > 0:
        LOGGER.debug('Custom format mappings: {}'.format(custom_format_mappings))
        for format_name in filter(lambda e: default_mapping != e, custom_format_mappings.keys()):
            LOGGER.debug('Checking if format {} is in movie custom formats {}'.format(format_name, movie_custom_formats))
            if format_name in movie_custom_formats:
                return custom_format_mappings[format_name]
    return custom_format_mappings[default_mapping]


def get_custom_format_names(movie):
    if 'movieFile' not in movie.keys():
        return list()
    return list(map(lambda e: e['name'], movie['movieFile']['quality']['customFormats']))
