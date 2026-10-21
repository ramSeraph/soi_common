import io
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image

from soi_common import captcha_helper


class CaptchaHelperTests(unittest.TestCase):
    def setUp(self):
        self.image = io.BytesIO()
        Image.new('RGB', (180, 50), 'white').save(self.image, format='PNG')
        self.image.seek(0)
        self.solver = SimpleNamespace(
            solve=Mock(return_value=' lgXeyz\n'),
            set_cache_dir=Mock(),
            download_model=Mock(),
        )

    def test_captchabreaker_normalizes_case_and_preserves_image_dimensions(self):
        with patch.object(captcha_helper, 'CAPTCHA_MANUAL', False), \
             patch.dict('sys.modules', captchabreaker=self.solver):
            self.assertEqual(captcha_helper.captcha_guess(self.image, 'models'), 'LGXEYZ')
        self.solver.set_cache_dir.assert_called_once_with(str(Path('models/captchabreaker')))
        self.assertEqual(self.solver.solve.call_args.args[0].size, (180, 50))

    def test_captchabreaker_keeps_only_soi_captcha_characters(self):
        self.solver.solve.return_value = ' cT6nQl! \n'
        with patch.object(captcha_helper, 'CAPTCHA_MANUAL', False), \
             patch.dict('sys.modules', captchabreaker=self.solver):
            self.assertEqual(captcha_helper.captcha_guess(self.image, 'models'), 'CT6NQL')

    def test_check_models_downloads_the_captchabreaker_model(self):
        with patch.dict('sys.modules', captchabreaker=self.solver):
            captcha_helper.check_captcha_models('models')
        self.solver.download_model.assert_called_once_with()

    def test_manual_mode_takes_precedence(self):
        with patch.object(captcha_helper, 'CAPTCHA_MANUAL', True), \
             patch.object(captcha_helper, 'guess_manual', return_value='MANUAL') as manual:
            self.assertEqual(captcha_helper.captcha_guess(self.image, 'models'), 'MANUAL')
        manual.assert_called_once_with(self.image)

    def test_fast_recognition_waits_for_minimum_captcha_age(self):
        response = SimpleNamespace(ok=True, content=self.image.getvalue())
        with patch.object(captcha_helper.session, 'get', return_value=response), \
             patch.object(captcha_helper, 'captcha_guess', return_value='ABC123'), \
             patch.object(captcha_helper.time, 'monotonic', side_effect=[10, 11.5]), \
             patch.object(captcha_helper.time, 'sleep') as sleep:
            self.assertEqual(captcha_helper.get_captcha('https://example.test/captcha'), 'ABC123')
        sleep.assert_called_once_with(3.5)

    def test_slow_recognition_does_not_add_another_delay(self):
        response = SimpleNamespace(ok=True, content=self.image.getvalue())
        with patch.object(captcha_helper.session, 'get', return_value=response), \
             patch.object(captcha_helper, 'captcha_guess', return_value='ABC123'), \
             patch.object(captcha_helper.time, 'monotonic', side_effect=[10, 16]), \
             patch.object(captcha_helper.time, 'sleep') as sleep:
            self.assertEqual(captcha_helper.get_captcha('https://example.test/captcha'), 'ABC123')
        sleep.assert_not_called()


if __name__ == '__main__':
    unittest.main()
