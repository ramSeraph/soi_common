import queue
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests

from soi_common import otp


def sms(code, timestamp, sender='VM-NAKSHE', body=None):
    return {
        'recipients': [{'number': sender}],
        'latest': {
            'timestamp': timestamp,
            'body': body if body is not None else f'{code} is your OTP for login.',
        },
    }


def response(threads):
    return SimpleNamespace(raise_for_status=Mock(), json=lambda: {'threads': threads})


class OtpTests(unittest.TestCase):
    def setUp(self):
        self.pb = SimpleNamespace(
            devices=[SimpleNamespace(active=True, has_sms=True, device_iden='test-device')],
            _session=Mock(),
        )
        self.listener = SimpleNamespace(q=queue.Queue(), close=Mock(), otp_not_before=100)

    def test_sms_ignores_old_and_unrelated_codes_and_chooses_newest(self):
        self.pb._session.get.return_value = response([
            sms('111111', 99),
            sms('222222', 101),
            sms('333333', 103, sender='OTHER-SERVICE'),
            sms('444444', 102, sender='UNKNOWN',
                body='444444 is your OTP for login to Online Maps Portal. SURVEY OF INDIA'),
        ])
        with patch.object(otp.time, 'monotonic', return_value=10):
            self.assertEqual(otp.get_otp_from_sms(self.pb, 100, 30), '444444')
        self.pb._session.get.assert_called_once_with(
            'https://api.pushbullet.com/v2/permanents/test-device_threads', timeout=10)

    def test_sms_failure_on_one_device_still_checks_the_other(self):
        self.pb.devices.append(SimpleNamespace(active=True, has_sms=True, device_iden='other'))
        self.pb._session.get.side_effect = [requests.HTTPError(), response([sms('123456', 101)])]
        with patch.object(otp.time, 'monotonic', return_value=10), \
             self.assertLogs(otp.logger, level='WARNING'):
            self.assertEqual(otp.get_otp_from_sms(self.pb, 100, 30), '123456')

    def test_sms_skips_inactive_devices_and_stops_at_deadline(self):
        self.pb.devices.insert(0, SimpleNamespace(active=False, has_sms=True, device_iden='old'))
        with patch.object(otp.time, 'monotonic', return_value=30):
            self.assertIsNone(otp.get_otp_from_sms(self.pb, 100, 30))
        self.pb._session.get.assert_not_called()

    def test_mirrored_notification_still_works_and_closes_listener(self):
        self.listener.q.put({'type': 'push', 'push': {
            'type': 'mirror', 'title': 'NAKSHE', 'body': '123456 is your OTP',
        }})
        with patch.object(otp, 'get_pb_client', return_value=self.pb):
            self.assertEqual(otp.get_otp_pb(self.listener), '123456')
        self.listener.close.assert_called_once_with()
        self.pb._session.get.assert_not_called()

    def test_sms_is_used_when_notifications_do_not_arrive(self):
        self.pb._session.get.return_value = response([sms('654321', 101)])
        with patch.object(otp, 'get_pb_client', return_value=self.pb):
            self.assertEqual(otp.get_otp_pb(self.listener), '654321')
        self.listener.close.assert_called_once_with()

    def test_unrelated_notifications_do_not_extend_timeout(self):
        # Keep supplying messages: the deadline must still end the wait.
        self.listener.q = Mock()
        self.listener.q.get.return_value = {'type': 'tickle'}
        ticks = iter(range(100))
        with patch.object(otp.time, 'monotonic', side_effect=lambda: next(ticks)), \
             patch.object(otp, 'get_pb_client', return_value=self.pb), \
             patch.object(otp, 'get_otp_from_sms', return_value=None):
            self.assertIsNone(otp.get_otp_pb(self.listener, timeout=10))
        self.listener.close.assert_called_once_with()
        self.assertLessEqual(self.listener.q.get.call_count, 4)

    def test_listener_closes_on_error(self):
        with patch.object(otp, 'get_pb_client', side_effect=RuntimeError('client error')):
            with self.assertRaises(RuntimeError):
                otp.get_otp_pb(self.listener)
        self.listener.close.assert_called_once_with()

    def test_setup_records_freshness_before_starting_listener(self):
        listener = SimpleNamespace(start=Mock())
        listener.start.side_effect = lambda: self.assertEqual(listener.otp_not_before, 123)
        with patch.object(otp, 'get_pb_client', return_value=self.pb), \
             patch.object(otp, 'Listener', return_value=listener), \
             patch.object(otp.time, 'time', return_value=123):
            self.assertIs(otp.setup_otp_listener(), listener)
        listener.start.assert_called_once_with()

    def test_non_mirrored_and_unrelated_notifications_are_ignored(self):
        for message in [{}, {'type': 'nop'}, {'type': 'push'},
                        {'type': 'push', 'push': {'type': 'mirror',
                         'title': 'Other app', 'body': '123456 is your OTP'}}]:
            self.assertIsNone(otp.get_otp_from_msg(message))


if __name__ == '__main__':
    unittest.main()
