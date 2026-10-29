// 垃圾分类类别中文名称
export const garbageClassNamesCN: Record<string, string> = {
  cardboard: '纸板',
  glass: '玻璃',
  metal: '金属',
  paper: '纸张',
  plastic: '塑料',
}

// 垃圾分类类别颜色
export const garbageClassColors: Record<string, string> = {
  cardboard: '#f59e0b',
  glass: '#06b6d4',
  metal: '#64748b',
  paper: '#3b82f6',
  plastic: '#ef4444',
}

// COCO 80类中文名称
export const cocoClassNamesCN: Record<string, string> = {
  person: '人', bicycle: '自行车', car: '汽车', motorcycle: '摩托车',
  airplane: '飞机', bus: '公交车', train: '火车', truck: '卡车', boat: '船',
  'traffic light': '红绿灯', 'fire hydrant': '消防栓', 'stop sign': '停车标志',
  'parking meter': '停车计时器', bench: '长椅', bird: '鸟', cat: '猫', dog: '狗',
  horse: '马', sheep: '羊', cow: '牛', elephant: '大象', bear: '熊',
  zebra: '斑马', giraffe: '长颈鹿', backpack: '背包', umbrella: '雨伞',
  handbag: '手提包', tie: '领带', suitcase: '行李箱', frisbee: '飞盘',
  skis: '滑雪板', snowboard: '单板滑雪', 'sports ball': '球', kite: '风筝',
  'baseball bat': '棒球棒', 'baseball glove': '棒球手套', skateboard: '滑板',
  surfboard: '冲浪板', 'tennis racket': '网球拍', bottle: '瓶子',
  'wine glass': '酒杯', cup: '杯子', fork: '叉子', knife: '刀', spoon: '勺子',
  bowl: '碗', banana: '香蕉', apple: '苹果', sandwich: '三明治',
  orange: '橙子', broccoli: '西兰花', carrot: '胡萝卜', 'hot dog': '热狗',
  pizza: '披萨', donut: '甜甜圈', cake: '蛋糕', chair: '椅子', couch: '沙发',
  'potted plant': '盆栽', bed: '床', 'dining table': '餐桌', toilet: '厕所',
  tv: '电视', laptop: '笔记本电脑', mouse: '鼠标', remote: '遥控器',
  keyboard: '键盘', 'cell phone': '手机', microwave: '微波炉', oven: '烤箱',
  toaster: '烤面包机', sink: '水槽', refrigerator: '冰箱', book: '书',
  clock: '时钟', vase: '花瓶', scissors: '剪刀', 'teddy bear': '泰迪熊',
  'hair drier': '吹风机', toothbrush: '牙刷',
}

// COCO 类别颜色（按分组）
const cocoColors = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
  '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
  '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
  '#ec4899', '#f43f5e', '#64748b', '#78716c', '#a8a29e',
]

export const cocoClassColors: Record<string, string> = {}
const cocoClassList = Object.keys(cocoClassNamesCN)
cocoClassList.forEach((name, i) => {
  cocoClassColors[name] = cocoColors[i % cocoColors.length]
})

// 获取类别中文名称
export function getClassNameCN(cls: string): string {
  return garbageClassNamesCN[cls] || cocoClassNamesCN[cls] || cls
}

// 获取类别颜色
export function getClassColor(cls: string): string {
  return garbageClassColors[cls] || cocoClassColors[cls] || '#6b7280'
}
