# YOLO 垃圾分类智能检测系统 - UI界面文档

## 一、项目概述

本项目是一个基于 YOLOv5 的垃圾分类智能检测系统，提供 Web 界面进行实时目标检测。系统采用前后端分离架构，支持**图片检测**、**视频检测**和**摄像头实时检测**三种模式。

---

## 二、技术栈

### 前端 (frontend/)

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue 3 | ^3.4.15 | 前端框架，使用 Composition API |
| TypeScript | ~5.3.3 | 类型安全 |
| Vite | ^5.0.12 | 构建工具 |
| Vue Router | ^4.2.5 | 路由管理 |
| TailwindCSS | ^3.4.19 | 原子化 CSS 框架 |
| Lucide Vue Next | ^0.511.0 | 图标库 |

### 后端 (backend/)

| 技术 | 说明 |
|------|------|
| Flask | Python Web 框架 |
| Flask-CORS | 跨域支持 |
| Ultralytics YOLO | 目标检测模型 |
| PyTorch | 深度学习框架，支持 GPU 加速 |
| OpenCV | 视频处理 |
| PIL | 图像处理 |

---

## 三、项目结构

```
ui界面/
├── backend/                    # 后端服务
│   ├── app.py                  # Flask 主应用，API 接口
│   ├── test_api.py             # API 测试脚本
│   ├── test_model.py           # 模型测试脚本
│   └── uploads/                # 上传文件存储目录
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── main.ts             # 应用入口
│   │   ├── App.vue             # 根组件
│   │   ├── style.css           # 全局样式（B站深色主题）
│   │   ├── router/
│   │   │   └── index.ts        # 路由配置
│   │   ├── pages/
│   │   │   └── HomePage.vue    # 主页（实际为空，逻辑在 App.vue）
│   │   ├── components/
│   │   │   ├── CameraView.vue      # 摄像头检测组件
│   │   │   ├── ControlPanel.vue    # 参数控制面板
│   │   │   ├── ImageList.vue       # 图片列表组件
│   │   │   ├── ImageUpload.vue     # 图片上传组件
│   │   │   ├── ResultPanel.vue     # 检测结果面板
│   │   │   ├── VideoPlayer.vue     # 视频播放器组件
│   │   │   ├── TabSwitch.vue       # Tab 切换组件（未使用）
│   │   │   └── Empty.vue           # 空组件（占位）
│   │   ├── composables/
│   │   │   ├── useDetection.ts     # 检测逻辑封装（API 调用）
│   │   │   └── useTheme.ts         # 主题切换（未使用）
│   │   ├── utils/
│   │   │   └── classNames.ts       # 类别中文名和颜色映射
│   │   └── lib/
│   │       └── utils.ts            # 工具函数（cn class 合并）
│   ├── public/
│   │   └── favicon.svg         # 网站图标
│   ├── index.html              # HTML 入口
│   ├── package.json            # 依赖配置
│   ├── vite.config.ts          # Vite 配置
│   ├── tailwind.config.js      # Tailwind 配置
│   └── postcss.config.js       # PostCSS 配置
```

---

## 四、后端 API 接口

### 4.1 健康检查

```
GET /api/health
```

**响应示例：**
```json
{
  "status": "ok",
  "message": "Service is running",
  "cuda_available": true,
  "gpu": "NVIDIA GeForce RTX 4060 Laptop"
}
```

---

### 4.2 获取模型列表

```
GET /api/models
```

