"""
三组实验结果对比脚本
对比 YOLOv5n / YOLOv5s / YOLOv5m 三个模型的性能
"""

import os
import torch
from ultralytics import YOLO
import yaml

os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'


def evaluate_model(model_path, data_yaml, device, batch_size):
    model = YOLO(model_path)
    results = model.val(
        data=data_yaml,
        device=device,
        imgsz=640,
        batch=batch_size,
        verbose=False,
    )

    model_size_mb = os.path.getsize(model_path) / 1024 / 1024

    metrics = {
        'mAP50': results.box.map50,
        'mAP50_95': results.box.map,
        'precision': results.box.mp,
        'recall': results.box.mr,
        'model_size_mb': model_size_mb,
    }
    return metrics


def main():
    device = 0 if torch.cuda.is_available() else 'cpu'
    data_yaml = 'yolo_dataset/yolo_dataset/data.yaml'

    experiments = [
        {
            'name': 'YOLOv5n',
            'exp_name': 'exp3_yolov5n_bs32',
            'model_path': 'runs/train/exp3_yolov5n_bs32/weights/best.pt',
            'batch_size': 32,
        },
        {
            'name': 'YOLOv5s',
            'exp_name': 'exp1_yolov5s_bs16',
            'model_path': 'runs/train/exp1_yolov5s_bs16-2/weights/best.pt',
            'batch_size': 16,
        },
        {
            'name': 'YOLOv5m',
            'exp_name': 'exp2_yolov5m_bs8',
            'model_path': 'runs/train/exp2_yolov5m_bs8/weights/best.pt',
            'batch_size': 8,
        },
    ]

    all_results = []

    print(f'\n{"="*80}')
    print('三组实验结果对比 (YOLOv5n vs YOLOv5s vs YOLOv5m)')
    print(f'{"="*80}\n')

    for exp in experiments:
        if not os.path.exists(exp['model_path']):
            print(f"[跳过] {exp['name']}: 模型文件不存在 {exp['model_path']}")
            continue

        print(f"评估 {exp['name']}...", end=' ')
        metrics = evaluate_model(exp['model_path'], data_yaml, device, exp['batch_size'])
        metrics['name'] = exp['name']
        all_results.append(metrics)
        print(f"完成 (mAP@0.5={metrics['mAP50']:.4f})")

    if not all_results:
        print('\n没有可对比的实验结果')
        return

    print(f'\n{"="*80}')
    print('对比结果汇总表')
    print(f'{"="*80}')
    print(f'{"模型":<12} {"mAP@0.5":<10} {"mAP@.5:.95":<12} {"Precision":<12} {"Recall":<10} {"模型大小":<12}')
    print('-' * 80)

    for r in all_results:
        print(f"{r['name']:<12} {r['mAP50']:<10.4f} {r['mAP50_95']:<12.4f} {r['precision']:<12.4f} {r['recall']:<10.4f} {r['model_size_mb']:<10.2f}MB")

    print(f'\n{"="*80}')

    with open('comparison_results.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(all_results, f, allow_unicode=True, default_flow_style=False)
    print('对比结果已保存到: comparison_results.yaml')


if __name__ == '__main__':
    main()
