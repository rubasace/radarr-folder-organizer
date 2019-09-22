import logging

LOGGER = logging.getLogger('root')


def get_movies(radarr_url, radarr_session):
    radarr_movies = radarr_session.get('{0}/api/movie'.format(radarr_url))
    if radarr_movies.status_code >= 300:
        LOGGER.error('Movies retrieve returned status code {}'.format(radarr_movies.status_code))
        raise ConnectionError("Cannot retrieve movies")
    return radarr_movies.json()


def refresh_movie(movie_info, radarr_url, radarr_session):
    movie_id = movie_info['movieId']
    title = movie_info['title']
    command = {'movieId': movie_id, 'name': 'refreshMovie'}
    refresh_response = radarr_session.post("{0}/api/command".format(radarr_url),
                                          data=json.dumps(command))
    if refresh_response.status_code < 300:
        LOGGER.debug('Movie "{}" refreshed successfully in Radarr'.format(title))
    else:
        LOGGER.error('Error while refreshing movie: {}'.format(title))


def update_movie_folder(movie_info, new_path, new_folder_name, radarr_url, radarr_session):
    movie_id = movie_info['movieId']
    old_path = movie_info['path']
    movie_info['path'] = new_path
    movie_info['folderName'] = new_folder_name
    update_response = radarr_session.put('{0}/api/movie/{1}'.format(radarr_url, movie_id),
                                        data=json.dumps(movie_info))
    if update_response.status_code < 300:
        LOGGER.info(
            'Movie info for "{}" updated successfully: it was moved from {} to {}'.format(movie_info['title'], old_path, new_path))
    else:
        LOGGER.error("Error while trying to update: {0}".format(movie_info['title']))