"""TMDB API client.

Notes
-----
For looser coupling, external packages should probably use the
shortcut functions defined in shortcuts.py.
"""

import os
import warnings
from typing import List

import requests

from django.conf import settings
from tmdb.pagination import collect_paginated_results
from .parsers.shows import ShowParser
from .datatypes import Show


class TMDBClient:
    """Client for interacting with the TMDB API."""

    LANGUAGE = 'en-US'
    ROOT_URL = 'https://api.themoviedb.org/3'

    show_parser_class = ShowParser

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _build_url(self, endpoint: str) -> str:
        """Build the full URL from an endpoint.

        Example:
        _build_url('search/tv') -> 'https://api.themoviedb.org/3/search/tv'
        """
        parts = (self.ROOT_URL, endpoint)
        return '/'.join(part.strip('/') for part in parts)

    def _request(self, endpoint: str, params: dict = None,
                 raise_for_status: bool = True) -> requests.Response:
        """Perform a request to the API.

        :param endpoint: str
        :param params: dict
            GET parameters passed to the underlying call to `requests.get()`.
        :param raise_for_status: bool, optional
            If True (the default), an exception is raised if the response
            has an error status code (400 or greater).
            See Requests' full documentation on status codes:
            http://docs.python-requests.org/en/master/user/quickstart/#response-status-codes
        :returns response
        """
        if params is None:
            params = {}

        # Attach the API key and language if not given
        params.setdefault('api_key', self.api_key)
        params.setdefault('language', self.LANGUAGE)

        url = self._build_url(endpoint)
        resp = requests.get(url, params=params)

        if raise_for_status:
            resp.raise_for_status()

        return resp

    def _get_show_parser(self) -> ShowParser:
        return self.show_parser_class()

    def search_show(self, title: str) -> List[Show]:
        """Search the title in the API to find corresponding TV shows.

        Note: only the first page of results is returned; support for
        pagination could be added in the future.

        :param title: string
        :return: list of Show objects
        """
        resp = self._request('search/tv', {
            'query': title,
            'page': 1,
        })
        content: dict = resp.json()
        parser = self._get_show_parser()
        shows = [parser.for_list(result) for result in content['results']]
        return shows

    def retrieve_show(self, show_id: int) -> Show:
        """Retrieve details of a show.

        :param show_id: id of the show in the API.
        :return: a Show object
        """
        resp = self._request(f'tv/{show_id}')
        data: dict = resp.json()
        parser = self._get_show_parser()
        return parser.for_detail(data)

    def get_airing_today_ids(self) -> List[int]:
        """Retrieve IDs of shows airing today.

        Notes
        -----
        Results from the TMDB API are paginated (20 items/page),
        so one request per page is performed to retrieve the complete list.
        As a result, calling this method is typically slow (1s per page).
        """
        return collect_paginated_results(
            fetch_page=lambda page: self._request('tv/airing_today', {
                'page': page,
                # Results differ by timezone, use the one configured
                # on this server.
                'timezone': settings.TIME_ZONE,
            }),
            total_pages=lambda data: data['total_pages'],
            extract=lambda data: [show['id'] for show in data['results']],
        )


def get_tmdb_client(api_key: str = None) -> TMDBClient:
    """Build and return a TMDB client.

    :param api_key: str, optional
        If not given, the API key is retrieved from the TMDB_API_KEY
        environment variable.
        If the environment variable is not set, raises a warning.
    :return client: TMDBClient
    :raises UserWarning:
        If the TMDB_API_KEY environment variable is not set,
        but it was used to build the client.
    """
    if api_key is None:
        api_key = os.getenv('TMDB_API_KEY')
        if api_key is None:
            message = (
                'TMDB_API_KEY environment variable not set! Requests to '
                'the TMDB API will most likely fail.'
            )
            warnings.warn(message)
    return TMDBClient(api_key=api_key)


# Provide a default global TMDB client for convenience
tmdb_client = get_tmdb_client()
