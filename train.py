import os
import torch
from ultralytics import YOLO

os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'


def train():
    if torch.cuda.is_available():
        device = 0
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f'使用设备: GPU ({gpu_name}, {gpu_mem:.1f}GB)')
    else:
        device = 'cpu'
        print('使用设备: CPU')

    model = YOLO('yolov5s.pt')

    results = model.train(
        data='yolo_dataset/yolo_dataset/data.yaml',
        epochs=100,
        imgsz=640,
        batch=16,
        device=device,
        project='runs/train',
        name='exp1_yolov5s',
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

    print('\n=== 训练完成 ===')
    print(f'最佳权重: {results.best}')
    print(f'最佳 mAP@0.5: {results.box.map50:.4f}')
    return results


if __name__ == '__main__':
    train()
