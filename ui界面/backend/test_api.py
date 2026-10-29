import requests
from PIL import Image
import io

img = Image.open(r'../yolo_dataset/images/val/web_glass_013.jpg').convert('RGB')
buf = io.BytesIO()
img.save(buf, format='JPEG')
img_bytes = buf.getvalue()

files = {'image': ('test.jpg', img_bytes, 'image/jpeg')}
data = {'model': 'yolov5s', 'conf': '0.5', 'iou': '0.45'}

resp = requests.post('http://localhost:5000/api/detect', files=files, data=data)
result = resp.json()

print('Success:', result.get('success'))
print('Total detections:', result.get('total'))
print('Counts:', result.get('counts'))
print('Detections:')
for d in result.get('detections', []):
    cls = d['class']
    conf = d['confidence']
    bbox = d['bbox']
    print(f'  - {cls} ({conf:.4f}), bbox={bbox}')
print('Has annotated_image:', bool(result.get('annotated_image')))
if result.get('annotated_image'):
    print('Annotated image length:', len(result['annotated_image']))

# 测试模型列表
resp2 = requests.get('http://localhost:5000/api/models')
models = resp2.json()
print('\nModels:', models.get('models'))
print('Loaded:', models.get('loaded'))
