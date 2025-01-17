# coding: utf-8
from __future__ import unicode_literals

import itertools

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    clean_html,
    ExtractorError,
    float_or_none,
    int_or_none,
    try_get,
    urlencode_postdata,
)


class CiscoLiveBaseIE(InfoExtractor):
    # These appear to be constant across all Cisco Live presentations
    # and are not tied to any user session or event
    RAINFOCUS_API_URL = 'https://events.rainfocus.com/api/%s'
    RAINFOCUS_API_PROFILE_ID = ''  # if blank will be fetched at runtime from site javascript
    RAINFOCUS_WIDGET_ID = ''  # if blank will be fetched at runtime from site javascript
    RAINFOCUS_TOKENS_URL = 'https://cdn-events.rainfocus.com/pages/cisco/clondemand/catalog.js'
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/5647924234001/SyK2FdqjM_default/index.html?videoId=%s'

    HEADERS = {
        'Origin': 'https://ciscolive.com',
        'rfApiProfileId': RAINFOCUS_API_PROFILE_ID,
        'rfWidgetId': RAINFOCUS_WIDGET_ID,
    }

    def _call_api(self, ep, rf_id, query, referrer, note=None):
        headers = self.HEADERS.copy()
        headers['Referer'] = referrer
        if not self.RAINFOCUS_API_PROFILE_ID and not self.RAINFOCUS_WIDGET_ID:
            rf_token_js = self._download_webpage(self.RAINFOCUS_TOKENS_URL, 'catalog.js', headers=headers)
            if "apiToken" not in rf_token_js:
                raise ExtractorError(
                    'Unable to fetch api profile (apiToken) value.', expected=True)
            if "widgetId" not in rf_token_js:
                raise ExtractorError(
                    'Unable to fetch widgetId value', expected=True)
            api_token = self._html_search_regex(
                r'(?:apiToken): \'(\w+)\',', rf_token_js, 'apiToken')
            widget_id = self._html_search_regex(
                r'(?:widgetId): \'(\w+)\',', rf_token_js, 'widgetId')
            if api_token and widget_id:
                headers['rfApiProfileId'] = api_token
                headers['rfWidgetId'] = widget_id
        return self._download_json(
            self.RAINFOCUS_API_URL % ep, rf_id, note=note,
            data=urlencode_postdata(query), headers=headers)

    def _parse_rf_item(self, rf_item):
        event_name = rf_item.get('eventName')
        title = rf_item['title']
        description = clean_html(rf_item.get('abstract'))
        presenter_name = try_get(rf_item, lambda x: x['participants'][0]['fullName'])
        bc_id = rf_item['videos'][0]['url']
        bc_url = self.BRIGHTCOVE_URL_TEMPLATE % bc_id
        duration = float_or_none(try_get(rf_item, lambda x: x['times'][0]['length']))
        location = try_get(rf_item, lambda x: x['times'][0]['room'])

        if duration:
            duration = duration * 60

        return {
            '_type': 'url_transparent',
            'url': bc_url,
            'ie_key': 'BrightcoveNew',
            'title': title,
            'description': description,
            'duration': duration,
            'creator': presenter_name,
            'location': location,
            'series': event_name,
        }


class CiscoLiveSessionIE(CiscoLiveBaseIE):
    _VALID_URL = r'https?://(?:www\.)?ciscolive\.com/[^#]*#/session/(?P<id>[^/?&]+)'
    _TESTS = [{
        'url': 'https://www.ciscolive.com/on-demand/on-demand-library.html?search=#/session/16360600004400017rMx',
        'md5': 'e0f5b0b2927b586ebff619294fec6926',
        'info_dict': {
            'id': '6128601216001',
            'ext': 'mp4',
            'title': 'A Deeper Dive into the Telco Cloud Architecture Evolution to support 5G and MEC - BRKSPG-1565',
            'description': 'md5:04bc54ec8ede2bbd9d21264bfaf16cb3',
            'timestamp': 1580474594,
            'upload_date': '20200131',
            'uploader_id': '5647924234001',
        },
    }, {
        'url': 'https://www.ciscolive.com/global/on-demand-library.html?search.event=ciscoliveemea2019#/session/15361595531500013WOU',
        'only_matching': True,
    }, {
        'url': 'https://www.ciscolive.com/global/on-demand-library.html?#/session/1490051371645001kNaS',
        'only_matching': True,
    }, {
        'url': 'https://www.ciscolive.com/on-demand/on-demand-library.html?#/session/16360600774720017Iby',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        rf_id = self._match_id(url)
        rf_result = self._call_api('session', rf_id, {'id': rf_id}, url)
        if int(rf_result['responseCode']) != 0:
            raise ExtractorError(
                'Rainfocus session api returned a non success responseCode: %s. api keys might be invalid' % rf_result['responseCode'], expected=True)
        return self._parse_rf_item(rf_result['items'][0])


class CiscoLiveSearchIE(CiscoLiveBaseIE):
    _VALID_URL = r'https?://(?:www\.)?ciscolive\.com/(?:global|on-demand/)?on-demand-library(?:\.html|/)'
    _TESTS = [{
        'url': 'https://www.ciscolive.com/on-demand/on-demand-library.html?search.event=1636046385176005FbBU&search.technology=scpsTechnology_dataCenter&search.technicallevel=scpsSkillLevel_aintroductory#/',
        'info_dict': {
            'title': 'Search query',
        },
        'playlist_count': 3,  # example returns 4 results, only 3 have video
    }, {
        'url': 'https://www.ciscolive.com/on-demand/on-demand-library.html?search.technology=scpsTechnology_automation&search.technicallevel=scpsSkillLevel_cadvanced#/',
    }, {
        'url': 'https://www.ciscolive.com/global/on-demand-library.html?search.technicallevel=scpsSkillLevel_aintroductory&search.event=ciscoliveemea2019&search.technology=scpsTechnology_dataCenter&search.focus=scpsSessionFocus_bestPractices#/',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if CiscoLiveSessionIE.suitable(url) else super(CiscoLiveSearchIE, cls).suitable(url)

    @staticmethod
    def _check_bc_id_exists(rf_item):
        return int_or_none(try_get(rf_item, lambda x: x['videos'][0]['url'])) is not None

    def _entries(self, query, url):
        query['size'] = 50
        query['from'] = 0
        for page_num in itertools.count(1):
            results = self._call_api(
                'search', None, query, url,
                'Downloading search JSON page %d' % page_num)
            if int(results['totalSearchItems']) == 0:
                raise ExtractorError(
                    'Search api returned 0 items (if matches are expected rfApiProfileId may be invalid)',
                    expected=True)
            sl = try_get(results, lambda x: x['sectionList'][0], dict)
            if sl:
                results = sl
            items = results.get('items')
            if not items or not isinstance(items, list):
                break
            for item in items:
                if not isinstance(item, dict):
                    continue
                if not self._check_bc_id_exists(item):
                    continue
                yield self._parse_rf_item(item)
            size = int_or_none(results.get('size'))
            if size is not None:
                query['size'] = size
            total = int_or_none(results.get('total'))
            if total is not None and query['from'] + query['size'] > total:
                break
            query['from'] += query['size']

    def _real_extract(self, url):
        query = compat_parse_qs(compat_urllib_parse_urlparse(url).query)
        query['type'] = 'session'
        return self.playlist_result(
            self._entries(query, url), playlist_title='Search query')
