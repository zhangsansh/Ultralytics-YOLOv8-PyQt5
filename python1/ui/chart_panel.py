# -*- coding: utf-8 -*-
"""ECharts 图表分析页：多种官方风格图表可随意组合。"""

from __future__ import annotations

import json
import random
from pathlib import Path

from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
)

from config import detection_params, load_config, save_config
from core.logger import app_logger
from core.storage import storage
from ui.echarts_options import CHART_TYPES, build_option
from ui.theme import theme_colors


ASSETS = Path(__file__).resolve().parent / "assets"


def _html_shell(bg: str) -> str:
    echarts = (ASSETS / "echarts.min.js").as_uri()
    ecstat = (ASSETS / "ecStat.min.js").as_uri()
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  html,body {{ margin:0; height:100%; background:{bg}; overflow:hidden; }}
  #wrap {{ display:flex; height:100%; gap:8px; padding:8px; box-sizing:border-box; }}
  .pane {{ flex:1; min-width:0; height:100%; border:1px solid #334155; border-radius:8px; }}
</style>
<script src="{echarts}"></script>
<script src="{ecstat}"></script>
</head>
<body>
<div id="wrap">
  <div id="c1" class="pane"></div>
  <div id="c2" class="pane" style="display:none;"></div>
</div>
<script>
  if (window.ecStat && echarts) {{
    echarts.registerTransform(ecStat.transform.regression);
  }}
  var chart1 = echarts.init(document.getElementById('c1'), null, {{renderer:'canvas'}});
  var chart2 = echarts.init(document.getElementById('c2'), null, {{renderer:'canvas'}});
  var treeData = null;

  function applySpecial(chart, option) {{
    if (option && option._treemap_sunburst) {{
      treeData = option._tree_data;
      option.toolbox = option.toolbox || {{}};
      option.toolbox.feature = option.toolbox.feature || {{}};
      option.toolbox.feature.myTreemap = {{
        show: true, title: '矩形树图',
        icon: 'path://M2,2h20v20h-20z',
        onclick: function() {{
          chart.setOption({{
            series: [{{
              id: 'viz', type: 'treemap', animationDurationUpdate: 1000,
              data: treeData, roam: false, nodeClick: false,
              label: {{color:'#0f172a', fontSize:13}},
              breadcrumb: {{itemStyle:{{color:'#1e293b'}}, textStyle:{{color:'#e2e8f0'}}}}
            }}]
          }});
        }}
      }};
      option.toolbox.feature.mySunburst = {{
        show: true, title: '旭日图',
        icon: 'path://M12,2 A10,10 0 1,1 11.9,2 Z',
        onclick: function() {{
          chart.setOption({{
            series: [{{
              id: 'viz', type: 'sunburst', animationDurationUpdate: 1000,
              data: treeData, radius: [0, '90%'],
              label: {{color:'#e2e8f0', fontSize:12}},
              itemStyle: {{borderWidth: 1, borderColor: '#0f172a'}}
            }}]
          }});
        }}
      }};
    }}
    // 清理内部标记字段
    if (option) {{
      delete option._use_ecstat;
      delete option._treemap_sunburst;
      delete option._tree_data;
    }}
    return option;
  }}

  function setCharts(payload) {{
    var dual = !!payload.dual;
    var o1 = applySpecial(chart1, payload.option1 || {{}});
    document.getElementById('c2').style.display = dual ? 'block' : 'none';
    chart1.clear();
    chart1.setOption(o1, true);
    if (dual) {{
      var o2 = applySpecial(chart2, payload.option2 || {{}});
      chart2.clear();
      chart2.setOption(o2, true);
    }}
    chart1.resize();
    chart2.resize();
  }}

  window.addEventListener('resize', function() {{
    chart1.resize(); chart2.resize();
  }});
</script>
</body>
</html>
"""


class ChartPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._ready = False
        self._build()

    def _build(self) -> None:
        root = QHBoxLayout(self)
        splitter = QSplitter()
        root.addWidget(splitter)

        left = QWidget()
        left_layout = QVBoxLayout(left)

        box = QGroupBox("分析参数")
        form = QFormLayout(box)
        cfg = load_config()
        self.spin_conf = QDoubleSpinBox()
        self.spin_conf.setRange(0.05, 0.99)
        self.spin_conf.setSingleStep(0.05)
        self.spin_conf.setValue(float(cfg.get("conf", 0.25)))
        self.spin_iou = QDoubleSpinBox()
        self.spin_iou.setRange(0.1, 0.95)
        self.spin_iou.setSingleStep(0.05)
        self.spin_iou.setValue(float(cfg.get("iou", 0.45)))
        self.spin_imgsz = QSpinBox()
        self.spin_imgsz.setRange(320, 1280)
        self.spin_imgsz.setSingleStep(32)
        self.spin_imgsz.setValue(int(cfg.get("imgsz", 640)))
        self.spin_maxdet = QSpinBox()
        self.spin_maxdet.setRange(1, 1000)
        self.spin_maxdet.setValue(int(cfg.get("max_det", 300)))
        form.addRow("置信度阈值", self.spin_conf)
        form.addRow("NMS IoU", self.spin_iou)
        form.addRow("输入尺寸", self.spin_imgsz)
        form.addRow("最大检测数", self.spin_maxdet)
        left_layout.addWidget(box)

        chart_box = QGroupBox("ECharts 样式（可多选组合）")
        cv = QVBoxLayout(chart_box)
        tip = QLabel("按住 Ctrl 多选；前两个将左右对照显示")
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#94a3b8;")
        cv.addWidget(tip)
        self.list_charts = QListWidget()
        self.list_charts.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for name in CHART_TYPES:
            self.list_charts.addItem(QListWidgetItem(name))
        self.list_charts.item(0).setSelected(True)
        self.list_charts.item(1).setSelected(True)
        cv.addWidget(self.list_charts)

        row = QHBoxLayout()
        self.cmb_quick = QComboBox()
        self.cmb_quick.addItems(["自定义组合", "随机两图组合", "仅单图"])
        self.btn_random = QPushButton("随机组合")
        row.addWidget(self.cmb_quick)
        row.addWidget(self.btn_random)
        cv.addLayout(row)
        left_layout.addWidget(chart_box)

        btns = QHBoxLayout()
        self.btn_apply = QPushButton("保存参数")
        self.btn_refresh = QPushButton("刷新图表")
        btns.addWidget(self.btn_apply)
        btns.addWidget(self.btn_refresh)
        left_layout.addLayout(btns)

        self.summary = QLabel("ECharts 图表页就绪")
        self.summary.setWordWrap(True)
        left_layout.addWidget(self.summary)
        left_layout.addStretch()
        splitter.addWidget(left)

        self.web = QWebEngineView()
        colors = theme_colors()
        self.web.setHtml(_html_shell(colors.get("chart_bg", "#0f172a")), QUrl.fromLocalFile(str(ASSETS) + "/"))
        splitter.addWidget(self.web)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        self.btn_apply.clicked.connect(self.apply_params)
        self.btn_refresh.clicked.connect(self.refresh_charts)
        self.btn_random.clicked.connect(self.random_combo)
        self.list_charts.itemSelectionChanged.connect(self.refresh_charts)
        self.cmb_quick.currentIndexChanged.connect(self._on_quick)
        self.web.loadFinished.connect(self._on_loaded)
        # 延迟刷新，等待页面就绪
        QTimer.singleShot(800, self.refresh_charts)

    def _on_loaded(self, ok: bool) -> None:
        self._ready = bool(ok)
        if ok:
            self.refresh_charts()

    def _on_quick(self, idx: int) -> None:
        if idx == 1:
            self.random_combo()
        elif idx == 2:
            self.list_charts.clearSelection()
            self.list_charts.item(0).setSelected(True)
            self.refresh_charts()

    def random_combo(self) -> None:
        self.list_charts.clearSelection()
        picks = random.sample(range(len(CHART_TYPES)), 2)
        for i in picks:
            self.list_charts.item(i).setSelected(True)
        app_logger.info(f"随机组合图表: {[CHART_TYPES[i] for i in picks]}")
        self.refresh_charts()

    def apply_params(self) -> None:
        cfg = load_config()
        cfg["conf"] = float(self.spin_conf.value())
        cfg["iou"] = float(self.spin_iou.value())
        cfg["imgsz"] = int(self.spin_imgsz.value())
        cfg["max_det"] = int(self.spin_maxdet.value())
        save_config(cfg)
        storage.save_params_snapshot(detection_params(cfg), note="ECharts图表页保存参数")
        app_logger.info("ECharts 图表页参数已保存")
        self.refresh_charts()

    def _selected_names(self) -> list[str]:
        items = self.list_charts.selectedItems()
        names = [i.text() for i in items]
        if not names:
            names = [CHART_TYPES[0]]
        return names[:2]

    def refresh_charts(self) -> None:
        stats = storage.run_stats()
        runs = storage.list_runs(100)
        names = self._selected_names()
        dual = len(names) >= 2
        opt1 = build_option(names[0], stats, runs)
        opt2 = build_option(names[1], stats, runs) if dual else {}

        total_runs = sum(d.get("cnt", 0) or 0 for d in (stats.get("by_day") or []))
        total_persons = sum((d.get("persons") or 0) for d in (stats.get("by_day") or []))
        confidences = stats.get("confidences") or []
        avg = (sum(confidences) / len(confidences) * 100) if confidences else 0.0
        self.summary.setText(
            f"当前组合：{' ＋ '.join(names)}\n"
            f"识别次数 {total_runs}　累计行人 {total_persons}\n"
            f"平均准确率 {avg:.1f}%　样本 {len(confidences)}\n"
            f"共 {len(CHART_TYPES)} 种 ECharts 样式可选"
        )

        payload = {"dual": dual, "option1": opt1, "option2": opt2 if dual else {}}
        js = "if (typeof setCharts==='function') { setCharts(%s); }" % json.dumps(
            payload, ensure_ascii=False
        )
        if self._ready:
            self.web.page().runJavaScript(js)
        else:
            # 页面未就绪时稍后再试
            QTimer.singleShot(500, lambda: self.web.page().runJavaScript(js) if self._ready else None)
