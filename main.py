import argparse

import cv2
import moviepy.editor as mp
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

    output_name = "sample_video.mp4"
    start_frame = 0  # 90
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    all_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(save_path + output_name)
    video_writer = cv2.VideoWriter(save_path + output_name, fourcc, fps, (W, H))

    num_charactors = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    max_frame = all_frames - start_frame
    # max_frame = 150
    erode = True
    pre_damage = 108  # 76# 0
    pre_kill_info = "0"
    digit = 3  # 2# 1
    pbar = tqdm.tqdm(total=max_frame)
    shoot_manager = ShootManager()

    frame = 0
    while cap.isOpened():
        ret, img = cap.read()
        if not ret:
            print("finish")
            break
        img = cv2.resize(img, (1920, 1080))
        src_img = img.copy()

        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        cropped_img = image_utils.get_weapon_info(img, H, W)
        cropped_img["weapon_bullet1"] = image_utils.otsu(cropped_img["weapon_bullet1"])
        cropped_img["weapon_bullet1"] = np.where(
            cropped_img["weapon_bullet1"] < 150, 255, 0
        ).astype(np.uint8)

        weapon_name1 = image_utils.get_text(cropped_img["weapon_name1"])
        weapon_name1 = weapon_name1[-6:]
        if weapon_name1 == "ウィングマン" or weapon_name1 == "ヴィングマン":
            if erode:
                kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
                cropped_img["weapon_bullet1"] = cv2.dilate(
                    cropped_img["weapon_bullet1"], kernel, borderValue=255
                )
            weapon_bullet1 = image_utils.get_text(
                # cropped_img["weapon_bullet1"], lang="eng", layout=6
                cropped_img["weapon_bullet1"],
                lang="eng",
                layout=7,
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
                dm_text = pre_damage
                # if pre_damage - 1 == dm_text:
                #     dm_text = pre_damage
                # else:
                #     print(dm_text_src)
                #     print("pre", pre_damage)
                #     print("damage", dm_text)
                #     print("damage decrease")
                #     break

            if pre_damage + 100 < dm_text:
                dm_text = pre_damage

            pre_damage = dm_text
            kill_img = image_utils.get_kill_info(img)
            kill_img = cv2.bitwise_not(image_utils.otsu(kill_img))
            kill_info = image_utils.get_text(kill_img, lang="eng", layout=7)
            if len(kill_info) > 0:
                kill_info = image_utils.str_to_number(kill_info)
            else:
                kill_info = "0"

            if pre_kill_info == kill_info:
                dm_text = shoot_manager.fix_damage(dm_text)
            pre_kill_info = kill_info

            shoot_manager.add_info(weapon_bullet1, dm_text)

            print(f"\r[{frame}]bullet:[{weapon_bullet1}][{dm_text}]", end="")

        frame += 1
        bullet, hits, percent = shoot_manager.get_hit_percentage()
        edit_img = image_utils.image_editer(src_img, percent, bullet, hits)
        edit_img = cv2.resize(edit_img, (W, H))

        video_writer.write(edit_img)
        pbar.update(1)
        if frame == max_frame:
            break
    print("")
    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()

    postprocess(
        save_path,
        output_name,
        args.file_path,
        (start_frame / fps, (start_frame + max_frame) / fps),
    )


def postprocess(save_path, output_name, src_path, video_range):
    import ffmpeg

    path = save_path + output_name

    (
        ffmpeg.input(path)
        .output(path[:-4] + "_encoded.mp4", vcodec="libx264", crf=23, preset="slow")
        .run()
    )
    extract_and_setaudio(
        src_video=src_path,
        output_video=path[:-4] + "_encoded.mp4",
        out_file=path[:-4] + "_encoded_audio.mp4",
        out_audio=path[:-4] + "_audio.mp3",
        video_range=video_range,
    )


def extract_and_setaudio(
    src_video, output_video, out_file, out_audio="tmp.mp3", video_range=(0, 0)
):
    clip_in = mp.VideoFileClip(src_video)
    clip_in = clip_in.subclip(video_range[0], video_range[1])
    # clip_in = clip_in.subclip(int(video_range[0]), int(video_range[1]))
    # clip_in = clip_in.subclip(video_range[0], video_range[1])

    clip_in.audio.write_audiofile(out_audio)

    clip_out = mp.VideoFileClip(output_video).subclip()
    clip_out.write_videofile(out_file, audio=out_audio)
    print(out_file)


if __name__ == "__main__":
    main()
