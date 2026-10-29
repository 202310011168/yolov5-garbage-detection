"""
YOLOv5s 训练脚本（独立运行）
模型：yolov5s (small 小模型)
结果保存：runs/train/exp1_yolov5s_bs16/
"""

import os
import torch
from ultralytics import YOLO

os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'


def main():
    if torch.cuda.is_available():
        device = 0
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f'设备: GPU ({gpu_name}, {gpu_mem:.1f}GB)')
    else:
        device = 'cpu'
        print('设备: CPU')

    exp_name = 'exp1_yolov5s_bs16'

    print(f'\n{"="*50}')
    print(f'实验一: YOLOv5s')
    print(f'  模型: yolov5s')
    print(f'  epochs: 100')
    print(f'  batch_size: 16')
    print(f'  imgsz: 640')
    print(f'  结果保存: runs/train/{exp_name}/')
    print(f'{"="*50}\n')

    best_pt = os.path.join('runs', 'train', exp_name, 'weights', 'best.pt')

    if os.path.exists(best_pt):
        print(f'实验已完成，直接验证...')
        model = YOLO(best_pt)
        results = model.val(
            data='yolo_dataset/yolo_dataset/data.yaml',
            device=device,
            imgsz=640,
            batch=16,
        )
    else:
        model = YOLO('yolov5s.pt')
        results = model.train(
            data='yolo_dataset/yolo_dataset/data.yaml',
            epochs=100,
            imgsz=640,
            batch=16,
            device=device,
            project='runs/train',
            name=exp_name,
            patience=20,
            save=True,
            plots=True,
            val=True,
            workers=2,
            optimizer='SGD',
            lr0=0.01,
            lrf=0.01,
            momentum=0.937,
            weight_decay=0.0005,
            warmup_epochs=3.0,
            warmup_momentum=0.8,
            warmup_bias_lr=0.1,
            cos_lr=True,
            close_mosaic=10,
            amp=True,
            seed=42,
        )

    print(f'\n{"="*50}')
    print('实验完成!')
    print(f'{"="*50}')
    print(f'  mAP@0.5:      {results.box.map50:.4f}')
    print(f'  mAP@0.5:0.95: {results.box.map:.4f}')
    print(f'  Precision:    {results.box.mp:.4f}')
    print(f'  Recall:       {results.box.mr:.4f}')
    print(f'\n结果保存在: runs/train/{exp_name}/')


if __name__ == '__main__':
    main()
