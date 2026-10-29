from ultralytics import YOLO
from PIL import Image
import torch
import base64
import io

model_path = r'../runs/detect/runs/train/exp1_yolov5s_bs16-2/weights/best.pt'
model = YOLO(model_path)

print(f'Model names: {model.names}')

# 测试 glass 图片
img_path = r'../yolo_dataset/images/val/web_glass_013.jpg'
img = Image.open(img_path).convert('RGB')
print(f'Image size: {img.size}')

results = model.predict(img, conf=0.5, iou=0.45, verbose=False, device=0 if torch.cuda.is_available() else 'cpu')

print('\n=== Detections ===')
for result in results:
    boxes = result.boxes
    if boxes is not None:
        print(f'Count: {len(boxes)}')
        for i, box in enumerate(boxes):
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            print(f'  [{i}] class={cls_name} (id={cls_id}), conf={conf:.4f}, bbox=[{x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}]')

# 测试 cardboard 图片
img_path2 = r'../yolo_dataset/images/val/web_paper_017.jpg'
print(f'\n=== Test paper image ===')
img2 = Image.open(img_path2).convert('RGB')
print(f'Image size: {img2.size}')

results2 = model.predict(img2, conf=0.5, iou=0.45, verbose=False, device=0 if torch.cuda.is_available() else 'cpu')

for result in results2:
    boxes = result.boxes
    if boxes is not None:
        print(f'Count: {len(boxes)}')
        for i, box in enumerate(boxes):
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            print(f'  [{i}] class={cls_name} (id={cls_id}), conf={conf:.4f}, bbox=[{x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}]')
