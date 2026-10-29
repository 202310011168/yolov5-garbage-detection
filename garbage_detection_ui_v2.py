#!/usr/bin/env python
"""YOLOv5 垃圾分类实时检测系统 - CustomTkinter 桌面版"""

import os
import threading
import time
import traceback
from pathlib import Path

import cv2
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk
from ultralytics import YOLO

import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]

CLASS_NAMES = ['cardboard', 'glass', 'metal', 'paper', 'plastic']
CLASS_CN = {
    'cardboard': '纸板',
    'glass': '玻璃',
    'metal': '金属',
    'paper': '纸张',
    'plastic': '塑料',
}
CLASS_COLORS_BGR = {
    'cardboard': (19, 69, 139),
    'glass': (255, 255, 0),
    'metal': (192, 192, 192),
    'paper': (0, 255, 0),
    'plastic': (0, 0, 255),
}

# ── COCO 80 类中文映射 ──
COCO_CLASSES = {
    0: '人', 1: '自行车', 2: '汽车', 3: '摩托车', 4: '飞机',
    5: '公交车', 6: '火车', 7: '卡车', 8: '船', 9: '交通灯',
    10: '消防栓', 11: '停车标志', 12: '停车计时器', 13: '长椅',
    14: '鸟', 15: '猫', 16: '狗', 17: '马', 18: '羊', 19: '牛',
    20: '大象', 21: '熊', 22: '斑马', 23: '长颈鹿', 24: '背包',
    25: '雨伞', 26: '手提包', 27: '领带', 28: '行李箱', 29: '飞盘',
    30: '滑雪板', 31: '单板滑雪', 32: '球', 33: '风筝', 34: '棒球棒',
    35: '棒球手套', 36: '滑板', 37: '冲浪板', 38: '网球拍', 39: '瓶子',
    40: '酒杯', 41: '杯子', 42: '叉子', 43: '刀', 44: '勺子',
    45: '碗', 46: '香蕉', 47: '苹果', 48: '三明治', 49: '橙子',
    50: '西兰花', 51: '胡萝卜', 52: '热狗', 53: '披萨', 54: '甜甜圈',
    55: '蛋糕', 56: '椅子', 57: '沙发', 58: '盆栽', 59: '床',
    60: '餐桌', 61: '厕所', 62: '电视', 63: '笔记本', 64: '鼠标',
    65: '遥控器', 66: '键盘', 67: '手机', 68: '微波炉', 69: '烤箱',
    70: '烤面包机', 71: '水槽', 72: '冰箱', 73: '书', 74: '时钟',
    75: '花瓶', 76: '剪刀', 77: '泰迪熊', 78: '吹风机', 79: '牙刷',
}

# COCO 检测框调色板（BGR，按类别 id 取模循环使用）
COCO_PALETTE_BGR = [
    (255, 165, 0), (255, 0, 0), (0, 255, 0), (0, 255, 255),
    (255, 0, 255), (0, 165, 255), (128, 0, 255), (0, 128, 255),
    (255, 255, 0), (0, 255, 128), (255, 128, 0), (128, 255, 0),
]

# ── 检测模式 ──
MODE_GARBAGE = 'garbage'
MODE_COCO = 'coco'

# ── 模型路径 ──
MODEL_PATHS = {
    'yolov5n': ROOT / 'runs' / 'detect' / 'runs' / 'train' / 'exp3_yolov5n_bs32' / 'weights' / 'best.pt',
    'yolov5s': ROOT / 'runs' / 'detect' / 'runs' / 'train' / 'exp1_yolov5s_bs16-2' / 'weights' / 'best.pt',
    'yolov5m': ROOT / 'runs' / 'detect' / 'runs' / 'train' / 'exp2_yolov5m_bs8' / 'weights' / 'best.pt',
}

MODEL_LABELS = {
    'yolov5n': 'YOLOv5 Nano (5n - 最快)',
    'yolov5s': 'YOLOv5 Small (5s - 推荐)',
    'yolov5m': 'YOLOv5 Medium (5m - 最准)',
}

# COCO 预训练模型（根目录下的 .pt 文件）
COCO_MODEL_PATHS = {
    'coco_5n': ROOT / 'yolov5nu.pt',
    'coco_5s': ROOT / 'yolov5su.pt',
    'coco_5m': ROOT / 'yolov5mu.pt',
}

