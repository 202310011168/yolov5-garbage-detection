import os
import json
import random
import shutil
from pathlib import Path


def labelme2yolo(labelme_dir, output_dir, class_names, train_ratio=0.7, val_ratio=0.2):
    """
    将 LabelMe 标注的 .json 文件转换为 YOLOv5 格式，并划分训练/验证/测试集

    Args:
        labelme_dir: LabelMe 标注文件所在目录（图片和 .json 在一起）
        output_dir: 输出目录（YOLO格式）
        class_names: 类别名称列表
        train_ratio: 训练集比例
        val_ratio: 验证集比例
    """
    output_dir = Path(output_dir)
    images_dir = output_dir / 'images'
    labels_dir = output_dir / 'labels'

    for split in ['train', 'val', 'test']:
        (images_dir / split).mkdir(parents=True, exist_ok=True)
        (labels_dir / split).mkdir(parents=True, exist_ok=True)

    json_files = list(Path(labelme_dir).glob('*.json'))
    random.shuffle(json_files)

    n = len(json_files)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    splits = ['train'] * n_train + ['val'] * n_val + ['test'] * (n - n_train - n_val)

    class_map = {name: idx for idx, name in enumerate(class_names)}

    for i, json_file in enumerate(json_files):
        split = splits[i]

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        img_width = data['imageWidth']
        img_height = data['imageHeight']
        img_name = data['imagePath']

        img_src = json_file.parent / img_name
        if not img_src.exists():
            print(f'  跳过: 找不到图片 {img_name}')
            continue

        img_dst = images_dir / split / img_name
        shutil.copy(img_src, img_dst)

        label_name = Path(img_name).stem + '.txt'
        label_dst = labels_dir / split / label_name

        with open(label_dst, 'w') as f:
            for shape in data['shapes']:
                label = shape['label']
                if label not in class_map:
                    print(f'  跳过未知类别: {label}')
                    continue

                points = shape['points']
                x_coords = [p[0] for p in points]
                y_coords = [p[1] for p in points]

                x_min = min(x_coords)
                x_max = max(x_coords)
                y_min = min(y_coords)
                y_max = max(y_coords)

                x_center = (x_min + x_max) / 2 / img_width
                y_center = (y_min + y_max) / 2 / img_height
                width = (x_max - x_min) / img_width
                height = (y_max - y_min) / img_height

                class_idx = class_map[label]
                f.write(f'{class_idx} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n')

        print(f'  [{i+1}/{n}] {img_name} -> {split}')

    print(f'\n转换完成！')
    print(f'  训练集: {n_train} 张')
    print(f'  验证集: {n_val} 张')
    print(f'  测试集: {n - n_train - n_val} 张')


if __name__ == '__main__':
    class_names = ['cardboard', 'glass', 'metal', 'paper', 'plastic']

    print('=== LabelMe -> YOLOv5 格式转换 ===')
    labelme_dir = input('请输入 LabelMe 标注文件所在目录路径: ').strip()

    if not os.path.exists(labelme_dir):
        print(f'目录不存在: {labelme_dir}')
        exit(1)

    output_dir = './dataset_yolo'
    labelme2yolo(labelme_dir, output_dir, class_names)
    print(f'\n输出目录: {os.path.abspath(output_dir)}')
