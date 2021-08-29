import cv2
import numpy as np
import pyocr
from PIL import Image

base_w = 1920
base_h = 1080


def cv2pil(image):
    """ OpenCV型 -> PIL型 """
    new_image = image.copy()
    if new_image.ndim == 2:  # モノクロ
        pass
    elif new_image.shape[2] == 3:  # カラー
        new_image = cv2.cvtColor(new_image, cv2.COLOR_BGR2RGB)
    elif new_image.shape[2] == 4:  # 透過
        new_image = cv2.cvtColor(new_image, cv2.COLOR_BGRA2RGBA)
    new_image = Image.fromarray(new_image)
    return new_image


def make_sharp_kernel(k: int):
    return np.array(
        [
            [-k / 9, -k / 9, -k / 9],
            [-k / 9, 1 + 8 * k / 9, k / 9],
            [-k / 9, -k / 9, -k / 9],
        ],
        np.float32,
    )


def make_sharp(img):
    kernel = make_sharp_kernel(k=1)
    img = cv2.filter2D(img, -1, kernel).astype("uint8")
    return img


def otsu(img):
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img


def get_weapon_info(img, H, W):
    weapon = img[H * int(950 / base_h) :, W * int(1500 / base_w) :]
    weapon_name1 = weapon[80:110, 50:175]
    weapon_bullet1 = weapon[5:50, 255:290]

    return {"weapon_name1": weapon_name1, "weapon_bullet1": weapon_bullet1}


def get_text(img, to_pil=True, lang="jpn+eng", layout=6):
    img = cv2pil(img)
    tools = pyocr.get_available_tools()
    tool = tools[0]
    text = tool.image_to_string(
        img, lang=lang, builder=pyocr.builders.TextBuilder(tesseract_layout=layout)
    )
    return text


def get_damage_info(img):
    info = img[100:120, 1785:1840]
    # x0 = info[:, -11:]
    # x1 = info[:, -22:-11]
    # x2 = info[:, -33:-22]
    # x3 = info[:, -44:-33]
    # return [x0, x1, x2, x3]
    return info


def image_editer(img, percent, hits, total, factor=0.8):
    font_sizes = [4, 3, 2, 5]
    font_sizes = [3, 2, 1, 3]
    h, w, _ = img.shape
    resize_h = int(h * factor)
    resize_w = int(w * factor)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, dsize=(resize_w, resize_h))
    img = cv2.copyMakeBorder(
        img, 0, h - resize_h, 0, w - resize_w, cv2.BORDER_CONSTANT, value=(187, 192, 0)
    )

    img = cv2.putText(
        img,
        str(int(percent * 100)) + "%",
        (resize_w + int(w * 50 / base_w), int(h * 200 / base_w)),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_sizes[0],
        (0, 0, 0),
        thickness=5,
    )
    img = cv2.putText(
        img,
        f"{str(len(hits))}/{str(len(total))}",
        (resize_w + int(w * 50 / base_w), int(h * 350 / base_h)),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_sizes[1],
        (0, 0, 0),
        thickness=5,
    )
    print_num = 5
    for i, t in enumerate(total[-print_num:]):
        if t in hits:
            x = ":HIT"
        else:
            x = ":MISS"

        img = cv2.putText(
            img,
            f"{t}{x}",
            (
                resize_w + int(w * 50 / base_w),
                int(h * 450 / base_h) + i * int(h * 100 / base_h),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_sizes[2],
            (0, 0, 0),
            thickness=2,
        )

    img = cv2.putText(
        img,
        "wingman hit counter",
        (int(w * 100 / base_w), resize_h + int(h * 150 / base_h)),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_sizes[3],
        (0, 0, 0),
        thickness=5,
    )
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img
