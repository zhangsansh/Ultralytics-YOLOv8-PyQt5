# 行人识别可视化大屏

基于 **Ultralytics YOLOv8（开源）** 与 **PyQt5** 的行人检测、分割、二次识别与数据分析桌面应用。

支持图片/视频上传、整图检测标注、行人分割与二次识别、准确率展示、**ECharts 多风格图表组合**、按日期归档存储、SQLite 持久化，以及主题/字体外观配置。

---

## 一、功能概览

| 页面 | 功能说明 |
|------|----------|
| ① 行人识别 | 上传图片/视频；整图检测；分割每个人；对分割图二次 YOLO 识别并展示准确率 |
| ② 日志记录 | 实时操作日志、SQLite 历史日志、打开当日日志文件与识别图片目录 |
| ③ 图表分析 | 基于 ECharts 的 19 种图表样式，可多选/随机组合；支持调参 |
| ④ 参数配置 | 输出目录、日志/图片子目录、模型路径、检测与预处理默认参数 |
| ⑤ 外观设置 | 主题（深色/浅色/青绿）、字体、字号、按钮边距，即时生效 |
| ⑥ 使用说明 | 程序内嵌操作指南与注意事项 |

### 核心能力

- **行人检测**：仅检测 `person` 类别，输出检测框、置信度（准确率）与人数  
- **行人分割**：按检测框裁剪；若使用分割模型则按掩膜抠图  
- **二次识别**：对每张分割图再次运行 YOLO，展示复核框与二次准确率（对比首次）  
- **中文准确率标注**：使用 Pillow + 系统中文字体，避免文字显示不全  
- **图像交互**：滚轮缩放、左键拖拽、右键/按钮旋转；可返回整图  
- **视频识别**：按抽帧间隔处理并导出带框视频；末帧分割并二次识别  
- **自动归档**：按日期保存整图、分割二次识别图、日志、参数快照；写入 SQLite  
- **ECharts 可视化**：数量、准确率及关系/树图等多种风格，支持左右双图组合  

---

## 二、技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| 目标检测 | [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) | 开源 YOLO；默认 `yolov8n.pt`；可选 `yolov8n-seg.pt` 做掩膜分割 |
| 桌面界面 | PyQt5 | 多标签页大屏、表单、图像查看器、主题样式 |
| Web 图表 | QtWebEngine + ECharts 5 + echarts-stat | 本地 `ui/assets` 加载，离线可用 |
| 图像处理 | OpenCV、NumPy、Pillow | 读写、预处理、绘制；中文标题用 Pillow 渲染 |
| 存储 | SQLite + 本地文件 | 识别记录、检测明细、操作日志；按日目录归档 |
| 配置 | JSON（`app_config.json`） | 路径、检测参数、外观主题与字体 |

### 依赖（`requirements.txt`）

```text
ultralytics>=8.0.0
opencv-python>=4.8.0
PyQt5>=5.15
matplotlib>=3.7
numpy>=1.23
Pillow>=9.0
```

另需已安装 **PyQtWebEngine**（用于 ECharts 页面）。Anaconda 环境通常可直接使用。

---

## 三、项目结构

```
python1/
├── main.py                 # 程序入口
├── config.py               # 全局配置、按日目录
├── app_config.json          # 用户配置（运行后生成/更新）
├── requirements.txt
├── README.md
├── yolov8n.pt              # YOLO 检测权重
├── core/
│   ├── detector.py        # YOLO 加载、图片/视频检测、二次识别
│   ├── segment.py         # 行人裁剪/掩膜分割、中文准确率标注
│   ├── preprocess.py      # 亮度/对比度/去噪/CLAHE/旋转翻转
│   ├── storage.py         # SQLite 与结果文件保存
│   ├── logger.py          # 按日文件日志 + UI 回调
│   └── image_io.py        # 中文路径兼容的图像读写
├── ui/
│   ├── main_window.py     # 主窗口与识别页
│   ├── image_viewer.py    # 缩放/平移/旋转查看器
│   ├── person_gallery.py  # 分割二次识别画廊
│   ├── log_panel.py       # 日志页
│   ├── chart_panel.py     # ECharts 图表页（QWebEngine）
│   ├── echarts_options.py # 19 种 ECharts option 构建
│   ├── param_panel.py     # 参数配置页
│   ├── theme.py / theme_panel.py
│   ├── help_panel.py
│   └── assets/            # echarts.min.js、ecStat.min.js
└── outputs/               # 默认输出根目录
    ├── db/pedestrian.db
    └── YYYY-MM-DD/
        ├── images/
        ├── logs/
        └── params/
```

