from flask import Flask, send_file
from flask_restful import reqparse, Api, Resource
from PIL import Image
from math import sqrt
import urllib.request
import io
import random
import re

app = Flask(__name__)
api = Api(app)


def one_to_eight_urls():
    def validate(s):
        links = list(filter(None, s.split(',')))
        if 1 <= len(links) <= 8:
            return s
        raise ValueError(f"Minimum {1} url, maximum {8} urls.")
    return validate


def resolution():
    def validate(s):
        if re.search("^[0-9]+[x][0-9]+$", s):
            if int(s.split('x')[0]) > 0 and int(s.split('x')[1]) > 0:
                return s
            raise ValueError(f"Width and height have to be greater than 0")
        raise ValueError(f"Resolution have to be in format AxB.")
    return validate


parser = reqparse.RequestParser()
parser.add_argument('zdjecia', type=one_to_eight_urls(), required=True, location='args')
parser.add_argument('rozdzielczosc', type=resolution(), default='2048x2048', location='args')
parser.add_argument('losowo', default='random', location='args')


class Mozaika(Resource):
    def get(self):
        args = parser.parse_args()
        photos = args.get('zdjecia').split(',')
        randomly = True if args.get('losowo') == "1" else False
        resolution = args.get('rozdzielczosc')

        if randomly:
            random.shuffle(photos)

        mosaic = self.concat_images(resolution, photos)

        return self.send_jpg_image(mosaic)

    def concat_images(self, resolution, photos):
        width, height = int(resolution.split('x')[0]), int(resolution.split('x')[1])

        mosaic = Image.new("RGB", (width, height))
        sizes = [1, 4, 9]

        counter = 0
        for url in photos:
            images_in_row = int(next(sqrt(i) for i in sizes if len(photos) <= i))
            image_width = width // images_in_row
            empty_rows = (images_in_row ** 2 - len(photos)) // images_in_row
            image_height = height // (images_in_row - empty_rows)

            with urllib.request.urlopen(url) as opened_url:
                f = io.BytesIO(opened_url.read())
            img = Image.open(f)
            img = img.resize((image_width, image_height), Image.ANTIALIAS)
            mosaic.paste(img, ((counter % images_in_row) * image_width, (counter // images_in_row) * image_height))
            counter += 1

        return mosaic

    def send_jpg_image(self, pil_img):
        img_io = io.BytesIO()
        pil_img.save(img_io, 'JPEG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')


api.add_resource(Mozaika, '/mozaika')


if __name__ == '__main__':
    app.run(debug=False)
