# -*- coding: utf-8 -*-
"""程序使用说明页面。"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QScrollArea, QTextBrowser, QVBoxLayout, QWidget


HELP_HTML = """
<h2 style="margin-bottom:6px;">行人识别可视化大屏 · 使用说明</h2>
<p style="color:#94a3b8;">技术栈：Ultralytics YOLOv8（开源） · PyQt5 · OpenCV · Matplotlib · SQLite</p>

<h3>一、功能概览</h3>
<ol>
  <li><b>行人识别</b>：上传图片/视频，检测行人数量与准确率，主图保留完整标注，下方展示分割出的每个人。</li>
  <li><b>日志记录</b>：查看实时操作日志，并可打开当日日志文件与识别图片目录。</li>
  <li><b>图表分析</b>：按数量、准确率等维度统计历史识别结果，可调整检测参数。</li>
  <li><b>参数配置</b>：设置输出目录、模型路径、日志/图片子目录及默认检测参数。</li>
  <li><b>外观设置</b>：调整字体大小、字体族与主题配色。</li>
  <li><b>使用说明</b>：本页，介绍实际使用方式与注意事项。</li>
</ol>

<h3>二、行人识别页面怎么用</h3>
<ol>
  <li>点击「上传图片/视频」，选择本地文件。</li>
  <li>按需调整右侧置信度阈值、IoU、亮度、旋转等参数。</li>
  <li>点击「开始识别」。识别完成后：
    <ul>
      <li>上方主图：带检测框的完整结果图（可滚轮缩放、左键拖拽、右键旋转）。</li>
      <li>下方画廊：每个人被分割出来，并显示<strong>准确率（%）</strong>。</li>
      <li>右侧统计：人数、平均/最高/最低置信度、耗时与保存路径。</li>
    </ul>
  </li>
  <li>点击某个分割卡片可在主图放大查看；点「返回整图」恢复完整结果。</li>
  <li>「手动保存当前图」可将当前主图再存一份到当日目录。</li>
</ol>

<h3>三、数据自动保存规则</h3>
<ul>
  <li>按日期归档：<code>outputs/YYYY-MM-DD/images|logs|params</code></li>
  <li>SQLite：<code>outputs/db/pedestrian.db</code> 保存识别记录与操作日志</li>
  <li>每次识别会保存：整图结果、每个人的分割图、参数快照 JSON</li>
</ul>

<h3>四、关于「准确率」</h3>
<p>
此处准确率来自模型输出的<strong>置信度（confidence）</strong>，表示模型认为该框是行人的把握程度，
范围 0%~100%。它不是人工标注意义上的绝对正确率，但可用于比较不同检测结果的可信程度。
可在图表页/参数页调整 <b>conf</b> 阈值，过滤低置信度结果。
</p>

<h3>五、视频识别说明</h3>
<ul>
  <li>视频按「抽帧间隔」逐帧（或隔帧）检测并导出带框视频。</li>
  <li>分割画廊展示的是<strong>最后处理帧</strong>中的行人。</li>
  <li>处理中可点「取消视频识别」中止。</li>
</ul>

<h3>六、常见问题</h3>
<ul>
  <li><b>检测不到人</b>：降低 conf、增大 imgsz，或检查图片是否含清晰行人；预处理旋转是否正确。</li>
  <li><b>首次加载慢</b>：首次加载 YOLO 权重会稍慢，之后会快很多。</li>
  <li><b>中文路径图片</b>：本程序已兼容中文路径读写。</li>
  <li><b>字体/看不清</b>：到「外观设置」增大字号或切换浅色主题。</li>
</ul>

<h3>七、推荐操作流程</h3>
<p>外观设置调大字体 → 参数配置确认输出目录 → 行人识别上传并检测 → 图表页查看数量/准确率统计 → 日志页核对操作记录。</p>
"""


class HelpPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        tip = QLabel("程序使用与实际情况说明（可滚动阅读）")
        tip.setStyleSheet("color:#94a3b8;")
        layout.addWidget(tip)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(HELP_HTML)
        browser.setStyleSheet(
            "QTextBrowser { background:#0f172a; color:#e2e8f0; padding:12px; border:1px solid #334155; }"
        )
        layout.addWidget(browser)
