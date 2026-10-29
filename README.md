# 基于 YOLOv5 的垃圾分类检测系统

> 深度学习课程设计 · 第三组

一个基于 **YOLOv5** 的垃圾分类检测系统，支持 **图片检测**、**摄像头实时检测** 和 **视频检测**，提供 **Vue 3 Web 界面** 与 **CustomTkinter 桌面端** 两种交互方式。

---

## 项目简介

系统使用 YOLOv5n / YOLOv5s / YOLOv5m 三个规模的模型，在自建的五类垃圾数据集上进行训练与对比，并将训练结果封装为可交互的检测应用。

支持的垃圾类别：

| 类别 | 中文 | 说明 |
| --- | --- | --- |
| cardboard | 纸板 | 纸箱、硬纸板 |
| glass | 玻璃 | 玻璃瓶、玻璃器皿 |
| metal | 金属 | 易拉罐、金属罐 |
| paper | 纸张 | 报纸、打印纸 |
| plastic | 塑料 | 塑料瓶、塑料包装 |

## 功能特性

- **图片上传检测**：上传 JPG / PNG，返回标注图、类别、置信度与统计
- **摄像头实时检测**：浏览器调用摄像头，逐帧发送到后端推理
- **视频检测**：上传视频，按帧间隔抽帧检测并生成标注视频
- **多模型切换**：yolov5n（最快）/ yolov5s（均衡）/ yolov5m（最准），另含 COCO 预训练模型用于基准对比
- **参数可调**：置信度阈值、IoU 阈值、抽帧间隔
- **两种客户端**：Vue 3 + Vite Web 端、CustomTkinter 桌面端

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 检测模型 | YOLOv5（Ultralytics 实现） |
| 深度学习框架 | PyTorch |
| 后端 | Flask + Flask-CORS |
| 图像处理 | OpenCV、Pillow、NumPy |
| 前端 | Vue 3、TypeScript、Vite、Tailwind CSS |
| 桌面端 | CustomTkinter (Tkinter) |

## 目录结构

```text
yolov5-garbage-detection/
├── README.md
├── requirements.txt
├── train.py                     # 基础训练脚本
├── train_yolov5n.py             # YOLOv5n 实验
├── train_yolov5s.py             # YOLOv5s 实验
├── train_yolov5m.py             # YOLOv5m 实验
├── val.py                       # 验证脚本
├── detect.py                    # 批量图片检测脚本
├── camera_detect.py             # 摄像头检测脚本
├── labelme2yolo.py              # LabelMe 标注转 YOLO 格式
├── check_env.py                 # 环境检测
├── compare_experiments.py       # 实验结果对比
├── compare_three.py             # 三模型对比
├── generate_comparison_figs.py  # 对比图生成
├── experiment_results.yaml      # 实验结果记录
├── garbage.yaml                 # 数据集配置（训练用）
├── garbage_detection_ui_v2.py   # 桌面端主程序
├── start_UI.bat                 # 桌面端启动脚本
├── documents/
│   ├── PRD-垃圾分类检测系统.md   # 产品需求文档
│   └── TECH-垃圾分类检测系统.md  # 技术架构文档
├── garbage_dataset/
│   └── data.yaml                # 数据集配置（示例）
└── ui界面/
    ├── UI界面文档.md             # Web 端设计与接口文档
    ├── start.bat                # 一键启动前后端
    ├── backend/
    │   ├── app.py               # Flask API 服务
    │   ├── test_api.py          # API 测试
    │   └── test_model.py        # 模型推理测试
    └── frontend/                # Vue 3 前端源码
        ├── src/
        │   ├── components/
        │   ├── composables/
        │   ├── pages/
        │   └── router/
        ├── package.json
        └── vite.config.ts
```

## 环境要求

- Python 3.10+
- Node.js 18+（仅 Web 前端需要）
- 可选：NVIDIA GPU + CUDA（CPU 也可运行，速度较慢）

## 快速开始

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

> 如需 GPU 加速，请先按 PyTorch 官方指引安装对应 CUDA 版本的 PyTorch。

运行环境自检：

```bash
python check_env.py
```

### 2. 准备模型权重（未随仓库上传）

仓库不包含 `.pt` 权重文件。请通过本仓库的训练脚本自行训练，或联系作者获取，并按以下路径放置：

