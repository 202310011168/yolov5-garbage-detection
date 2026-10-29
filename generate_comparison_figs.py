"""
生成三组实验的对比拼接图
将 YOLOv5n / YOLOv5s / YOLOv5m 的同名图片横向拼接，方便对比
输出到 comparison_figures/ 目录
"""

import os
import cv2
import numpy as np


def add_title(img, title, font_scale=1.2, thickness=2):
    h, w = img.shape[:2]
    title_h = 50
    canvas = np.zeros((h + title_h, w, 3), dtype=np.uint8)
    canvas[title_h:, :] = img
    cv2.putText(canvas, title, (w // 2 - len(title) * 14, 35),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
    return canvas


def concat_horizontal(images, titles):
    titled = []
    for img, title in zip(images, titles):
        titled.append(add_title(img, title))

    heights = [img.shape[0] for img in titled]
    max_h = max(heights)

    resized = []
    for img in titled:
        if img.shape[0] != max_h:
            scale = max_h / img.shape[0]
            new_w = int(img.shape[1] * scale)
            img = cv2.resize(img, (new_w, max_h))
        resized.append(img)

    return cv2.hconcat(resized)


def main():
    base_dir = r'c:\Users\HW\Desktop\dataset\runs\detect\runs\train'
    exp_dirs = {
        'YOLOv5n': os.path.join(base_dir, 'exp3_yolov5n_bs32'),
        'YOLOv5s': os.path.join(base_dir, 'exp1_yolov5s_bs16-3'),
        'YOLOv5m': os.path.join(base_dir, 'exp2_yolov5m_bs8'),
    }

    image_names = [
        'results.png',
        'confusion_matrix.png',
        'BoxPR_curve.png',
        'BoxF1_curve.png',
    ]

    output_dir = r'c:\Users\HW\Desktop\dataset\comparison_figures'
    os.makedirs(output_dir, exist_ok=True)

    for img_name in image_names:
        images = []
        titles = list(exp_dirs.keys())
        for name, exp_dir in exp_dirs.items():
            path = os.path.join(exp_dir, img_name)
            if os.path.exists(path):
                img = cv2.imread(path)
                if img is not None:
                    images.append(img)
                    print(f'  加载 {name}/{img_name}  ({img.shape[1]}x{img.shape[0]})')
                else:
                    print(f'  警告: 无法读取 {path}')
                    images.append(np.zeros((640, 640, 3), dtype=np.uint8))
            else:
                print(f'  警告: 文件不存在 {path}')
                images.append(np.zeros((640, 640, 3), dtype=np.uint8))

        if images:
            result = concat_horizontal(images, titles)
            out_path = os.path.join(output_dir, f'compare_{img_name}')
            cv2.imwrite(out_path, result)
            print(f'  已生成: {out_path}  ({result.shape[1]}x{result.shape[0]})')
        print()

    print('所有对比图生成完成！保存在 comparison_figures/ 目录下')


if __name__ == '__main__':
    main()