COCO_MODEL_LABELS = {
    'coco_5n': 'COCO Nano (5n - 最快)',
    'coco_5s': 'COCO Small (5s - 推荐)',
    'coco_5m': 'COCO Medium (5m - 最准)',
}


def get_font(size: int) -> ImageFont.FreeTypeFont:
    font_paths = [
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/simsun.ttc',
    ]
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()


class GarbageDetector:
    def __init__(self):
        self.model = None
        self.device = None
        self.loaded = False
        self.current_model_key = None
        self.mode = MODE_GARBAGE          # 当前检测模式

    def load_model(self, model_key: str, mode: str = MODE_GARBAGE):
        if self.loaded and self.current_model_key == model_key:
            return True, None

        self.mode = mode
        paths = COCO_MODEL_PATHS if mode == MODE_COCO else MODEL_PATHS
        model_path = paths.get(model_key)
        if model_path is None or not model_path.exists():
            return False, f"模型文件不存在: {model_path}"

        try:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.model = YOLO(str(model_path))
            self.model.to(self.device)
            self.loaded = True
            self.current_model_key = model_key
            return True, None
        except Exception as e:
            traceback.print_exc()
            return False, str(e)

    def detect(self, image: np.ndarray, conf_thres: float = 0.6, iou_thres: float = 0.45):
        if not self.loaded or self.model is None:
            return image, []

        try:
            results = self.model.predict(
                image,
                conf=conf_thres,
                iou=iou_thres,
                verbose=False,
                device=self.device,
                max_det=50,
                agnostic_nms=True,
            )

            detections = []
            annotated = image.copy()

            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                        if self.mode == MODE_COCO:
                            cls_name = COCO_CLASSES.get(cls_id, f'类别{cls_id}')
                            color = COCO_PALETTE_BGR[cls_id % len(COCO_PALETTE_BGR)]
                        else:
                            cls_name = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else str(cls_id)
                            color = CLASS_COLORS_BGR.get(cls_name, (0, 255, 0))

                        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                        detections.append({
                            'class': cls_name,
                            'class_id': cls_id,
                            'confidence': conf,
                            'bbox': [x1, y1, x2, y2],
                            'color': color,
                        })

            if detections:
                annotated = self._draw_labels(annotated, detections)

            return annotated, detections
        except Exception as e:
            traceback.print_exc()
            return image, []

    def _draw_labels(self, image: np.ndarray, detections: list) -> np.ndarray:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        draw = ImageDraw.Draw(pil_img)
        font = get_font(18)

        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cls_name = det['class']
            conf = det['confidence']
            bgr_color = det['color']
            rgb_color = (bgr_color[2], bgr_color[1], bgr_color[0])

            # COCO 模式直接用中文名；垃圾模式查 CLASS_CN
            if self.mode == MODE_COCO:
                display_name = cls_name
            else:
                display_name = CLASS_CN.get(cls_name, cls_name)
            label = f"{display_name} {conf:.0%}"

            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]

            draw.rectangle([x1, y1, x2, y2], outline=rgb_color, width=2)

            label_y = y1 - th - 6
            if label_y < 0:
                label_y = y1
            draw.rectangle([x1, label_y, x1 + tw + 6, label_y + th + 4], fill=rgb_color)
            draw.text((x1 + 3, label_y + 2), label, fill=(255, 255, 255), font=font)

        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("垃圾分类智能检测系统")
        self.geometry("1280x800")
        self.minsize(1024, 600)

        self.detector = GarbageDetector()
        self.cap = None
        self.running = False
        self.camera_thread = None
        self.current_frame = None
        self.annotated_frame = None
        self.detections = []
        self.video_path = None
        self.video_playing = False
        self.image_mode = False
        self._canvas_img_id = None
        self.current_mode = MODE_GARBAGE

        self._setup_ui()
        self._load_default_model()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(main_frame, width=280)
        sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        sidebar.grid_propagate(False)

        self._setup_sidebar(sidebar)

        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=0)

        self._setup_display(right_frame)
        self._setup_controls(right_frame)

    def _setup_sidebar(self, parent):
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=0)
        parent.grid_rowconfigure(2, weight=0)
        parent.grid_rowconfigure(3, weight=0)
        parent.grid_rowconfigure(4, weight=1)

        title = ctk.CTkLabel(
            parent, text="垃圾分类检测",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        subtitle = ctk.CTkLabel(
            parent, text="基于 YOLOv5 实时检测",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        subtitle.grid(row=0, column=0, padx=15, pady=(40, 15), sticky="w")

        # ── 检测模式切换 ──
        mode_frame = ctk.CTkFrame(parent)
        mode_frame.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")
        mode_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            mode_frame, text="检测模式",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=(8, 4), sticky="w")

        self.mode_var = ctk.StringVar(value="垃圾分类")
        self.mode_menu = ctk.CTkOptionMenu(
            mode_frame,
            values=["垃圾分类", "COCO 通用检测"],
            variable=self.mode_var,
            command=self._on_mode_change,
            font=ctk.CTkFont(size=12),
            width=200,
        )
        self.mode_menu.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")

        model_frame = ctk.CTkFrame(parent)
        model_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        model_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            model_frame, text="模型选择",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.model_var = ctk.StringVar(value=list(MODEL_LABELS.values())[1])  # 默认 5s
        self.model_menu = ctk.CTkOptionMenu(
            model_frame,
            values=list(MODEL_LABELS.values()),
            variable=self.model_var,
            command=self._on_model_change,
            font=ctk.CTkFont(size=12),
        )
        self.model_menu.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")

        self.model_status = ctk.CTkLabel(
            model_frame, text="加载中...",
            font=ctk.CTkFont(size=11),
            text_color="orange",
        )
        self.model_status.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")

        params_frame = ctk.CTkFrame(parent)
        params_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        params_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            params_frame, text="参数设置",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        ctk.CTkLabel(params_frame, text="置信度阈值", font=ctk.CTkFont(size=11)).grid(
            row=1, column=0, padx=10, pady=(5, 0), sticky="w"
        )
        self.conf_var = ctk.DoubleVar(value=0.6)
        self.conf_slider = ctk.CTkSlider(
            params_frame, from_=0.1, to=1.0, variable=self.conf_var,
            number_of_steps=18, command=self._on_conf_change,
        )
        self.conf_slider.grid(row=2, column=0, padx=10, pady=(0, 0), sticky="ew")
        self.conf_label = ctk.CTkLabel(
            params_frame, text="0.60", font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#3b8ed0",
        )
        self.conf_label.grid(row=3, column=0, padx=10, pady=(0, 5))

        ctk.CTkLabel(params_frame, text="IoU 阈值", font=ctk.CTkFont(size=11)).grid(
            row=4, column=0, padx=10, pady=(5, 0), sticky="w"
        )
        self.iou_var = ctk.DoubleVar(value=0.45)
        self.iou_slider = ctk.CTkSlider(
            params_frame, from_=0.1, to=1.0, variable=self.iou_var,
            number_of_steps=18, command=self._on_iou_change,
        )
        self.iou_slider.grid(row=5, column=0, padx=10, pady=(0, 0), sticky="ew")
        self.iou_label = ctk.CTkLabel(
            params_frame, text="0.45", font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#3b8ed0",
        )
        self.iou_label.grid(row=6, column=0, padx=10, pady=(0, 10))

        result_frame = ctk.CTkFrame(parent)
        result_frame.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="nsew")
        result_frame.grid_columnconfigure(0, weight=1)
        result_frame.grid_rowconfigure(0, weight=0)
        result_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            result_frame, text="检测结果",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.result_text = ctk.CTkTextbox(
            result_frame, font=ctk.CTkFont(size=12), wrap="word",
        )
        self.result_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.result_text.insert("end", "等待模型加载...\n")

    def _setup_display(self, parent):
        self.canvas = ctk.CTkCanvas(parent, bg="#1a1a1a", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 0))

        self.status_var = ctk.StringVar(value="就绪")
        self.status_bar = ctk.CTkLabel(
            parent, textvariable=self.status_var,
            font=ctk.CTkFont(size=11), text_color="gray",
            anchor="w",
        )
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 0))

    def _setup_controls(self, parent):
        ctrl_frame = ctk.CTkFrame(parent, fg_color="transparent")
        ctrl_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        ctrl_frame.grid_columnconfigure(0, weight=1)

        btn_frame = ctk.CTkFrame(ctrl_frame)
        btn_frame.pack(side="left", fill="x", expand=True)

        self.btn_camera = ctk.CTkButton(
            btn_frame, text="📷 启动摄像头", width=120,
            fg_color="#2e7d32", hover_color="#1b5e20",
            command=self._toggle_camera,
            font=ctk.CTkFont(size=12),
        )
        self.btn_camera.pack(side="left", padx=(0, 5))

        self.btn_image = ctk.CTkButton(
            btn_frame, text="🖼️ 检测图片", width=110,
            command=self._upload_image,
            font=ctk.CTkFont(size=12),
        )
        self.btn_image.pack(side="left", padx=5)

        self.btn_video = ctk.CTkButton(
            btn_frame, text="🎬 检测视频", width=110,
            command=self._upload_video,
            font=ctk.CTkFont(size=12),
        )
        self.btn_video.pack(side="left", padx=5)

        self.btn_stop = ctk.CTkButton(
            btn_frame, text="⏹ 停止", width=80,
            fg_color="#c62828", hover_color="#b71c1c",
            command=self._stop_all,
            font=ctk.CTkFont(size=12),
        )
        self.btn_stop.pack(side="left", padx=5)

        self.fps_label = ctk.CTkLabel(
            btn_frame, text="FPS: --",
            font=ctk.CTkFont(size=12), text_color="gray",
        )
        self.fps_label.pack(side="right", padx=10)

    def _load_default_model(self):
        def _load():
            self.model_status.configure(text="加载中...", text_color="orange")
            model_key = self._get_model_key()
            success, error = self.detector.load_model(model_key, self.current_mode)
            self.after(0, lambda: self._on_model_loaded(success, error))
        threading.Thread(target=_load, daemon=True).start()

    def _on_model_loaded(self, success, error):
        if success:
            device = "CUDA" if torch.cuda.is_available() else "CPU"
            mode_text = "COCO 通用" if self.current_mode == MODE_COCO else "垃圾分类"
            self.model_status.configure(
                text=f"{mode_text} · {device}",
                text_color="#4caf50",
            )
            self.status_var.set(f"{mode_text} 模型就绪 · {device}")
            self._update_results(f"{mode_text} 模型加载成功！\n")
        else:
            self.model_status.configure(text="加载失败", text_color="#f44336")
            self.status_var.set("模型加载失败")
            self._update_results(f"模型加载失败: {error}\n")

    def _get_model_key(self) -> str:
        label = self.model_var.get()
        labels = COCO_MODEL_LABELS if self.current_mode == MODE_COCO else MODEL_LABELS
        for key, lbl in labels.items():
            if lbl == label:
                return key
        # 回退默认
        return 'coco_5s' if self.current_mode == MODE_COCO else 'yolov5s'

    def _on_model_change(self, choice):
        self.model_status.configure(text="切换中...", text_color="orange")
        def _switch():
            model_key = self._get_model_key()
            success, error = self.detector.load_model(model_key, self.current_mode)
            self.after(0, lambda: self._on_model_loaded(success, error))
        threading.Thread(target=_switch, daemon=True).start()

    def _on_mode_change(self, choice):
        """切换检测模式时，更新模型下拉列表并重新加载"""
        if choice == "COCO 通用检测":
            self.current_mode = MODE_COCO
            labels = list(COCO_MODEL_LABELS.values())
            default_key = 'coco_5s'
        else:
            self.current_mode = MODE_GARBAGE
            labels = list(MODEL_LABELS.values())
            default_key = 'yolov5s'

        self.model_menu.configure(values=labels)
        # 找到默认模型的显示名
        label_map = COCO_MODEL_LABELS if self.current_mode == MODE_COCO else MODEL_LABELS
        default_label = label_map.get(default_key, labels[0])
        self.model_var.set(default_label)

        # 强制重新加载
        self.detector.loaded = False
        self.detector.current_model_key = None
        self.model_status.configure(text="切换中...", text_color="orange")

        def _switch():
            model_key = self._get_model_key()
            success, error = self.detector.load_model(model_key, self.current_mode)
            self.after(0, lambda: self._on_model_loaded(success, error))
        threading.Thread(target=_switch, daemon=True).start()

    def _on_conf_change(self, value):
        self.conf_label.configure(text=f"{float(value):.2f}")

    def _on_iou_change(self, value):
        self.iou_label.configure(text=f"{float(value):.2f}")

    def _toggle_camera(self):
        if self.running:
            self._stop_camera()
        else:
            self._start_camera()

    def _start_camera(self):
        if self.running:
            return
        self._stop_all()
        self.image_mode = False
        self.video_playing = False

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("错误", "无法打开摄像头")
            self.cap = None
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.running = True
        self.btn_camera.configure(text="⏸ 暂停摄像头", fg_color="#e65100", hover_color="#bf360c")
        self.status_var.set("摄像头运行中...")
        self._update_results("摄像头已启动\n")

        self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.camera_thread.start()

    def _stop_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.btn_camera.configure(text="📷 启动摄像头", fg_color="#2e7d32", hover_color="#1b5e20")
        self.status_var.set("摄像头已停止")
        self.fps_label.configure(text="FPS: --")
        self._update_results("摄像头已停止\n")

    def _camera_loop(self):
        fps_times = []
        while self.running:
            if self.cap is None:
                break
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)

            t0 = time.time()
            annotated, dets = self.detector.detect(
                frame,
                conf_thres=self.conf_var.get(),
                iou_thres=self.iou_var.get(),
            )
            t1 = time.time()

            fps_times.append(t1 - t0)
            if len(fps_times) > 30:
                fps_times.pop(0)
            fps = 1.0 / (sum(fps_times) / len(fps_times)) if fps_times else 0

            self.annotated_frame = annotated
            self.detections = dets

            # 所有 UI 更新必须通过 self.after 派发到主线程，
            # 否则后台线程直接操作 Canvas 会导致画面闪烁
            self.after(0, lambda a=annotated: self._update_canvas(a))
            self.after(0, lambda f=fps: self._update_fps(f))
            self.after(0, lambda d=dets: self._update_detection_results(d))

        self.after(0, self._stop_camera)

    def _upload_image(self):
        self._stop_all()
        self.image_mode = True

        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp"), ("所有文件", "*.*")],
        )
        if not file_path:
            return

        self.status_var.set(f"检测图片: {os.path.basename(file_path)}")
        self._update_results(f"检测图片: {file_path}\n")

        image = cv2.imread(file_path)
        if image is None:
            messagebox.showerror("错误", "无法读取图片")
            return

        self._show_image_on_canvas(image)

        def _detect():
            annotated, dets = self.detector.detect(
                image,
                conf_thres=self.conf_var.get(),
                iou_thres=self.iou_var.get(),
            )
            self.after(0, lambda: self._on_image_detected(annotated, dets))

        threading.Thread(target=_detect, daemon=True).start()

    def _on_image_detected(self, annotated, dets):
        self.annotated_frame = annotated
        self.detections = dets
        self._update_canvas(annotated)
        self._update_detection_results(dets)
        self.status_var.set("图片检测完成")
        self._update_results(f"检测完成，共 {len(dets)} 个目标\n")

    def _upload_video(self):
        self._stop_all()
        self.image_mode = False
        self.video_playing = False

        file_path = filedialog.askopenfilename(
            title="选择视频",
            filetypes=[("视频文件", "*.mp4 *.avi *.mov *.mkv"), ("所有文件", "*.*")],
        )
        if not file_path:
            return

        self.video_path = file_path
        self.video_playing = True
        self.status_var.set(f"播放视频: {os.path.basename(file_path)}")
        self._update_results(f"播放视频: {file_path}\n")

        def _play():
            cap = cv2.VideoCapture(file_path)
            fps_times = []
            while self.video_playing and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                t0 = time.time()
                annotated, dets = self.detector.detect(
                    frame,
                    conf_thres=self.conf_var.get(),
                    iou_thres=self.iou_var.get(),
                )
                t1 = time.time()

                fps_times.append(t1 - t0)
                if len(fps_times) > 30:
                    fps_times.pop(0)
                fps = 1.0 / (sum(fps_times) / len(fps_times)) if fps_times else 0

                self.annotated_frame = annotated
                self.detections = dets

                self.after(0, lambda a=annotated: self._update_canvas(a))
                self.after(0, lambda f=fps: self._update_fps(f))
                self.after(0, lambda d=dets: self._update_detection_results(d))

                delay = int(1000 / 30)
                cv2.waitKey(delay)

            cap.release()
            self.after(0, self._on_video_end)

        threading.Thread(target=_play, daemon=True).start()

    def _on_video_end(self):
        self.video_playing = False
        self.status_var.set("视频播放完毕")
        self.fps_label.configure(text="FPS: --")
        self._update_results("视频播放完毕\n")

    def _stop_all(self):
        self._stop_camera()
        self.video_playing = False
        self.image_mode = False
        self.detections = []
        self.annotated_frame = None
        self.canvas.delete("all")
        self._canvas_img_id = None
        self.status_var.set("就绪")
        self.fps_label.configure(text="FPS: --")
        self._update_results("已停止\n")

    def _update_canvas(self, image: np.ndarray):
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w < 10 or canvas_h < 10:
            return

        img_h, img_w = image.shape[:2]
        scale = min(canvas_w / img_w, canvas_h / img_h)
        dw = int(img_w * scale)
        dh = int(img_h * scale)

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb).resize((dw, dh), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(pil_img)

        ox = (canvas_w - dw) // 2
        oy = (canvas_h - dh) // 2

        # 复用已有 image item，避免 delete+create 造成的闪烁
        if getattr(self, '_canvas_img_id', None) is not None:
            self.canvas.itemconfig(self._canvas_img_id, image=self._photo)
            self.canvas.coords(self._canvas_img_id, ox, oy)
        else:
            self._canvas_img_id = self.canvas.create_image(
                ox, oy, anchor="nw", image=self._photo,
            )

    def _show_image_on_canvas(self, image: np.ndarray):
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w < 10 or canvas_h < 10:
            canvas_w = 800
            canvas_h = 560

        img_h, img_w = image.shape[:2]
        scale = min(canvas_w / img_w, canvas_h / img_h)
        dw = int(img_w * scale)
        dh = int(img_h * scale)

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb).resize((dw, dh), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(pil_img)

        ox = (canvas_w - dw) // 2
        oy = (canvas_h - dh) // 2

        if getattr(self, '_canvas_img_id', None) is not None:
            self.canvas.itemconfig(self._canvas_img_id, image=self._photo)
            self.canvas.coords(self._canvas_img_id, ox, oy)
        else:
            self._canvas_img_id = self.canvas.create_image(
                ox, oy, anchor="nw", image=self._photo,
            )

    def _update_fps(self, fps: float):
        self.fps_label.configure(text=f"FPS: {fps:.1f}")

    def _update_detection_results(self, detections: list):
        if not detections:
            return

        counts = {}
        for d in detections:
            name = d['class']
            counts[name] = counts.get(name, 0) + 1

        lines = ["──── 检测结果 ────"]

        if self.current_mode == MODE_COCO:
            # COCO 模式：只显示检测到的类别
            for cls_name, count in sorted(counts.items(), key=lambda x: -x[1]):
                bar = "█" * min(count, 20)
                lines.append(f"  {cls_name}: {count}  {bar}")
        else:
            # 垃圾模式：显示全部 5 个类别
            for cls_name in CLASS_NAMES:
                count = counts.get(cls_name, 0)
                cn = CLASS_CN.get(cls_name, cls_name)
                bar = "█" * min(count, 20)
                lines.append(f"  {cn}: {count}  {bar}")

        lines.append(f"  总计: {len(detections)} 个目标")

        top5 = sorted(detections, key=lambda d: d['confidence'], reverse=True)[:5]
        if top5:
            lines.append("──── 置信度 TOP5 ────")
            for d in top5:
                lines.append(f"  {d['class']}: {d['confidence']:.1%}")

        self._update_results("")
        self._update_results("\n".join(lines) + "\n")

    def _update_results(self, text: str):
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", text)

    def _on_close(self):
        self._stop_all()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()