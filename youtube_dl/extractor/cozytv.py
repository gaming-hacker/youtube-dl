# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    unified_timestamp,
)


class CozyTVReplayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cozy\.tv/(?P<user>[^/]+)/replays/(?P<id>\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])(?:_\d+)?)'
    _TESTS = [
        {
            'url': 'https://cozy.tv/althype/replays/2022-04-22',
            'md5': '46fb59b29231c816ef4abaa4c54bdbaf',
            'info_dict': {
                'id': '6261fed63f2f1a99756b6923',
                'title': 'Where did the Jews Go?',
                'ext': 'mp4',
                'display_id': '2022-04-22',
                'thumbnail': r're:^https?://.*/replays/althype/2022-04-22/thumb\.webp$',
                'uploader': 'althype',
                'creator': 'althype',
                'release_timestamp': 1650589357,
                'release_date': '20220422',
                'timestamp': 1650589357,
                'upload_date': '20220422',
                'uploader_id': 'althype',
                'uploader_url': 'https://cozy.tv/althype',
                'channel': 'althype',
                'channel_id': 'althype',
                'channel_url': 'https://cozy.tv/althype',
                'duration': 7349,
                'view_count': 804,
                'webpage_url': 'https://cozy.tv/althype/replays/2022-04-22',
            }
        },
        {
            'url': 'https://cozy.tv/beardson/replays/2022-05-01_2',
            'md5': '2f474ea9404fe90ca87a6390a6e10173',
            'info_dict': {
                'id': '626eb2b73f2f1a99756b6a1b',
                'title': '24 HOUR STREAM',
                'ext': 'mp4',
                'display_id': '2022-05-01_2',
                'thumbnail': r're:^https?://.*/replays/beardson/2022-05-01_2/thumb\.webp$',
                'uploader': 'beardson',
                'creator': 'beardson',
                'release_timestamp': 1651421852,
                'release_date': '20220501',
                'timestamp': 1651421852,
                'upload_date': '20220501',
                'uploader_id': 'beardson',
                'uploader_url': 'https://cozy.tv/beardson',
                'channel': 'beardson',
                'channel_id': 'beardson',
                'channel_url': 'https://cozy.tv/beardson',
                'duration': 313,
                'view_count': 656,
                'webpage_url': 'https://cozy.tv/beardson/replays/2022-05-01_2',
            }
        }
    ]

    def _real_extract(self, url):
        video_id, user = re.match(self._VALID_URL, url).group('id', 'user')
        data = self._download_json('https://api.cozy.tv/cache/%s/replay/%s' % (user, video_id), video_id)

        cdn_url = '/'.join((data['cdns'][0], 'replays', user, video_id))
        user_url = 'https://cozy.tv/' + user

        info = {
            'id': data.get('_id') or video_id,
            'title': data['title'],
        }

        timestamp = unified_timestamp(data.get('date'))
        formats = self._extract_m3u8_formats(cdn_url + '/index.m3u8', video_id, ext='mp4', m3u8_id='hls')
        self._sort_formats(formats)

        info.update({
            'channel': user,
            'channel_id': user,
            'channel_url': user_url,
            'creator': user,
            'display_id': video_id,
            'duration': float_or_none(data.get('duration')),
            'formats': formats,
            'release_timestamp': timestamp,
            'thumbnail': cdn_url + '/thumb.webp',
            'timestamp': timestamp,
            'uploader': user,
            'uploader_id': user,
            'uploader_url': user_url,
            'view_count': int_or_none(data.get('peakViewers')),
            'webpage_url': url,
        })

        return info
