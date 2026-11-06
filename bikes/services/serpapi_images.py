"""Search bike images with SerpApi (Google Images engine)."""
import logging
import time
import mimetypes
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

SERPAPI_URL = 'https://serpapi.com/search.json'
TIMEOUT = 40
RETRIES = 3


class SerpApiError(Exception):
    """fatal=True means retrying other bikes is pointless (bad key, no credits)."""

    def __init__(self, message, fatal=False):
        super().__init__(message)
        self.fatal = fatal


def build_query(bike):
    """Build the search text from the bike's details."""
    parts = [bike.brand.name, bike.model_name]
    if bike.engine_cc:
        parts.append(f'{bike.engine_cc}cc')
    parts.append('bike' if bike.fuel_type == 'Petrol' else 'electric scooter')
    return ' '.join(parts)


def search_images(query, limit=5):
    """Return a list of dicts: {'url', 'thumbnail', 'title'} for the query."""
    api_key = getattr(settings, 'SERPAPI_API_KEY', '')
    if not api_key:
        raise SerpApiError('SERPAPI_API_KEY is not set in .env', fatal=True)

    params = {
        'engine': 'google_images',
        'q': query,
        'api_key': api_key,
        'gl': 'in',
        'hl': 'en',
        'safe': 'active',
        'imgsz': 'l',
        'tbs': 'itp:photo',
    }
    data = None
    last_exc = None
    for attempt in range(1, RETRIES + 1):
        try:
            resp = requests.get(SERPAPI_URL, params=params, timeout=TIMEOUT)
            if resp.status_code in (401, 403):
                raise SerpApiError('SerpApi rejected the API key', fatal=True)
            resp.raise_for_status()
            data = resp.json()
            break
        except SerpApiError:
            raise
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(2 * attempt)
    if data is None:
        raise SerpApiError(f'SerpApi request failed after {RETRIES} tries: {last_exc}')

    if data.get('error'):
        msg = str(data['error'])
        fatal = any(k in msg.lower() for k in ('invalid api key', 'run out of searches', 'limit'))
        if 'any results' in msg.lower():
            return []
        raise SerpApiError(msg, fatal=fatal)

    return [
        {
            'url': r.get('original'),
            'thumbnail': r.get('thumbnail'),
            'title': r.get('title', ''),
        }
        for r in data.get('images_results', [])[:limit]
        if r.get('original')
    ]


def fetch_and_save_image(bike, query=None):
    """Search, download the first usable image and save it to bike.image."""
    results = search_images(query or build_query(bike), limit=6)
    headers = {'User-Agent': 'Mozilla/5.0 (BikeAI image fetcher)'}

    for item in results:
        try:
            r = requests.get(item['url'], headers=headers, timeout=TIMEOUT)
            r.raise_for_status()
            ctype = r.headers.get('Content-Type', '').split(';')[0]
            if not ctype.startswith('image/'):
                continue
            ext = mimetypes.guess_extension(ctype) or '.jpg'
            if ext == '.jpe':
                ext = '.jpg'
            name = f'{bike.brand.name}_{bike.model_name}'.replace(' ', '_') + ext
            bike.image.save(name, ContentFile(r.content), save=True)
            return item['url']
        except requests.RequestException as exc:
            logger.warning('Skipping %s: %s', urlparse(item['url']).netloc, exc)
    return None