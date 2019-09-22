import logging

LOGGER = logging.getLogger("root")


def load_section(config_parser, section):
    dict1 = {}
    options = config_parser.options(section)
    for option in options:
        try:
            dict1[option] = config_parser.get(section, option)
            if dict1[option] == -1:
                LOGGER.debug("skip: {}".format(option))
        except Exception:
            LOGGER.error("exception on {}!".format(option))
            dict1[option] = None
    return dict1