**响应示例：**
```json
{
  "models": [
    {
      "id": "yolov5n",
      "name": "YOLOv5 Nano (最快)",
      "size": "5.3 MB",
      "description": "轻量快速，适合实时检测",
      "type": "garbage"
    },
    {
      "id": "yolov5s",
      "name": "YOLOv5 Small (推荐)",
      "size": "17.7 MB",
      "description": "速度和精度平衡",
      "type": "garbage"
    },
    {
      "id": "yolov5m",
      "name": "YOLOv5 Medium (最准)",
      "size": "48.2 MB",
      "description": "精度最高，速度稍慢",
      "type": "garbage"
    },
    {
      "id": "yolov5s-coco",
      "name": "YOLOv5 COCO (基准)",
      "size": "22.5 MB",
      "description": "COCO预训练模型，用于对比测试",
      "type": "coco"
    }
  ],
  "current": "yolov5s",
  "loaded": ["yolov5s"]
}
```

---

### 4.3 图片检测（文件上传）

```
POST /api/detect
Content-Type: multipart/form-data
```

**请求参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| image | File | 是 | - | 图片文件 |
| model | string | 否 | yolov5s | 模型名称 |
| conf | float | 否 | 0.5 | 置信度阈值 (0.1-1.0) |
| iou | float | 否 | 0.45 | IoU 阈值 (0.1-1.0) |

**响应示例：**
```json
{
  "success": true,
  "detections": [
    {
      "class": "cardboard",
      "confidence": 0.9234,
      "bbox": [100.5, 200.3, 300.8, 400.1]
    }
  ],
  "annotated_image": "base64编码的标注图片字符串",
  "counts": {
    "cardboard": 2,
    "plastic": 1
  },
  "total": 3
}
```

---

### 4.4 图片检测（Base64）

```
POST /api/detect_base64
Content-Type: application/json
```

**请求体：**
```json
{
  "image": "base64编码的图片数据",
  "model": "yolov5s",
  "conf": 0.5,
  "iou": 0.45
}
```

**响应：** 同 `/api/detect`

> **用途：** 主要用于摄像头实时检测和视频帧检测

---

### 4.5 视频检测

```
POST /api/detect_video
Content-Type: multipart/form-data
```

**请求参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| video | File | 是 | - | 视频文件 |
| model | string | 否 | yolov5s | 模型名称 |
| conf | float | 否 | 0.6 | 置信度阈值 |
| iou | float | 否 | 0.45 | IoU 阈值 |
| frame_interval | int | 否 | 10 | 每隔多少帧检测一次 |

**响应示例：**
```json
{
  "success": true,
  "video_url": "/api/download/xxx_annotated.mp4",
  "total_frames": 300,
  "processed_frames": 30,
  "fps": 30.0,
  "duration": 10.0,
  "counts": {
    "cardboard": 5,
    "plastic": 3
  },
  "total_detected": 8,
  "frame_results": [
    {
      "frame": 1,
      "time": 0.03,
      "detections": [...]
    }
  ]
}
```

---

### 4.6 文件下载

```
GET /api/download/<filename>?download=1
```

**参数说明：**
- `filename`: 文件名（如 `xxx_annotated.mp4`）
- `download=1`: 设置为附件下载模式

---

## 五、前端组件详解

### 5.1 App.vue（根组件）

**功能：** 主应用容器，包含所有核心逻辑

**主要功能模块：**

| 功能 | 说明 |
|------|------|
| 模式切换 | 摄像头检测 / 图片检测 / 视频检测 |
| 图片管理 | 图片列表、切换、批量检测、批量下载 |
| 视频管理 | 视频上传、完整检测、实时预览 |
| 摄像头管理 | 启动/停止摄像头、实时检测 |
| 参数控制 | 模型选择、置信度、IoU 阈值 |

**数据流：**
```
用户操作 → useDetection API 调用 → 后端处理 → 返回结果 → 更新 UI
```

---

### 5.2 CameraView.vue（摄像头组件）

**功能：** 摄像头实时检测

**Props：**
| 属性 | 类型 | 说明 |
|------|------|------|
| currentModel | string | 当前使用的模型 |
| confidence | number | 置信度阈值 |
| iou | number | IoU 阈值 |

**Events：**
| 事件 | 参数 | 说明 |
|------|------|------|
| detections | (detections, counts) | 实时检测结果 |