```text
<项目根目录>/
├── runs/detect/runs/train/
│   ├── exp1_yolov5s_bs16-2/weights/best.pt   # yolov5s
│   ├── exp2_yolov5m_bs8/weights/best.pt      # yolov5m
│   └── exp3_yolov5n_bs32/weights/best.pt     # yolov5n
└── yolov5su.pt                               # COCO 预训练模型（基准对比）
```

`ui界面/backend/app.py` 中的 `MODEL_CONFIGS` 就是按上述相对路径读取的，如放在其他位置请同步修改。

### 3. 准备数据集（未随仓库上传）

数据集体量较大，未包含在仓库中。目录格式如下：

```text
dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

训练前请修改 `garbage_dataset/data.yaml` 中的 `path` 字段，使其指向你的数据集根目录。

若使用 LabelMe 标注的数据，可先转换为 YOLO 格式：

```bash
python labelme2yolo.py
```

### 4. 启动 Web 系统

**方式一：Windows 一键启动**

双击 `ui界面/start.bat`（会分别启动 Flask 后端和 Vite 前端）。

**方式二：手动启动**

后端（默认 `http://localhost:5000`）：

```bash
cd ui界面/backend
python app.py
```

前端（默认 `http://localhost:3000`）：

```bash
cd ui界面/frontend
npm install
npm run dev
```

浏览器访问 `http://localhost:3000`。

### 5. 启动桌面端

```bash
python garbage_detection_ui_v2.py
```

或双击 `start_UI.bat`。

## 模型训练

三个规模的模型使用统一的训练配置（100 epochs、imgsz 640、SGD、余弦学习率、AMP）：

```bash
python train_yolov5s.py    # YOLOv5s, batch 16
python train_yolov5m.py    # YOLOv5m, batch 8
python train_yolov5n.py    # YOLOv5n, batch 32
```

或使用基础脚本：

```bash
python train.py
```

训练结果默认保存在 `runs/train/<实验名>/`。

验证与批量检测：

```bash
python val.py
python detect.py <图片或目录>
```

## 实验结果

在自建五类垃圾数据集上训练 100 epochs，最终验证集指标如下：

| 实验 | 模型 | Batch | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
| --- | --- | --- | --- | --- | --- | --- |
| exp1 | YOLOv5s | 16 | 0.9097 | 0.9188 | **0.9544** | **0.8383** |
| exp2 | YOLOv5m | 8 | 0.9307 | 0.9156 | 0.9555 | 0.8389 |
| exp3 | YOLOv5n | 32 | 0.8952 | 0.9257 | 0.9418 | 0.8194 |

> 指标取自各实验 `results.csv` 的最后一个 epoch。YOLOv5m 精度略高但速度较慢，YOLOv5n 体积最小、速度最快，YOLOv5s 综合表现最均衡。

## API 接口

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/health` | GET | 健康检查（含 CUDA / GPU 信息） |
| `/api/models` | GET | 获取可用模型列表 |
| `/api/detect` | POST | 图片检测（multipart/form-data） |
| `/api/detect_base64` | POST | 摄像头帧检测（JSON + base64） |
| `/api/detect_video` | POST | 视频检测（multipart/form-data） |
| `/api/download/<filename>` | GET | 下载标注后的图片 / 视频 |

请求与响应字段详见 [`documents/TECH-垃圾分类检测系统.md`](documents/TECH-垃圾分类检测系统.md) 与 [`ui界面/UI界面文档.md`](ui界面/UI界面文档.md)。

## 文档

- [产品需求文档 PRD](documents/PRD-垃圾分类检测系统.md)
- [技术架构文档](documents/TECH-垃圾分类检测系统.md)
- [Web 界面文档](ui界面/UI界面文档.md)

## 说明

- 本仓库仅包含**源代码与文档**。模型权重、数据集、训练产物（`runs/`）、前端依赖与构建产物（`node_modules/`、`dist/`）均已通过 `.gitignore` 排除。
- 仓库中所有本机绝对路径与用户名已做脱敏/相对化处理；如训练或部署时路径不一致，请按上述说明修改配置。
- 本项目为课程设计作品，仅供学习与交流使用。

## 致谢

- [Ultralytics YOLOv5](https://github.com/ultralytics/yolov5)
- [Vue.js](https://vuejs.org/)、[Vite](https://vitejs.dev/)、[Tailwind CSS](https://tailwindcss.com/)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
