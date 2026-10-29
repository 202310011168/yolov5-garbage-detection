"""
YOLO 垃圾分类检测服务
提供 RESTful API 接口供前端调用
"""

import os
import io
import base64
import tempfile
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image
import torch
from ultralytics import YOLO
import cv2
import numpy as np

app = Flask(__name__, static_folder='static')
CORS(app)

# 配置
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static', exist_ok=True)

# 模型配置
MODEL_CONFIGS = {
    'yolov5n': {
        'name': 'YOLOv5 Nano',
        'size': '5.3 MB',
        'path': r'../../runs/detect/runs/train/exp3_yolov5n_bs32/weights/best.pt',
        'type': 'garbage',
    },
    'yolov5s': {
        'name': 'YOLOv5 Small',
        'size': '17.7 MB',
        'path': r'../../runs/detect/runs/train/exp1_yolov5s_bs16-2/weights/best.pt',
        'type': 'garbage',
    },
    'yolov5m': {
        'name': 'YOLOv5 Medium',
        'size': '48.2 MB',
        'path': r'../../runs/detect/runs/train/exp2_yolov5m_bs8/weights/best.pt',
        'type': 'garbage',
    },
    'yolov5s-coco': {
        'name': 'YOLOv5 Small COCO',
        'size': '22.5 MB',
        'path': r'../../yolov5su.pt',
        'type': 'coco',
    },
}

# 垃圾分类类别
GARBAGE_CLASS_NAMES = ['cardboard', 'glass', 'metal', 'paper', 'plastic']

# COCO 80类名称
COCO_CLASS_NAMES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator',
    'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

COCO_CLASS_NAMES_CN = {
    'person': '人', 'bicycle': '自行车', 'car': '汽车', 'motorcycle': '摩托车',
    'airplane': '飞机', 'bus': '公交车', 'train': '火车', 'truck': '卡车', 'boat': '船',
    'traffic light': '红绿灯', 'fire hydrant': '消防栓', 'stop sign': '停车标志',
    'parking meter': '停车计时器', 'bench': '长椅', 'bird': '鸟', 'cat': '猫', 'dog': '狗',
    'horse': '马', 'sheep': '羊', 'cow': '牛', 'elephant': '大象', 'bear': '熊',
    'zebra': '斑马', 'giraffe': '长颈鹿', 'backpack': '背包', 'umbrella': '雨伞',
    'handbag': '手提包', 'tie': '领带', 'suitcase': '行李箱', 'frisbee': '飞盘',
    'skis': '滑雪板', 'snowboard': '单板滑雪', 'sports ball': '球', 'kite': '风筝',
    'baseball bat': '棒球棒', 'baseball glove': '棒球手套', 'skateboard': '滑板',
    'surfboard': '冲浪板', 'tennis racket': '网球拍', 'bottle': '瓶子',
    'wine glass': '酒杯', 'cup': '杯子', 'fork': '叉子', 'knife': '刀', 'spoon': '勺子',
    'bowl': '碗', 'banana': '香蕉', 'apple': '苹果', 'sandwich': '三明治',
    'orange': '橙子', 'broccoli': '西兰花', 'carrot': '胡萝卜', 'hot dog': '热狗',
    'pizza': '披萨', 'donut': '甜甜圈', 'cake': '蛋糕', 'chair': '椅子', 'couch': '沙发',
    'potted plant': '盆栽', 'bed': '床', 'dining table': '餐桌', 'toilet': '厕所',
    'tv': '电视', 'laptop': '笔记本电脑', 'mouse': '鼠标', 'remote': '遥控器',
    'keyboard': '键盘', 'cell phone': '手机', 'microwave': '微波炉', 'oven': '烤箱',
    'toaster': '烤面包机', 'sink': '水槽', 'refrigerator': '冰箱', 'book': '书',
    'clock': '时钟', 'vase': '花瓶', 'scissors': '剪刀', 'teddy bear': '泰迪熊',
    'hair drier': '吹风机', 'toothbrush': '牙刷'
}


def get_class_names(model_id: str):
    config = MODEL_CONFIGS.get(model_id)
    if not config:
        return GARBAGE_CLASS_NAMES
    if config['type'] == 'coco':
        return COCO_CLASS_NAMES
    return GARBAGE_CLASS_NAMES

# 模型缓存
models_cache = {}


