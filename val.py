import torch
from ultralytics import YOLO


def validate():
    device = 0 if torch.cuda.is_available() else 'cpu'
    print(f'使用设备: {"GPU" if device == 0 else "CPU"}')

    model = YOLO('runs/train/exp1_yolov5s/weights/best.pt')

    results = model.val(
        data='yolo_dataset/yolo_dataset/data.yaml',
        imgsz=640,
        batch=16,
        device=device,
        split='val',
        plots=True,
        save_json=True,
    )

    print('\n=== 验证结果 ===')
    print(f'mAP@0.5: {results.box.map50:.4f}')
    print(f'mAP@0.5:0.95: {results.box.map:.4f}')
    print(f'Precision: {results.box.mp:.4f}')
    print(f'Recall: {results.box.mr:.4f}')
    return results


if __name__ == '__main__':
    validate()