---

## 四、环境安装与启动

### 环境建议

- Windows 10 / 11  
- Python 3.10+（推荐 Anaconda）  

### 安装依赖

```bash
pip install -r requirements.txt
# 若图表页空白，请确认已安装：
pip install PyQtWebEngine
```

本机 Anaconda 示例：

```bash
E:\Anconda3\python.exe -m pip install -r requirements.txt
```

首次运行若本地无权重，Ultralytics 可能自动下载官方开源权重（需网络）。

### 启动程序

```bash
python main.py
```

或：

```bash
E:\Anconda3\python.exe main.py
```

---

## 五、推荐操作流程

```
外观设置（调大字号）
    ↓
参数配置（确认输出目录、模型路径）
    ↓
行人识别：上传 → 调整参数 → 开始识别
    ↓
查看主图标注 + 下方分割二次识别卡片
    ↓
图表分析：多选/随机组合 ECharts 样式
    ↓
日志记录：核对操作与归档路径
```

---

## 六、各页面使用说明

### 1. 行人识别页

**操作步骤**

1. 点击 **上传图片/视频**，选择本地文件。  
2. 按需调整右侧参数：`conf`、IoU、输入尺寸、线宽、视频抽帧、亮度/对比度、预处理旋转等。  
3. 点击 **开始识别**。  
4. 识别完成后：  
   - **上方主图**：带检测框的完整结果（可缩放、拖拽、旋转）。  
   - **下方画廊**：每个人物分割图，并显示 **二次识别准确率**（含首次对比）。  
   - 点击某张卡片可在主图放大；点 **返回整图** 恢复完整结果。  
   - **手动保存当前图**：将当前主图再存一份到当日目录。  
5. 视频识别中可点 **取消视频识别**。

**内部处理流程**

1. 整图预处理 → YOLO 检测 `person`  
2. 按框（或掩膜）分割每个人  
3. 对每张分割图再次 YOLO 识别（过小图会先放大）  
4. 绘制二次检测框 + 中文准确率横幅 → 画廊展示并落盘  

**图像操作**

| 操作 | 方式 |
|------|------|
| 缩放 | 鼠标滚轮 |
| 平移 | 左键拖拽 |
| 旋转 90° | 右键，或工具栏左转/右转 |
| 重置视图 | 「重置视图」 |
| 查看单人 | 点击下方分割卡片 |
| 恢复整图 | 「返回整图」 |

### 2. 日志记录页

- 上方：实时操作日志  
- 下方：SQLite 历史日志表（深色样式）  
- 可刷新数据库日志、打开今日日志文件、打开今日识别图片目录  

### 3. 图表分析页（ECharts）

- 左侧：检测参数（可保存）+ 图表样式列表  
- **Ctrl 多选**：选中的前两个样式左右对照显示  
- **随机组合**：随机挑选两种样式组合  
- 数据来源：历史识别次数、行人数、准确率等（SQLite）  

**已支持的 ECharts 样式（19 种）**

