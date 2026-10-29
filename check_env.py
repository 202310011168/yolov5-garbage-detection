import sys
import os

os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'


def check_environment():
    print('=' * 60)
    print('环境检测报告')
    print('=' * 60)

    print('\n1. Python 版本')
    print(f'   {sys.version}')

    print('\n2. PyTorch 版本')
    try:
        import torch
        print(f'   PyTorch: {torch.__version__}')
        print(f'   CUDA 可用: {torch.cuda.is_available()}')
        if torch.cuda.is_available():
            print(f'   CUDA 版本: {torch.version.cuda}')
            print(f'   cuDNN 版本: {torch.backends.cudnn.version()}')
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                print(f'   GPU {i}: {props.name} ({props.total_memory / 1024**3:.1f}GB)')
        else:
            print('   警告: CUDA 不可用，将使用 CPU 训练（速度很慢）')
            print('   请安装 CUDA 版 PyTorch: conda install pytorch pytorch-cuda=11.8 -c pytorch -c nvidia')
    except ImportError as e:
        print(f'   错误: PyTorch 未安装 - {e}')
        return False

    print('\n3. Ultralytics (YOLO) 版本')
    try:
        import ultralytics
        print(f'   Ultralytics: {ultralytics.__version__}')
    except ImportError as e:
        print(f'   错误: Ultralytics 未安装 - {e}')
        print('   安装命令: pip install ultralytics')
        return False

    print('\n4. 数据集配置')
    yaml_path = 'yolo_dataset/yolo_dataset/data.yaml'
    if os.path.exists(yaml_path):
        print(f'   配置文件: {yaml_path} (存在)')
        import yaml
        with open(yaml_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        print(f'   类别数: {cfg.get("nc", "未知")}')
        print(f'   类别名: {cfg.get("names", "未知")}')
        dataset_path = os.path.dirname(yaml_path)
        if os.path.exists(dataset_path):
            print(f'   数据集目录: {dataset_path} (存在)')
            for split in ['train', 'val', 'test']:
                img_dir = os.path.join(dataset_path, 'images', split)
                lbl_dir = os.path.join(dataset_path, 'labels', split)
                n_img = len(os.listdir(img_dir)) if os.path.exists(img_dir) else 0
                n_lbl = len(os.listdir(lbl_dir)) if os.path.exists(lbl_dir) else 0
                print(f'     {split}: {n_img} 张图片, {n_lbl} 个标注')
        else:
            print(f'   数据集目录: 不存在 (请先准备数据)')
    else:
        print(f'   配置文件: {yaml_path} (不存在)')

    print('\n5. 建议配置 (RTX 4060 Laptop 8GB)')
    print('   - 模型: yolov5s (推荐), yolov5m (显存够的话)')
    print('   - batch_size: 16 (yolov5s), 8 (yolov5m)')
    print('   - imgsz: 640')
    print('   - workers: 2 (Windows 下不要设太高)')
    print('   - amp: True (混合精度训练，省显存)')

    print('\n' + '=' * 60)
    print('检测完成！')
    print('=' * 60)

    return torch.cuda.is_available()


if __name__ == '__main__':
    ok = check_environment()
    sys.exit(0 if ok else 1)