def get_model(model_id: str):
    """获取模型（带缓存，避免重复加载）"""
    if model_id not in models_cache:
        config = MODEL_CONFIGS.get(model_id)
        if not config:
            raise ValueError(f'Unknown model: {model_id}')
        print(f'Loading model: {config["name"]} ({config["path"]})')
        models_cache[model_id] = YOLO(config['path'])
        print(f'Model {config["name"]} loaded successfully')
    return models_cache[model_id]


def get_available_models():
    """获取可用模型列表"""
    return [
        {
            'id': 'yolov5n',
            'name': 'YOLOv5 Nano (最快)',
            'size': '5.3 MB',
            'description': '轻量快速，适合实时检测',
            'type': 'garbage'
        },
        {
            'id': 'yolov5s',
            'name': 'YOLOv5 Small (推荐)',
            'size': '17.7 MB',
            'description': '速度和精度平衡',
            'type': 'garbage'
        },
        {
            'id': 'yolov5m',
            'name': 'YOLOv5 Medium (最准)',
            'size': '48.2 MB',
            'description': '精度最高，速度稍慢',
            'type': 'garbage'
        },
        {
            'id': 'yolov5s-coco',
            'name': 'YOLOv5 COCO (基准)',
            'size': '22.5 MB',
            'description': 'COCO预训练模型，用于对比测试',
            'type': 'coco'
        },
    ]


def process_detection(image_data, model_name='yolov5s', conf=0.6, iou=0.45):
    """
    处理检测请求

    Args:
        image_data: PIL Image 对象
        model_name: 模型名称
        conf: 置信度阈值
        iou: IoU 阈值

    Returns:
        检测结果字典
    """
    try:
        yolo_model = get_model(model_name)
        device = 0 if torch.cuda.is_available() else 'cpu'

        results = yolo_model.predict(
            image_data,
            conf=conf,
            iou=iou,
            verbose=False,
            device=device,
            max_det=50,
            agnostic_nms=True
        )

        detections = []
        counts = {}
        class_names = get_class_names(model_name)

        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls_id = int(box.cls[0])
                    cls_name = class_names[cls_id] if cls_id < len(class_names) else str(cls_id)
                    conf_score = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    detections.append({
                        'class': cls_name,
                        'confidence': round(conf_score, 4),
                        'bbox': [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)]
                    })

                    counts[cls_name] = counts.get(cls_name, 0) + 1

        annotated_result = results[0].plot()
        annotated_img = Image.fromarray(annotated_result)
        annotated_base64 = pil_to_base64(annotated_img)

        return {
            'success': True,
            'detections': detections,
            'annotated_image': annotated_base64,
            'counts': counts,
            'total': len(detections)
        }

    except Exception as e:
        print(f'Detection error: {e}')
        return {
            'success': False,
            'error': str(e),
            'detections': [],
            'counts': {},
            'annotated_image': None
        }


def pil_to_base64(img):
    """将 PIL Image 转换为 base64 字符串（不带 data URL 前缀）"""
    if img is None:
        return None
    buffered = io.BytesIO()
    img.save(buffered, format='JPEG', quality=85)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


# ==================== API 路由 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'message': 'Service is running',
        'cuda_available': torch.cuda.is_available(),
        'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    })


@app.route('/api/models', methods=['GET'])
def get_models():
    """获取可用模型列表"""
    return jsonify({
        'models': get_available_models(),
        'current': 'yolov5s',
        'loaded': list(models_cache.keys()),
    })


@app.route('/api/detect', methods=['POST'])
def detect_upload():
    """
    处理图片上传检测

    请求: multipart/form-data
        - image: 图片文件
        - model: 模型名称 (可选，默认 yolov5s)
        - conf: 置信度阈值 (可选，默认 0.5)
        - iou: IoU 阈值 (可选，默认 0.45)
    """
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image uploaded'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename'}), 400

    model_name = request.form.get('model', 'yolov5s')
    conf = float(request.form.get('conf', 0.5))
    iou = float(request.form.get('iou', 0.45))

    try:
        image = Image.open(file.stream).convert('RGB')
        result = process_detection(image, model_name, conf, iou)
        return jsonify(result)

    except Exception as e:
        print(f'Processing error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/detect_base64', methods=['POST'])
