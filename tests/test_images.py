import io

import pytest
from PIL import Image

from connections.images import prepare_image


def make_image(size=(1800, 900)):
    stream = io.BytesIO()
    Image.new("RGBA", size, (255, 255, 255, 0)).save(stream, "PNG")
    return stream.getvalue()


def test_image_resized_and_reencoded_without_metadata():
    prepared = prepare_image(make_image())
    assert (prepared.width, prepared.height) == (1600, 800)
    assert prepared.data_url.startswith("data:image/png;base64,")
    with Image.open(io.BytesIO(prepared.data)) as image:
        assert image.mode == "RGB"
        assert image.getpixel((0, 0)) == (255, 255, 255)
        assert not image.getexif()


@pytest.mark.parametrize("data", [b"not an image", b"", b"x" * (12 * 1024 * 1024 + 1)])
def test_invalid_or_oversized_input_rejected(data):
    with pytest.raises(ValueError):
        prepare_image(data)


def test_tiny_images_rejected():
    with pytest.raises(ValueError, match="small"):
        prepare_image(make_image((10, 10)))