**核心特性：**
- 使用 `getUserMedia` API 访问摄像头
- 每 400ms 抓取一帧进行检测
- 检测结果**防抖稳定化**（IoU 匹配，2 帧历史）
- Canvas 覆盖层绘制检测框
- 镜像显示（`scaleX(-1)`）

---

### 5.3 VideoPlayer.vue（视频播放器）

**功能：** 视频播放与实时检测

**Props：**
| 属性 | 类型 | 说明 |
|------|------|------|
| videoSrc | string | 原始视频 URL |
| annotatedSrc | string | 标注后视频 URL（可选） |
| currentModel | string | 当前模型 |
| confidence | number | 置信度阈值 |
| iou | number | IoU 阈值 |
| detectInterval | number | 检测间隔（默认 300ms） |

**Events：**
| 事件 | 参数 | 说明 |
|------|------|------|
| detections | (detections, counts) | 实时检测结果 |
| loaded | - | 视频加载完成 |
| upload | (file) | 拖放上传视频 |

**核心特性：**
- 支持原始视频和标注视频切换显示
- 播放时实时检测（可配置间隔）
- 检测结果防抖稳定化
- 支持拖放上传
- 有标注视频时自动停止实时检测

---

### 5.4 ImageList.vue（图片列表）

**功能：** 图片上传与管理

**Props：**
| 属性 | 类型 | 说明 |
|------|------|------|
| images | ImageItem[] | 图片列表 |
| currentIndex | number | 当前选中索引 |

**Events：**
| 事件 | 参数 | 说明 |
|------|------|------|
| select | (index) | 选择图片 |
| upload | (files) | 上传文件 |

**功能：**
- 支持单文件/多文件上传
- 支持文件夹上传（`webkitdirectory`）
- 支持拖放上传
- 显示缩略图、检测状态、检测结果标签

---

### 5.5 ControlPanel.vue（控制面板）

**功能：** 检测参数配置

**Props：**
| 属性 | 类型 | 说明 |
|------|------|------|
| models | Model[] | 可用模型列表 |
| currentModel | string | 当前模型 |
| confidence | number | 置信度阈值 |
| iou | number | IoU 阈值 |

**Events：**
| 事件 | 参数 | 说明 |
|------|------|------|
| update:currentModel | (value) | 切换模型 |
| update:confidence | (value) | 修改置信度 |
| update:iou | (value) | 修改 IoU |

**UI 元素：**
- 模型选择下拉框
- 置信度滑块（0.1-1.0，步长 0.05）
- IoU 滑块（0.1-1.0，步长 0.05）

---

### 5.6 ResultPanel.vue（结果面板）

**功能：** 显示检测结果

**Props：**
| 属性 | 类型 | 说明 |
|------|------|------|
| detections | Detection[] | 检测列表 |
| counts | Record<string, number> | 各类别数量统计 |

**显示内容：**
- 总检测数量（大字显示）
- 类别统计（带进度条）
- 检测详情列表（类别 + 置信度）

---

### 5.7 ImageUpload.vue（图片上传组件）

> **注：** 此组件在当前主界面中未被使用，功能已集成到 ImageList.vue

**功能：** 单张图片上传与预览

---

### 5.8 TabSwitch.vue / Empty.vue

> **注：** 这两个组件在当前版本中未被使用

---

## 六、核心 Composables

### 6.1 useDetection.ts

**功能：** 封装所有后端 API 调用

**导出的函数：**

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| getModels | - | Promise\<Model[]\> | 获取模型列表 |
| detectImage | (file, model, conf, iou) | Promise\<DetectionResponse\> | 图片文件检测 |
| detectBase64 | (imageData, model, conf, iou) | Promise\<DetectionResponse\> | Base64 图片检测 |
| detectVideo | (file, model, conf, iou, frameInterval) | Promise\<VideoDetectionResponse\> | 视频检测 |
| downloadImage | (dataUrl, filename) | void | 下载标注图片 |
| getDownloadUrl | (path) | string | 获取完整下载 URL |

