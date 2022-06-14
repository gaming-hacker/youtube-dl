# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from ..compat import (
    compat_str,
)
from ..utils import (
    sanitize_url,
)

class ThisVidIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisvid\.com/(?P<type>videos|embed)/(?P<id>[A-Za-z0-9-]+/?)'
    _TESTS = [{
        'url': 'https://thisvid.com/videos/big-man-walking26/',
        'md5': '74a11cac6a738f28c1a37945145a3f96',
        'info_dict': {
            'id': '2123318',
            'ext': 'mp4',
            'title': 'Big Man Walking26',
            'thumbnail': 'https://media.thisvid.com/contents/videos_screenshots/2123000/2123318/preview.mp4.jpg',
            'age_limit': 18,
        }
    }, {
        'url': 'https://thisvid.com/embed/2123318/',
        'md5': '74a11cac6a738f28c1a37945145a3f96',
        'info_dict': {
            'id': '2123318',
            'ext': 'mp4',
            'title': 'Big Man Walking26',
            'thumbnail': 'https://media.thisvid.com/contents/videos_screenshots/2123000/2123318/preview.mp4.jpg',
            'age_limit': 18,
        }
    }]

    def _real_extract(self, url):
        main_id, type_ = re.match(self._VALID_URL, url).group('id', 'type')
        webpage = self._download_webpage(url, main_id)

        # URL decryptor was reversed from version 4.0.4, later verified working with 5.0.1
        kvs_version = self._html_search_regex(r'<script [^>]+?src="https://thisvid\.com/player/kt_player\.js\?v=(\d+(\.\d+)+)">', webpage, 'kvs_version', fatal=False)
        if not (kvs_version and kvs_version.startswith('5.')):
            self.report_warning("Major version change (" + kvs_version + ") in player engine--Download may fail.")

        title = self._html_search_regex(r'<title\b[^>]*?>(?:Video:\s+)?(.+?)(?:\s+-\s+ThisVid(?:\.com| tube))?</title>', webpage, 'title')
        # video_id, video_url and license_code from the 'flashvars' JSON object:
        video_id = self._html_search_regex(r"video_id:\s+'([0-9]+)',", webpage, 'video_id')
        video_url = self._html_search_regex(r"video_url:\s+'(function/0/.+?)',", webpage, 'video_url')
        license_code = self._html_search_regex(r"license_code:\s+'([0-9$]{16})',", webpage, 'license_code')
        thumbnail = self._html_search_regex(r"preview_url:\s+'((?:https?:)?//media\.thisvid\.com/.+?\.jpg)',", webpage, 'thumbnail', fatal=False)
        uploader = self._html_search_regex(r'<span>Added by: </span><a class="author" href="https://thisvid.com/members/[0-9]+/">(.+?)</a>', webpage, 'uploader')
        uploader_id = self._html_search_regex(r'<span>Added by: </span><a class="author" href="https://thisvid.com/members/([0-9]+)/">.+?</a>', webpage, 'uploader_id')
        thumbnail = sanitize_url(thumbnail)
        if (re.match(self._VALID_URL, url).group('type') == "videos"):
            display_id = main_id
        else:
            display_id = self._search_regex(r'<link\s+rel\s*=\s*"canonical"\s+href\s*=\s*"%s"' % (self._VALID_URL, ), webpage, 'display_id', fatal=False)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'url': getrealurl(video_url, license_code),
            'thumbnail': thumbnail,
            'age_limit': 18,
        }


def getrealurl(video_url, license_code):
    urlparts = video_url.split('/')[2:]
    license = getlicensetoken(license_code)
    newmagic = urlparts[5][:32]

    for o in range(len(newmagic) - 1, -1, -1):
        new = ''
        l = (o + sum([int(n) for n in license[o:]])) % 32

        for i in range(0, len(newmagic)):
            idx = i
            if idx == o:
                idx = l
            elif idx == l:
                idx = o
            new += newmagic[idx]
        newmagic = new

    urlparts[5] = newmagic + urlparts[5][32:]
    return "/".join(urlparts)


def getlicensetoken(license):
    modlicense = license.replace("$", "").replace("0", "1")
    center = len(modlicense) // 2
    fronthalf = int(modlicense[:center + 1])
    backhalf = int(modlicense[center:])

    modlicense = compat_str(4 * abs(fronthalf - backhalf))
    retval = ''
    for o in range(0, center + 1):
        for i in range(1, 5):
            retval += compat_str((int(license[o + i]) + int(modlicense[o])) % 10)
    return retval
