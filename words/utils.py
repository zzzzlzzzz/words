from random import randint, choice
from os import path, listdir
from io import BytesIO
from base64 import b64encode

from flask import current_app
from PIL import Image, ImageDraw, ImageFont


def generate_logotype(text, base_color=(255, 255, 255)):
    """Generate JPG logotype from text

    :param text: text for logotype
    :param base_color: (r, g, b) tuple of base color
    :return: base64 encoded logotype
    """
    red = (randint(0, 255) + base_color[0]) // 2
    green = (randint(0, 255) + base_color[1]) // 2
    blue = (randint(0, 255) + base_color[2]) // 2

    font_root_path = path.join(current_app.root_path, 'fonts')
    font = ImageFont.truetype(choice([path.join(font_root_path, _) for _ in listdir(font_root_path)]), 220)

    logotype_width, logotype_height = 512, 512
    logotype = Image.new('RGB', (logotype_width, logotype_height), (red, green, blue))
    draw = ImageDraw.Draw(logotype, 'RGB')
    text_width, text_height = draw.textsize(text, font)
    draw.text(((logotype_width - text_width) // 2, ((logotype_height - text_height) // 2) // 2), text, base_color, font)

    logotype_buffer = BytesIO()
    logotype.save(logotype_buffer, 'jpeg')
    return 'data:image/jpg;base64,{}'.format(b64encode(logotype_buffer.getvalue()).decode('utf8'))