**API 基础地址：** `http://localhost:5000/api`

---

### 6.2 useTheme.ts

> **注：** 此 composable 在当前版本中未被使用

**功能：** 主题切换（light/dark）

---

## 七、工具函数

### 7.1 classNames.ts

**功能：** 类别中文名和颜色映射

**支持的类别：**

#### 垃圾分类（5类）

| 英文 | 中文 | 颜色 |
|------|------|------|
| cardboard | 纸板 | #f59e0b (琥珀色) |
| glass | 玻璃 | #06b6d4 (青色) |
| metal | 金属 | #64748b (灰色) |
| paper | 纸张 | #3b82f6 (蓝色) |
| plastic | 塑料 | #ef4444 (红色) |

#### COCO 数据集（80类）

包含人、车辆、动物、日常物品等 80 个类别的中文名称和颜色映射。

**导出函数：**
```typescript
getClassNameCN(cls: string): string   // 获取类别中文名
getClassColor(cls: string): string    // 获取类别颜色
```

---

### 7.2 utils.ts

**功能：** Tailwind class 合并工具

```typescript
cn(...inputs: ClassValue[]): string
```

使用 `clsx` + `tailwind-merge` 实现 class 的智能合并。

---

## 八、UI 设计

### 8.1 主题风格

采用 **B站（Bilibili）深色主题**，主要配色：

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 背景色 | #18191c | 深灰黑色 |
| 卡片背景 | #23252b | 稍亮的深灰色 |
| 悬停背景 | #2a2d36 | 交互高亮 |
| 边框色 | #333640 | 分隔线 |
| 主题色 | #fb7299 | B站粉色 |
| 主文字 | #ffffff | 白色 |
| 次要文字 | #9499a0 | 灰色 |
| 辅助文字 | #61666d | 深灰色 |

### 8.2 布局结构

```
┌─────────────────────────────────────────────────────────┐
│  Header (顶部导航栏)                                      │
│  [Logo] [垃圾分类智能检测] [摄像头|图片|视频] [GPU信息]    │
├──────────────────────────────────────┬──────────────────┤
│                                      │  右侧边栏         │
│                                      │  ┌──────────────┐ │
│                                      │  │ 列表 | 参数   │ │
│                                      │  ├──────────────┤ │
│   主预览区                            │  │              │ │
│   (摄像头/图片/视频)                   │  │  内容区域     │ │
│                                      │  │              │ │
│                                      │  └──────────────┘ │
├──────────────────────────────────────┴──────────────────┤
│  底部控制栏 (图片模式)                                    │
│  [上一张] [下一张] [1/5] [检测当前] [批量检测] [下载]    │
└─────────────────────────────────────────────────────────┘
```

---

## 九、检测流程

### 9.1 图片检测流程

```
1. 用户上传图片/文件夹 → ImageList 组件
2. 创建 ImageItem 对象，生成预览 URL
3. 用户点击"检测当前"或"批量检测"
4. 调用 useDetection.detectImage() → POST /api/detect
5. 后端加载模型（带缓存）→ YOLO 推理
6. 返回检测结果 + 标注图片（base64）
7. 前端更新 ImageItem 状态，显示标注图片
8. 用户可下载标注结果
```

### 9.2 摄像头检测流程

```
1. 用户切换到"摄像头检测"模式
2. 点击"启动摄像头" → getUserMedia
3. 视频流显示在 video 元素上
4. 每 400ms 执行一次检测循环：
   a. 抓取当前帧 → Canvas → base64
   b. 调用 useDetection.detectBase64() → POST /api/detect_base64
   c. 后端 YOLO 推理 → 返回检测结果
   d. 前端防抖处理（IoU 匹配，2帧历史）
   e. Canvas 覆盖层绘制检测框
5. 点击"停止检测" → 关闭摄像头，清理资源
```

