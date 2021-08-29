import argparse

import cv2
import numpy as np
import tqdm

import image_utils
from shoot_manager import ShootManager


def get_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", type=str, help="path to video")
    args = parser.parse_args()
    return args


def main():
    args = get_arg()
    cap = cv2.VideoCapture(args.file_path)
    save_path = "output/"
    frame = 0
    start_frame = 10000  # 9000
    start_frame += 5400
    start_frame = 0
    max_frame = 30
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    erode = True
    num_charactors = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    shoot_manager = ShootManager()

    output_name = "sample_video.mp4"
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(save_path + output_name)
    video_writer = cv2.VideoWriter(save_path + output_name, fourcc, fps, (W, H))

    pre_damage = 108  # 76# 0
    digit = 3  # 2# 1
    pbar = tqdm.tqdm(total=max_frame)

    while cap.isOpened():
        ret, img = cap.read()
        if not ret:
            break
        src_img = img.copy()

        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cropped_img = image_utils.get_weapon_info(img, H, W)
        cropped_img["weapon_bullet1"] = image_utils.otsu(cropped_img["weapon_bullet1"])
        cropped_img["weapon_bullet1"] = np.where(
            cropped_img["weapon_bullet1"] < 150, 255, 0
        ).astype(np.uint8)

        weapon_name1 = image_utils.get_text(cropped_img["weapon_name1"])
        if weapon_name1 == "ウィングマン":
            if erode:
                kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
                cropped_img["weapon_bullet1"] = cv2.dilate(
                    cropped_img["weapon_bullet1"], kernel, borderValue=255
                )
            weapon_bullet1 = image_utils.get_text(
                cropped_img["weapon_bullet1"], lang="eng", layout=7
            )
            weapon_bullet1 = weapon_bullet1[0]

            weapon_bullet1 = image_utils.str_to_number(weapon_bullet1)
            if weapon_bullet1 not in num_charactors:
                print("")
                print(len(weapon_bullet1))
                print(f"bullet[{weapon_bullet1}]")
                break

            damages = image_utils.get_damage_info(img)

            damages = image_utils.otsu(damages)
            damages = np.where(damages < 150, 255, 0).astype(np.uint8)

            dm_text_src = image_utils.get_text(damages, lang="eng", layout=7)
            dm_text = list(dm_text_src)
            for i in range(len(dm_text)):
                dm_text[i] = image_utils.str_to_number(dm_text[i])
            dm_text = "".join(dm_text)

            if len(dm_text) == 0:
                dm_text = str(pre_damage)

            if dm_text[-1] != str(pre_damage)[-1]:
                if 60 < pre_damage and digit == 2:
                    digit += 1
                if 960 < pre_damage and digit == 3:
                    digit += 1

            dm_text = dm_text[-digit:]
            dm_text = image_utils.str_to_number2(dm_text)

            if len(dm_text) == 0:
                dm_text = 0
                print("damage wrong")
                break
            else:
                try:
                    dm_text = int(dm_text)
                except ValueError:
                    dm_text = pre_damage

            if pre_damage > dm_text:
                if pre_damage - 1 == dm_text:
                    dm_text = pre_damage
                else:
                    print(dm_text_src)
                    print("pre", pre_damage)
                    print("damage", dm_text)
                    print("damage decrease")
                    break

            if pre_damage + 100 < dm_text:
                dm_text = pre_damage
            dm_text = shoot_manager.fix_damage(dm_text)

            pre_damage = dm_text

            shoot_manager.add_info(weapon_bullet1, dm_text)

            print(f"\r[{frame}]bullet:[{weapon_bullet1}][{dm_text}]", end="")

        frame += 1
        bullet, hits, percent = shoot_manager.get_hit_percentage()
        edit_img = image_utils.image_editer(src_img, percent, bullet, hits)
        # edit_img = cv2.cvtColor(edit_img, cv2.COLOR_RGB2BGR)

        video_writer.write(edit_img)
        pbar.update(1)
        if frame == max_frame:
            break
    print("")
    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()

    postprocess(save_path + output_name)


def postprocess(path):
    import ffmpeg

    (
        ffmpeg.input(path)
        .output(path[:-4] + "_encoded.mp4", vcodec="libx264", crf=23, preset="slow")
        .run()
    )


if __name__ == "__main__":
    main()
