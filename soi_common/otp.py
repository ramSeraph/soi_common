import os
import re
import queue
import time
import logging

import pushbullet
import requests

from .pb_listener import Listener

logger = logging.getLogger(__name__)
SMS_POLL_INTERVAL = 3


def get_otp_manual():
    val = input('Enter OTP: ')
    return val.strip()

pb_client = None

def extract_soi_otp(sender, body):
    if not re.search(r'NAKSHE|SURVEY\s+OF\s+INDIA|ONLINE\s*MAPS\s+PORTAL',
                     sender + ' ' + body, re.IGNORECASE):
        return None
    otps = re.findall(r'\b(\d{6})\s+is\s+your\s+OTP\b', body, re.IGNORECASE)
    return otps[-1] if otps else None


def get_otp_from_msg(data):
    if data.get('type') != 'push':
        return None
    push = data.get('push', {})
    if push.get('type') != 'mirror':
        return None
    return extract_soi_otp(push.get('title', ''), push.get('body', ''))


def get_otp_from_sms(pb, not_before, deadline):
    """Read fresh SOI codes from SMS sync when notification mirroring is absent."""
    newest = None
    for device in pb.devices:
        if not device.active or not device.has_sms:
            continue
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        url = f'https://api.pushbullet.com/v2/permanents/{device.device_iden}_threads'
        try:
            response = pb._session.get(url, timeout=min(10, remaining))
            response.raise_for_status()
            threads = response.json().get('threads', [])
        except (requests.RequestException, ValueError) as exc:
            # A device without SMS access must not disable notification mirroring.
            logger.warning('Unable to read Pushbullet SMS (%s)', type(exc).__name__)
            continue
        for thread in threads:
            latest = thread.get('latest', {})
            timestamp = latest.get('timestamp', 0)
            if timestamp < not_before:
                continue
            sender = ' '.join(r.get('number', '') for r in thread.get('recipients', []))
            code = extract_soi_otp(sender, latest.get('body', ''))
            if code is not None and (newest is None or timestamp > newest[0]):
                newest = (timestamp, code)
    return newest[1] if newest else None

def get_pb_client():
    global pb_client
    if pb_client is None:
        pb_token = os.environ.get('PB_TOKEN', '')
        if pb_token == '':
            raise Exception('PB_TOKEN environment variable not set or empty')
        pb_client = pushbullet.PushBullet(pb_token)
    return pb_client


def setup_otp_listener():
    pb = get_pb_client()
    listener = Listener(pb)
    # Record this before the password submission can trigger an SMS.
    listener.otp_not_before = time.time()
    listener.start()
    return listener

def get_otp_pb(listener, timeout=60):
    deadline = time.monotonic() + timeout
    next_sms_check = time.monotonic()
    try:
        pb = get_pb_client()
        while True:
            now = time.monotonic()
            if now >= deadline:
                return None
            try:
                data = listener.q.get(timeout=min(deadline - now,
                                                  max(0, next_sms_check - now)))
                otp = get_otp_from_msg(data)
                if otp is not None:
                    logger.info('Received SOI OTP through notification mirroring')
                    return otp
            except queue.Empty:
                pass
            if time.monotonic() >= next_sms_check:
                otp = get_otp_from_sms(pb, listener.otp_not_before, deadline)
                if otp is not None:
                    logger.info('Received fresh SOI OTP through Pushbullet SMS sync')
                    return otp
                next_sms_check = time.monotonic() + SMS_POLL_INTERVAL
    finally:
        listener.close()


if __name__ == '__main__':
    listener = setup_otp_listener()
    print('done setting up listener')
    otp =  get_otp_pb(listener, timeout=600)
    print(f'got {otp=}')


