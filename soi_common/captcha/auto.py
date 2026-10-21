from pathlib import Path

from PIL import Image

img_data_dir = 'data/captcha/imgs/'


def get_solver(models_pathname):
    import captchabreaker

    captchabreaker.set_cache_dir(str(Path(models_pathname) / 'captchabreaker'))
    return captchabreaker


def guess(filename, models_dir):
    solver = get_solver(models_dir)
    with Image.open(filename) as image:
        prediction = solver.solve(image).upper()
    return ''.join(c for c in prediction if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')


def save_captcha(tempfile):
    Path(img_data_dir).mkdir(parents=True, exist_ok=True)
    counter_fname = Path(img_data_dir).joinpath('counter')
    if not Path(counter_fname).exists():
        with open(counter_fname, 'w') as f:
            f.write('1')
    with open(counter_fname, 'r') as f:
        counter = int(f.read().strip())

    contents = tempfile.getvalue()
    new_filename = Path(img_data_dir).joinpath(f'{counter}.jpeg')
    with open(new_filename, 'wb') as f:
        f.write(contents)

    with open(counter_fname, 'w') as f:
        f.write(str(counter + 1))
