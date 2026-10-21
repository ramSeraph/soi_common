import os
import io
import logging
import time

from PIL import Image
from imgcat import imgcat

from .captcha.auto import guess, get_solver, save_captcha
from .common import session, base_url

logger = logging.getLogger(__name__)

CAPTCHA_MANUAL = (os.environ.get('CAPTCHA_MANUAL', '0') == '1')
captcha_model_dir = 'data/captcha/models'
# SOI rejects otherwise correct CAPTCHA answers submitted immediately.
CAPTCHA_MIN_AGE_SECONDS = 5

def guess_manual(filename):
    save_captcha(filename)
    image = Image.open(filename)
    imgcat(image)
    captcha_code = input("Enter the captcha: ")
    return captcha_code.strip()


def captcha_guess(filename, captcha_model_dir):
    if CAPTCHA_MANUAL:
        return guess_manual(filename)
    return guess(filename, captcha_model_dir)


def get_captcha(captcha_url):
    fetched_at = time.monotonic()
    web_data = session.get(captcha_url)
    if not web_data.ok:
        raise Exception(f'unable to retrieve captcha at {captcha_url}')

    captcha_content = web_data.content
    tempfile = io.BytesIO(captcha_content)
    captcha_code = captcha_guess(tempfile, captcha_model_dir)
    remaining = CAPTCHA_MIN_AGE_SECONDS - (time.monotonic() - fetched_at)
    if remaining > 0:
        time.sleep(remaining)
    logger.info(f'guessed captcha as {captcha_code}')
    return captcha_code


def get_captcha_from_page(soup):
    div = soup.find('div', { 'class': 'captcha' })
    img = div.find('img')
    captcha_url = img.attrs['src']
    captcha_url = base_url + captcha_url
    captcha = get_captcha(captcha_url)
    return captcha


def check_captcha_models(models_pathname):
    get_solver(models_pathname).download_model()
