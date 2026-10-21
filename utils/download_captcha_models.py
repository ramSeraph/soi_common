import argparse

from soi_common.captcha_helper import check_captcha_models


def main():
    parser = argparse.ArgumentParser(description='Download the captchabreaker model')
    parser.add_argument('models_dir', help='Directory for CAPTCHA models')
    args = parser.parse_args()
    check_captcha_models(args.models_dir)


if __name__ == '__main__':
    main()