1. 渐变堆叠面积图  
2. 带背景色的柱状图  
3. 柱状图标签旋转  
4. 嵌套环形图  
5. 饼图纹理  
6. 数据聚合  
7. 聚合过程可视化  
8. 线性回归（统计插件 ecStat）  
9. 单轴散点图  
10. AQI-雷达图  
11. 数据聚合盒须图  
12. 热力图-大数据  
13. 日历热力图  
14. 笛卡尔坐标系 Graph  
15. 关系图自动隐藏重叠标签  
16. 依赖关系图  
17. 多棵树  
18. 径向树状图  
19. 矩形树图与旭日图过渡（工具栏切换动画）  

### 4. 参数配置页

- 输出根目录、日志/图片/参数子目录名  
- SQLite 路径、YOLO 模型路径  
- 默认检测与预处理参数  
- 保存后写入 `app_config.json`  

### 5. 外观设置页

- 主题：**深色科技** / **浅色清晰** / **青绿护眼**  
- 字体、正文字号（默认约 18）、标题字号、按钮内边距  
- **应用并保存** 后立即刷新全局样式（适合大屏再调到 20–22）  

### 6. 使用说明页

程序内嵌帮助文档，可与本 README 对照阅读。

---

## 七、关于「准确率」

界面中的准确率来自 YOLO 输出的 **置信度（confidence）**，表示模型认为该目标是行人的把握程度（0%～100%）。

- 便于比较不同检测结果的可信程度，**不是**人工标注意义上的绝对正确率。  
- 整图识别有「整图平均准确率」；分割卡片展示「二次识别准确率」并对比「首次」。  
- 可通过调高 `conf` 过滤低置信度框；调低则更容易检出更多目标（也可能增加误检）。  

---

## 八、数据存储说明

### 按日期归档

默认根目录：`outputs/`

```
outputs/YYYY-MM-DD/
├── images/     # 整图 *_det_*.jpg、二次识别分割图 *_personN_re_*.jpg、视频、预览等
├── logs/       # app_YYYY-MM-DD.log
└── params/     # params_HHMMSS.json 参数快照
```

### SQLite（`outputs/db/pedestrian.db`）

| 表 | 内容 |
|------|------|
| `detection_runs` | 每次识别摘要（人数、置信度、耗时、参数、结果路径等） |
| `detections` | 每个检测框明细 |
| `operation_logs` | 操作日志 |

路径可在「参数配置」页修改。

---

## 九、常见问题

**检测不到人或人数偏少**  
降低 `conf`、增大 `imgsz`，检查预处理旋转是否正确，确认画面中有清晰行人。

**分割图上中文准确率显示不全 / 乱码**  
当前版本已用 Pillow + 微软雅黑绘制，并自动加宽标题栏。请确认系统存在 `C:\Windows\Fonts\msyh.ttc` 等字体。

**图表页空白**  
确认已安装 `PyQtWebEngine`，且 `ui/assets/echarts.min.js`、`ecStat.min.js` 存在。

**首次启动较慢**  
首次加载 YOLO 权重与依赖初始化会稍慢，之后会明显加快。

**中文路径图片**  
程序通过 OpenCV `imdecode`/`imencode` 兼容中文路径。

**字太小**  
到「外观设置」增大正文字号，或切换「浅色清晰」主题。

**想用掩膜抠图**  
将 `yolov8n-seg.pt` 放到项目根目录，或在参数配置中指定分割模型路径；无分割模型时按检测框裁剪。

---

## 十、许可证与致谢

- 本项目界面与业务代码可按自身需求使用与修改。  
- 检测能力基于 [Ultralytics](https://github.com/ultralytics/ultralytics) 开源 YOLO，请遵循其开源协议（以官方仓库为准）。  
- 界面：PyQt5 / QtWebEngine；图表：Apache ECharts；图像：OpenCV、Pillow。  

---

## 十一、快速命令摘要

```bash
# 安装依赖
pip install -r requirements.txt
pip install PyQtWebEngine

# 启动程序
python main.py
```

如有问题，可查看当日日志：

`outputs/YYYY-MM-DD/logs/app_YYYY-MM-DD.log`

或在程序「② 日志记录」页直接打开。
