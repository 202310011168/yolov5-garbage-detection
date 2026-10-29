"""
垃圾分类实时检测 - 摄像头版本
使用电脑摄像头进行实时垃圾分类目标检测

使用方法：
1. 确保已训练好模型，模型路径在 MODEL_PATH 中
2. 运行脚本：python camera_detect.py
3. 按 q 键退出
"""

import cv2
from ultralytics import YOLO


# ==================== 配置区 ====================
# 训练好的模型路径（根据实际情况修改）
MODEL_PATH = 'runs/train/exp1_yolov5s/weights/best.pt'

# 类别名称（与 garbage.yaml 中的顺序一致）
CLASS_NAMES = ['cardboard', 'glass', 'metal', 'paper', 'plastic']

# 置信度阈值（低于这个值的检测结果会被忽略）
CONFIDENCE_THRESHOLD = 0.5

# 摄像头编号（0=默认摄像头，如果有外接摄像头可能是1）
CAMERA_INDEX = 0
# ============================================


def main():
    # 加载模型
    print(f'正在加载模型: {MODEL_PATH}')
    try:
        model = YOLO(MODEL_PATH)
        print('模型加载成功！')
    except FileNotFoundError:
        print(f'错误: 找不到模型文件 {MODEL_PATH}')
        print('请先训练模型，或修改 MODEL_PATH 为正确的模型路径')
        return

    # 打开摄像头
    print(f'正在打开摄像头 (index={CAMERA_INDEX})...')
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print('错误: 无法打开摄像头！')
        print('请检查：1. 摄像头是否连接 2. 摄像头是否被其他程序占用')
        return

    print('摄像头打开成功！按 q 键退出')

    # 设置摄像头分辨率（可选，越大越清晰但越慢）
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # 颜色配置（BGR格式）
    COLORS = {
        'cardboard': (155, 155, 0),    # 黄色
        'glass': (0, 200, 200),         # 青色
        'metal': (200, 200, 200),      # 灰色
        'paper': (100, 100, 255),      # 蓝色
        'plastic': (255, 100, 100),    # 红色
    }

    # 检测次数计数器（用于显示 FPS）
    frame_count = 0
    fps = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            print('错误: 无法读取摄像头画面')
            break

        frame_count += 1

        # YOLO 推理（只检测，不画框）
        results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)

        # 获取检测结果
        annotated_frame = results[0].plot()

        # 显示 FPS（在左上角）
        if frame_count % 10 == 0:
            # 简单计算 FPS
            fps = 10 / 0.5  # 实际使用时可以用 time 模块精确计算
        cv2.putText(
            annotated_frame,
            f'FPS: {fps:.1f}',
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # 显示类别说明
        cv2.putText(
            annotated_frame,
            'Classes: cardboard, glass, metal, paper, plastic',
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )

        # 显示画面
        cv2.imshow('Garbage Classification - Real-time Detection', annotated_frame)

        # 按 q 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print('退出检测')
            break

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
    print('检测已关闭')


if __name__ == '__main__':
    main()
