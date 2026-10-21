# SOI common scraping helpers

Automatic CAPTCHA recognition uses
[captchabreaker](https://github.com/ramSeraph/captchabreaker).
Predictions are normalized to uppercase letters and digits for the SOI forms.
`check_captcha_models()` downloads the ONNX model into the `captchabreaker/`
subdirectory of the supplied model directory; cache this directory in CI.
You can also prefetch it with `download-captcha-models <models_dir>`.

Set `CAPTCHA_MANUAL=1` for manual entry.

SOI sometimes rejects correct answers submitted too quickly. CAPTCHA fetching
and recognition take at least five seconds before returning an answer; slower
recognition or manual entry does not incur an additional delay.

Set `PB_TOKEN` to receive login OTPs through Pushbullet. The listener accepts
mirrored SOI notifications and polls SMS sync on active SMS-enabled devices.
SMS codes older than the start of the login attempt are ignored. Unrelated
notifications do not extend the OTP timeout.

Run the helper tests with `python -m unittest discover -s tests`.
