import torch
from ultralytics import YOLO
import sys


def detect(source='yolo_dataset/yolo_dataset/images/test'):
    device = 0 if torch.cuda.is_available() else 'cpu'
    print(f'使用设备: {"GPU" if device == 0 else "CPU"}')

    model = YOLO('runs/train/exp1_yolov5s/weights/best.pt')

    results = model.predict(
        source=source,
        imgsz=640,
        conf=0.25,
        iou=0.45,
        device=device,
        save=True,
        save_txt=True,
        save_conf=True,
        project='runs/detect',
        name='exp',
    )

    print(f'\n=== 预测完成 ===')
    print(f'结果保存在: runs/detect/exp/')
    return results


if __name__ == '__main__':
    source = sys.argv[1] if len(sys.argv) > 1 else 'yolo_dataset/yolo_dataset/images/test'
    detect(source)
