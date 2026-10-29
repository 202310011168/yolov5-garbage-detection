import os
import torch
from ultralytics import YOLO
import yaml

os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'


def train_experiment(model_name='yolov5s', epochs=100, batch_size=16, exp_name='exp'):
    if torch.cuda.is_available():
        device = 0
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f'\n{"="*50}')
        print(f'开始实验: {exp_name}')
        print(f'模型: {model_name}, epochs: {epochs}, batch_size: {batch_size}')
        print(f'设备: GPU ({gpu_name}, {gpu_mem:.1f}GB)')
        print(f'{"="*50}\n')
    else:
        device = 'cpu'
        print(f'\n{"="*50}')
        print(f'开始实验: {exp_name}')
        print(f'模型: {model_name}, epochs: {epochs}, batch_size: {batch_size}')
        print(f'设备: CPU')
        print(f'{"="*50}\n')

    best_pt = os.path.join('runs', 'train', exp_name, 'weights', 'best.pt')

    if os.path.exists(best_pt):
        print(f'实验 {exp_name} 已完成，跳过训练，直接加载结果')
        model = YOLO(best_pt)
        results = model.val(
            data='yolo_dataset/yolo_dataset/data.yaml',
            device=device,
            imgsz=640,
            batch=batch_size,
        )
        best_path = best_pt
    else:
        model = YOLO(f'{model_name}.pt')
        results = model.train(
            data='yolo_dataset/yolo_dataset/data.yaml',
            epochs=epochs,
            imgsz=640,
            batch=batch_size,
            device=device,
            project='runs/train',
            name=exp_name,
            patience=20,
            save=True,
            plots=True,
            val=True,
            workers=2,
            optimizer='SGD',
            lr0=0.01,
            lrf=0.01,
            momentum=0.937,
            weight_decay=0.0005,
            warmup_epochs=3.0,
            warmup_momentum=0.8,
            warmup_bias_lr=0.1,
            cos_lr=True,
            close_mosaic=10,
            amp=True,
            seed=42,
        )
        best_path = os.path.join(results.save_dir, 'weights', 'best.pt')

    metrics = {
        'exp_name': exp_name,
        'model': model_name,
        'epochs': epochs,
        'batch_size': batch_size,
        'mAP50': results.box.map50,
        'mAP50_95': results.box.map,
        'precision': results.box.mp,
        'recall': results.box.mr,
        'best_weights': best_path,
    }

    print(f'\n实验 {exp_name} 完成:')
    print(f'  mAP@0.5: {metrics["mAP50"]:.4f}')
    print(f'  mAP@0.5:0.95: {metrics["mAP50_95"]:.4f}')
    print(f'  Precision: {metrics["precision"]:.4f}')
    print(f'  Recall: {metrics["recall"]:.4f}')

    return metrics


def compare_experiments():
    experiments = [
        {
            'model_name': 'yolov5s',
            'epochs': 100,
            'batch_size': 16,
            'exp_name': 'exp1_yolov5s_bs16',
        },
        {
            'model_name': 'yolov5m',
            'epochs': 100,
            'batch_size': 8,
            'exp_name': 'exp2_yolov5m_bs8',
        },
    ]

    all_results = []
    for exp in experiments:
        metrics = train_experiment(**exp)
        all_results.append(metrics)

    print(f'\n\n{"="*60}')
    print('对比实验结果汇总')
    print(f'{"="*60}')
    print(f'{"实验名称":<25} {"mAP@0.5":<10} {"mAP@.5:.95":<12} {"Precision":<10} {"Recall":<10}')
    print('-' * 60)
    for r in all_results:
        print(f'{r["exp_name"]:<25} {r["mAP50"]:<10.4f} {r["mAP50_95"]:<12.4f} {r["precision"]:<10.4f} {r["recall"]:<10.4f}')

    with open('experiment_results.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(all_results, f, allow_unicode=True, default_flow_style=False)

    print(f'\n结果已保存到: experiment_results.yaml')


if __name__ == '__main__':
    compare_experiments()
