# -*- coding: utf-8 -*-
'''
A module that adds data to the Pillar structure retrieved by an http request


Configuring the HTTP_YAML ext_pillar
====================================

Set the following Salt config to setup an http endpoint as the external pillar source:

.. code-block:: yaml

  ext_pillar:
    - http_yaml:
        url: http://example.com/api/minion_id
        ::TODO::
        username: username
        password: password

If the with_grains parameter is set, grain keys wrapped in can be provided (wrapped
in <> brackets) in the url in order to populate pillar data based on the grain value.

.. code-block:: yaml

  ext_pillar:
    - http_yaml:
        url: http://example.com/api/<nodename>
        with_grains: True

.. versionchanged:: Oxygen

    If %s is present in the url, it will be automaticaly replaced by the minion_id:

    .. code-block:: yaml

        ext_pillar:
          - http_json:
              url: http://example.com/api/%s

Module Documentation
====================
'''

# Import python libs
from __future__ import absolute_import
import logging
import re

# Import Salt libs
try:
    from salt.ext.six.moves.urllib.parse import quote as _quote
    _HAS_DEPENDENCIES = True
except ImportError:
    _HAS_DEPENDENCIES = False


# Set up logging
_LOG = logging.getLogger(__name__)


def __virtual__():
    return _HAS_DEPENDENCIES


def ext_pillar(minion_id,
               pillar,  # pylint: disable=W0613
               url,
               with_grains=False):
    '''
    Read pillar data from HTTP response.

    :param str url: Url to request.
    :param bool with_grains: Whether to substitute strings in the url with their grain values.

    :return: A dictionary of the pillar data to add.
    :rtype: dict
    '''

    url = url.replace('%s', _quote(minion_id))

    grain_pattern = r'<(?P<grain_name>.*?)>'

    if with_grains:
        # Get the value of the grain and substitute each grain
        # name for the url-encoded version of its grain value.
        for match in re.finditer(grain_pattern, url):
            grain_name = match.group('grain_name')
            grain_value = __salt__['grains.get'](grain_name, None)

            if not grain_value:
                _LOG.error("Unable to get minion '%s' grain: %s", minion_id, grain_name)
                return {}

            grain_value = _quote(str(grain_value))
            url = re.sub('<{0}>'.format(grain_name), grain_value, url)

    _LOG.debug('Getting url: %s', url)
    data = __salt__['http.query'](url=url, decode=True, decode_type='yaml')

    if 'dict' in data:
        return data['dict']

    _LOG.error("Error on minion '%s' http query: %s\nMore Info:\n", minion_id, url)

    for key in data:
        _LOG.error('%s: %s', key, data[key])

    return {}