### 9.3 视频检测流程

#### 完整检测（后端处理）

```
1. 用户上传视频文件
2. 点击"完整检测" → useDetection.detectVideo() → POST /api/detect_video
3. 后端逐帧处理（按 frame_interval 间隔）
4. 生成标注视频，保存到 uploads/ 目录
5. 返回 video_url 和统计信息
6. 前端显示标注视频，用户可下载
```

#### 实时预览（前端处理）

```
1. 视频播放时，每 300ms 抓取一帧
2. 调用 detectBase64() 进行实时检测
3. Canvas 覆盖层绘制检测框
4. 如果有标注视频，自动停止实时检测
```

---

## 十、模型配置

### 10.1 可用模型

| 模型 ID | 名称 | 大小 | 类型 | 特点 |
|---------|------|------|------|------|
| yolov5n | YOLOv5 Nano | 5.3 MB | 垃圾分类 | 最快，轻量 |
| yolov5s | YOLOv5 Small | 17.7 MB | 垃圾分类 | 推荐，平衡 |
| yolov5m | YOLOv5 Medium | 48.2 MB | 垃圾分类 | 最准，稍慢 |
| yolov5s-coco | YOLOv5 COCO | 22.5 MB | COCO | 基准对比 |

### 10.2 模型路径配置

模型路径在 `backend/app.py` 的 `MODEL_CONFIGS` 中配置：

```python
MODEL_CONFIGS = {
    'yolov5n': {
        'path': r'../../runs/detect/runs/train/exp3_yolov5n_bs32/weights/best.pt',
        'type': 'garbage',
    },
    # ... 其他模型
}
```

### 10.3 模型缓存机制

后端使用 `models_cache` 字典缓存已加载的模型，避免重复加载：

```python
def get_model(model_id: str):
    if model_id not in models_cache:
        models_cache[model_id] = YOLO(config['path'])
    return models_cache[model_id]
```

---

## 十一、启动方式

### 11.1 后端启动

```bash
cd backend
python app.py
```

服务将在 `http://localhost:5000` 启动，自动预加载默认模型 `yolov5s`。

### 11.2 前端启动

```bash
cd frontend
npm install    # 首次运行需要
npm run dev
```

开发服务器默认在 `http://localhost:5173`。

---

## 十二、注意事项

1. **后端地址硬编码：** 前端 API 基础地址写死为 `http://localhost:5000/api`，不依赖代理
2. **模型路径：** 模型路径使用相对路径 `../../runs/...`，需确保路径正确
3. **GPU 支持：** 后端自动检测 CUDA，有 GPU 时使用 GPU 推理
4. **摄像头权限：** 需要浏览器授予摄像头访问权限
5. **跨域问题：** 后端使用 Flask-CORS 允许所有跨域请求
6. **文件清理：** 视频检测的临时文件会在处理完成后自动删除

---

## 十三、数据接口类型定义

```typescript
// 检测结果
interface Detection {
  class: string           // 类别名称（英文）
  confidence: number      // 置信度 (0-1)
  bbox: [number, number, number, number]  // [x1, y1, x2, y2]
}

// 图片检测响应
interface DetectionResponse {
  success: boolean
  detections: Detection[]
  annotated_image: string  // base64 编码
  counts: Record<string, number>
}

// 模型信息
interface Model {
  id: string
  name: string
  size: string
}

// 视频检测响应
interface VideoDetectionResponse {
  success: boolean
  video_url: string
  total_frames: number
  processed_frames: number
  fps: number
  duration: number
  counts: Record<string, number>
  total_detected: number
  frame_results: Array<{
    frame: number
    time: number
    detections: Detection[]
  }>
}
```

---

## 十四、版本信息

- **文档生成日期：** 2026-06-28
- **前端框架：** Vue 3.4.15 + TypeScript 5.3.3
- **后端框架：** Flask + Ultralytics YOLO
- **UI 主题：** Bilibili 深色风格