def detect_base64():
    """
    处理 base64 图片检测（用于摄像头实时检测）

    请求: JSON
        - image: base64 编码的图片数据
        - model: 模型名称 (可选，默认 yolov5s)
        - conf: 置信度阈值 (可选，默认 0.5)
        - iou: IoU 阈值 (可选，默认 0.45)
    """
    data = request.get_json()

    if not data or 'image' not in data:
        return jsonify({'success': False, 'error': 'No image data'}), 400

    model_name = data.get('model', 'yolov5s')
    conf = float(data.get('conf', 0.5))
    iou = float(data.get('iou', 0.45))

    try:
        image_data = base64.b64decode(data['image'])
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        result = process_detection(image, model_name, conf, iou)
        return jsonify(result)

    except Exception as e:
        print(f'Processing error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """下载标注后的图片/视频"""
    as_attachment = request.args.get('download', '0') == '1'
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=as_attachment)


@app.route('/api/detect_video', methods=['POST'])
def detect_video():
    """
    处理视频上传检测

    请求: multipart/form-data
        - video: 视频文件
        - model: 模型名称 (可选，默认 yolov5s)
        - conf: 置信度阈值 (可选，默认 0.6)
        - iou: IoU 阈值 (可选，默认 0.45)
        - frame_interval: 每隔多少帧检测一次 (可选，默认 10)
    """
    if 'video' not in request.files:
        return jsonify({'success': False, 'error': 'No video uploaded'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename'}), 400

    model_name = request.form.get('model', 'yolov5s')
    conf = float(request.form.get('conf', 0.6))
    iou = float(request.form.get('iou', 0.45))
    frame_interval = int(request.form.get('frame_interval', 10))

    temp_video_path = None
    temp_output_path = None

    try:
        yolo_model = get_model(model_name)
        device = 0 if torch.cuda.is_available() else 'cpu'

        suffix = os.path.splitext(file.filename)[1] or '.mp4'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            file.save(tmp.name)
            temp_video_path = tmp.name

        cap = cv2.VideoCapture(temp_video_path)
        if not cap.isOpened():
            return jsonify({'success': False, 'error': 'Failed to open video'}), 400

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        output_filename = f"{uuid.uuid4().hex}_annotated.mp4"
        temp_output_path = os.path.join(UPLOAD_FOLDER, output_filename)

        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(temp_output_path, fourcc, fps, (width, height))

        all_counts = {}
        frame_results = []
        frame_count = 0
        processed_count = 0
        class_names = get_class_names(model_name)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            if frame_count % frame_interval == 0 or frame_count == 1:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)

                results = yolo_model.predict(
                    pil_img,
                    conf=conf,
                    iou=iou,
                    verbose=False,
                    device=device,
                    max_det=50,
                    agnostic_nms=True
                )

                detections = []
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            cls_id = int(box.cls[0])
                            cls_name = class_names[cls_id] if cls_id < len(class_names) else str(cls_id)
                            conf_score = float(box.conf[0])
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            detections.append({
                                'class': cls_name,
                                'confidence': round(conf_score, 4),
                                'bbox': [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)]
                            })
                            all_counts[cls_name] = all_counts.get(cls_name, 0) + 1

                annotated_frame = results[0].plot()
                annotated_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
                out.write(annotated_bgr)

                processed_count += 1
                frame_results.append({
                    'frame': frame_count,
                    'time': round(frame_count / fps, 2),
                    'detections': detections
                })
            else:
                out.write(frame)

        cap.release()
        out.release()

        return jsonify({
            'success': True,
            'video_url': f'/api/download/{output_filename}',
            'total_frames': total_frames,
            'processed_frames': processed_count,
            'fps': fps,
            'duration': round(total_frames / fps, 2),
            'counts': all_counts,
            'total_detected': sum(all_counts.values()),
            'frame_results': frame_results
        })

    except Exception as e:
        print(f'Video detection error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.unlink(temp_video_path)
            except:
                pass


# ==================== 启动服务 ====================

if __name__ == '__main__':
    print('=' * 50)
    print('YOLO Garbage Detection Service')
    print('=' * 50)
    print(f'CUDA available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'GPU: {torch.cuda.get_device_name(0)}')
    print('=' * 50)
    print('Pre-loading default model (yolov5s)...')
    get_model('yolov5s')
    print('=' * 50)

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
