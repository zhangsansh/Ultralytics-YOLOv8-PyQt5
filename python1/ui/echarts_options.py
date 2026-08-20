# -*- coding: utf-8 -*-
"""行人识别数据 → ECharts option 构建（多种官方示例风格组合）。"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any


CHART_TYPES = [
    "渐变堆叠面积图",
    "带背景色的柱状图",
    "柱状图标签旋转",
    "嵌套环形图",
    "饼图纹理",
    "数据聚合",
    "聚合过程可视化",
    "线性回归（统计插件）",
    "单轴散点图",
    "AQI-雷达图",
    "数据聚合盒须图",
    "热力图-大数据",
    "日历热力图",
    "笛卡尔坐标系 Graph",
    "关系图自动隐藏重叠标签",
    "依赖关系图",
    "多棵树",
    "径向树状图",
    "矩形树图与旭日图过渡",
]


def _sample_days(by_day: list[dict], n: int = 7) -> tuple[list[str], list[float], list[float], list[float]]:
    if not by_day:
        days = [(datetime.now() - timedelta(days=i)).strftime("%m-%d") for i in range(n)][::-1]
        return days, [0] * n, [0] * n, [0] * n
    days = [str(d.get("day", ""))[-5:] for d in by_day]
    cnts = [float(d.get("cnt") or 0) for d in by_day]
    persons = [float(d.get("persons") or 0) for d in by_day]
    avgs = [float(d.get("avg_conf") or 0) * 100 for d in by_day]
    return days, cnts, persons, avgs


def _dark_text() -> dict:
    return {"color": "#e2e8f0", "fontSize": 14}


def build_option(name: str, stats: dict[str, Any], runs: list[dict] | None = None) -> dict:
    by_day = stats.get("by_day") or []
    confidences = stats.get("confidences") or []
    recent = list(reversed(stats.get("recent") or []))
    runs = runs or []
    days, cnts, persons, avgs = _sample_days(by_day)

    builders = {
        "渐变堆叠面积图": lambda: _stacked_area(days, cnts, persons, avgs),
        "带背景色的柱状图": lambda: _bar_background(days, persons),
        "柱状图标签旋转": lambda: _bar_rotate(recent),
        "嵌套环形图": lambda: _nested_ring(confidences, persons, cnts),
        "饼图纹理": lambda: _pie_texture(confidences),
        "数据聚合": lambda: _data_aggregate(confidences),
        "聚合过程可视化": lambda: _aggregate_process(confidences),
        "线性回归（统计插件）": lambda: _linear_regression(recent),
        "单轴散点图": lambda: _single_axis_scatter(confidences),
        "AQI-雷达图": lambda: _aqi_radar(stats, confidences, recent),
        "数据聚合盒须图": lambda: _boxplot(confidences, by_day),
        "热力图-大数据": lambda: _heatmap_big(confidences),
        "日历热力图": lambda: _calendar_heatmap(by_day, runs),
        "笛卡尔坐标系 Graph": lambda: _cartesian_graph(by_day, recent),
        "关系图自动隐藏重叠标签": lambda: _graph_hide_overlap(by_day, runs),
        "依赖关系图": lambda: _dependency_graph(by_day, runs),
        "多棵树": lambda: _multi_tree(by_day, runs),
        "径向树状图": lambda: _radial_tree(by_day, runs),
        "矩形树图与旭日图过渡": lambda: _treemap_sunburst(by_day, confidences),
    }
    fn = builders.get(name)
    if not fn:
        return _stacked_area(days, cnts, persons, avgs)
    opt = fn()
    opt.setdefault("backgroundColor", "transparent")
    opt.setdefault("textStyle", _dark_text())
    return opt


def _stacked_area(days, cnts, persons, avgs) -> dict:
    return {
        "title": {"text": "渐变堆叠面积图 · 次数/人数/准确率", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["识别次数", "行人数", "准确率%"], "top": 30, "textStyle": _dark_text()},
        "xAxis": {"type": "category", "data": days, "axisLabel": {"color": "#94a3b8"}},
        "yAxis": {"type": "value", "axisLabel": {"color": "#94a3b8"}, "splitLine": {"lineStyle": {"color": "#334155"}}},
        "series": [
            {
                "name": "识别次数",
                "type": "line",
                "stack": "Total",
                "areaStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [{"offset": 0, "color": "rgba(56,189,248,0.8)"}, {"offset": 1, "color": "rgba(56,189,248,0.05)"}],
                    }
                },
                "emphasis": {"focus": "series"},
                "data": cnts,
                "smooth": True,
            },
            {
                "name": "行人数",
                "type": "line",
                "stack": "Total",
                "areaStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [{"offset": 0, "color": "rgba(251,191,36,0.8)"}, {"offset": 1, "color": "rgba(251,191,36,0.05)"}],
                    }
                },
                "data": persons,
                "smooth": True,
            },
            {
                "name": "准确率%",
                "type": "line",
                "stack": "Total",
                "areaStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [{"offset": 0, "color": "rgba(52,211,153,0.8)"}, {"offset": 1, "color": "rgba(52,211,153,0.05)"}],
                    }
                },
                "data": avgs,
                "smooth": True,
            },
        ],
    }


def _bar_background(days, persons) -> dict:
    return {
        "title": {"text": "带背景色的柱状图 · 每日行人数", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": days, "axisLabel": {"color": "#94a3b8"}},
        "yAxis": {"type": "value", "axisLabel": {"color": "#94a3b8"}, "splitLine": {"lineStyle": {"color": "#334155"}}},
        "series": [
            {
                "type": "bar",
                "data": persons,
                "showBackground": True,
                "backgroundStyle": {"color": "rgba(148,163,184,0.18)"},
                "itemStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [{"offset": 0, "color": "#38bdf8"}, {"offset": 1, "color": "#0369a1"}],
                    },
                    "borderRadius": [6, 6, 0, 0],
                },
            }
        ],
    }


def _bar_rotate(recent) -> dict:
    labels = [str(r.get("created_at", ""))[-8:] for r in recent] or ["暂无"]
    vals = [float(r.get("person_count") or 0) for r in recent] or [0]
    return {
        "title": {"text": "柱状图标签旋转 · 最近识别人数", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"trigger": "axis"},
        "grid": {"bottom": 80},
        "xAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"rotate": 45, "color": "#94a3b8", "interval": 0},
        },
        "yAxis": {"type": "value", "axisLabel": {"color": "#94a3b8"}, "splitLine": {"lineStyle": {"color": "#334155"}}},
        "series": [{"type": "bar", "data": vals, "itemStyle": {"color": "#f472b6"}, "label": {"show": True, "position": "top", "color": "#e2e8f0"}}],
    }


def _nested_ring(confidences, persons, cnts) -> dict:
    high = sum(1 for c in confidences if c >= 0.5)
    mid = sum(1 for c in confidences if 0.35 <= c < 0.5)
    low = sum(1 for c in confidences if c < 0.35)
    if high + mid + low == 0:
        high, mid, low = 1, 1, 1
    total_p = sum(persons) or 1
    total_c = sum(cnts) or 1
    return {
        "title": {"text": "嵌套环形图 · 准确率分层 / 规模", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"trigger": "item"},
        "series": [
            {
                "name": "准确率分层",
                "type": "pie",
                "radius": [0, "35%"],
                "label": {"position": "inner", "fontSize": 12, "color": "#0f172a"},
                "data": [
                    {"value": high, "name": "高", "itemStyle": {"color": "#34d399"}},
                    {"value": mid, "name": "中", "itemStyle": {"color": "#fbbf24"}},
                    {"value": low, "name": "低", "itemStyle": {"color": "#f87171"}},
                ],
            },
            {
                "name": "规模",
                "type": "pie",
                "radius": ["45%", "65%"],
                "label": {"color": "#e2e8f0"},
                "data": [
                    {"value": total_p, "name": "累计行人", "itemStyle": {"color": "#38bdf8"}},
                    {"value": total_c, "name": "识别次数", "itemStyle": {"color": "#a78bfa"}},
                ],
            },
        ],
    }


def _pie_texture(confidences) -> dict:
    bins = [("0-20%", 0), ("20-40%", 0), ("40-60%", 0), ("60-80%", 0), ("80-100%", 0)]
    for c in confidences:
        p = c * 100
        idx = min(4, int(p // 20))
        bins[idx] = (bins[idx][0], bins[idx][1] + 1)
    if sum(b[1] for b in bins) == 0:
        bins = [("示例A", 3), ("示例B", 2), ("示例C", 1)]
    colors = ["#38bdf8", "#34d399", "#fbbf24", "#f472b6", "#a78bfa"]
    data = []
    for i, (name, val) in enumerate(bins):
        data.append({
            "value": val,
            "name": name,
            "itemStyle": {
                "color": colors[i % len(colors)],
                "decal": {"symbol": "rect", "symbolSize": 1, "rotation": math.pi / 4, "dashArrayX": [1, 0], "dashArrayY": [2, 3], "color": "rgba(255,255,255,0.25)"},
            },
        })
    return {
        "title": {"text": "饼图纹理 · 准确率区间", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"trigger": "item"},
        "aria": {"enabled": True, "decal": {"show": True}},
        "series": [{"type": "pie", "radius": "65%", "data": data, "label": {"color": "#e2e8f0"}}],
    }


def _data_aggregate(confidences) -> dict:
    # 将置信度按 0.1 分箱聚合
    buckets = {f"{i/10:.1f}-{(i+1)/10:.1f}": 0 for i in range(10)}
    for c in confidences:
        i = min(9, int(c * 10))
        key = f"{i/10:.1f}-{(i+1)/10:.1f}"
        buckets[key] += 1
    keys = list(buckets.keys())
    vals = list(buckets.values())
    if sum(vals) == 0:
        vals = [1] * 10
    return {
        "title": {"text": "数据聚合 · 准确率分箱计数", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": keys, "axisLabel": {"color": "#94a3b8", "rotate": 30}},
        "yAxis": {"type": "value", "name": "聚合数量", "axisLabel": {"color": "#94a3b8"}, "splitLine": {"lineStyle": {"color": "#334155"}}},
        "series": [{"type": "bar", "data": vals, "itemStyle": {"color": "#34d399"}, "barWidth": "60%"}],
    }


def _aggregate_process(confidences) -> dict:
    # 模拟聚合过程：逐步合并分箱
    raw = confidences[:40] if confidences else [random.random() * 0.6 + 0.2 for _ in range(20)]
    steps = []
    cur = [round(x, 2) for x in raw]
    steps.append(cur[:])
    while len(cur) > 4:
        nxt = []
        for i in range(0, len(cur), 2):
            if i + 1 < len(cur):
                nxt.append(round((cur[i] + cur[i + 1]) / 2, 2))
            else:
                nxt.append(cur[i])
        cur = nxt
        steps.append(cur[:])
    series = []
    for si, step in enumerate(steps):
        series.append({
            "name": f"第{si+1}步",
            "type": "scatter",
            "data": [[si, v] for v in step],
            "symbolSize": 12 + si * 2,
        })
    return {
        "title": {"text": "聚合过程可视化 · 置信度两两合并", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"trigger": "item"},
        "legend": {"top": 30, "textStyle": _dark_text()},
        "xAxis": {"type": "category", "data": [f"步骤{i+1}" for i in range(len(steps))], "axisLabel": {"color": "#94a3b8"}},
        "yAxis": {"type": "value", "name": "置信度", "min": 0, "max": 1, "axisLabel": {"color": "#94a3b8"}, "splitLine": {"lineStyle": {"color": "#334155"}}},
        "series": series,
    }


def _linear_regression(recent) -> dict:
    # 使用 ecStat 在前端做回归；这里准备 [[x,y], ...]
    pts = []
    for i, r in enumerate(recent or []):
        pts.append([i, float(r.get("person_count") or 0)])
    if len(pts) < 2:
        pts = [[0, 1], [1, 2], [2, 2], [3, 3], [4, 4], [5, 5]]
    return {
        "title": {"text": "线性回归 · 次数序号 vs 人数（ecStat）", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "value", "axisLabel": {"color": "#94a3b8"}, "splitLine": {"lineStyle": {"color": "#334155"}}},
        "yAxis": {"type": "value", "axisLabel": {"color": "#94a3b8"}, "splitLine": {"lineStyle": {"color": "#334155"}}},
        "dataset": [{"source": pts}, {"transform": {"type": "ecStat:regression"}}],
        "series": [
            {"name": "散点", "type": "scatter", "datasetIndex": 0, "symbolSize": 10, "itemStyle": {"color": "#38bdf8"}},
            {
                "name": "回归线",
                "type": "line",
                "datasetIndex": 1,
                "symbolSize": 0.1,
                "lineStyle": {"color": "#fbbf24", "width": 2},
                "encode": {"x": 0, "y": 1},
                "label": {"show": True, "fontSize": 14, "color": "#fbbf24", "formatter": "回归拟合"},
            },
        ],
        "_use_ecstat": True,
    }


def _single_axis_scatter(confidences) -> dict:
    vals = [round(c * 100, 1) for c in (confidences[:60] if confidences else [random.random() * 100 for _ in range(24)])]
    cats = [f"样本{i+1}" for i in range(len(vals))]
    return {
        "title": {"text": "单轴散点图 · 准确率(%)", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"trigger": "item"},
        "singleAxis": {
            "left": 80,
            "right": 80,
            "type": "category",
            "boundaryGap": False,
            "data": cats,
            "axisLabel": {"interval": max(0, len(cats) // 12), "color": "#94a3b8", "rotate": 40},
        },
        "series": [
            {
                "type": "scatter",
                "coordinateSystem": "singleAxis",
                "data": vals,
                "symbolSize": 14,
                "itemStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 1, "y2": 0,
                        "colorStops": [{"offset": 0, "color": "#38bdf8"}, {"offset": 1, "color": "#34d399"}],
                    }
                },
            }
        ],
    }


def _aqi_radar(stats, confidences, recent) -> dict:
    avg = (sum(confidences) / len(confidences) * 100) if confidences else 50
    persons = sum((d.get("persons") or 0) for d in (stats.get("by_day") or []))
    runs_n = sum((d.get("cnt") or 0) for d in (stats.get("by_day") or []))
    recent_avg = (sum(r.get("person_count") or 0 for r in recent) / max(1, len(recent))) if recent else 0
    high_ratio = (sum(1 for c in confidences if c >= 0.5) / max(1, len(confidences))) * 100
    indicators = [
        {"name": "平均准确率", "max": 100},
        {"name": "高置信占比", "max": 100},
        {"name": "累计人数规模", "max": max(50, persons * 1.2)},
        {"name": "识别次数规模", "max": max(20, runs_n * 1.2)},
        {"name": "近期人均", "max": max(10, recent_avg * 2 + 1)},
        {"name": "稳定性", "max": 100},
    ]
    stability = max(0, 100 - (max(confidences) - min(confidences)) * 100) if confidences else 60
    return {
        "title": {"text": "AQI 风格雷达图 · 识别质量画像", "left": "center", "textStyle": _dark_text()},
        "tooltip": {},
        "radar": {
            "indicator": indicators,
            "axisName": {"color": "#e2e8f0"},
            "splitLine": {"lineStyle": {"color": "#334155"}},
            "splitArea": {"areaStyle": {"color": ["rgba(56,189,248,0.05)", "rgba(56,189,248,0.12)"]}},
        },
        "series": [
            {
                "type": "radar",
                "data": [
                    {
                        "value": [avg, high_ratio, persons, runs_n, recent_avg, stability],
                        "name": "当前画像",
                        "areaStyle": {"color": "rgba(56,189,248,0.35)"},
                        "lineStyle": {"color": "#38bdf8"},
                    }
                ],
            }
        ],
    }


def _boxplot(confidences, by_day) -> dict:
    # 按日聚合置信度做盒须；不足则造示例
    groups = {}
    # 无逐框按日数据时，用全局置信度切段模拟多组
    if confidences:
        chunk = max(1, len(confidences) // max(1, len(by_day) or 5))
        for i in range(0, len(confidences), chunk):
            key = f"组{len(groups)+1}"
            groups[key] = [c * 100 for c in confidences[i:i + chunk]]
            if len(groups) >= 6:
                break
    if not groups:
        groups = {f"组{i}": [random.uniform(20, 90) for _ in range(12)] for i in range(1, 5)}

    def five(arr):
        s = sorted(arr)
        n = len(s)
        return [s[0], s[n // 4], s[n // 2], s[(3 * n) // 4], s[-1]]

    source = [five(v) for v in groups.values()]
    return {
        "title": {"text": "数据聚合盒须图 · 准确率(%)", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"trigger": "item"},
        "xAxis": {"type": "category", "data": list(groups.keys()), "axisLabel": {"color": "#94a3b8"}},
        "yAxis": {"type": "value", "axisLabel": {"color": "#94a3b8"}, "splitLine": {"lineStyle": {"color": "#334155"}}},
        "series": [{"type": "boxplot", "data": source, "itemStyle": {"color": "#38bdf8", "borderColor": "#e2e8f0"}}],
    }


def _heatmap_big(confidences) -> dict:
    # 构造约 2 万级热力点（小时 x 分钟网格 + 抖动）
    hours = list(range(24))
    slots = list(range(40))  # 24*40=960 base, expand with noise samples
    data = []
    base = confidences or [random.random() for _ in range(200)]
    random.seed(42)
    target = 20000
    while len(data) < target:
        h = random.randrange(24)
        s = random.randrange(40)
        v = base[len(data) % len(base)] * 100
        data.append([s, h, round(v + random.uniform(-5, 5), 1)])
    return {
        "title": {"text": f"热力图 · {len(data)} 点（准确率模拟网格）", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"position": "top"},
        "grid": {"height": "60%", "top": "12%"},
        "xAxis": {"type": "category", "data": [str(i) for i in slots], "axisLabel": {"color": "#94a3b8", "interval": 4}},
        "yAxis": {"type": "category", "data": [f"{h:02d}时" for h in hours], "axisLabel": {"color": "#94a3b8"}},
        "visualMap": {
            "min": 0, "max": 100, "calculable": True, "orient": "horizontal", "left": "center", "bottom": 10,
            "textStyle": {"color": "#e2e8f0"},
            "inRange": {"color": ["#0f172a", "#0369a1", "#38bdf8", "#fbbf24", "#f87171"]},
        },
        "series": [{"type": "heatmap", "data": data, "emphasis": {"itemStyle": {"shadowBlur": 10}}}],
    }


def _calendar_heatmap(by_day, runs) -> dict:
    year = datetime.now().year
    data_map = {}
    for d in by_day:
        day = str(d.get("day", ""))
        if day:
            data_map[day] = float(d.get("persons") or 0)
    for r in runs:
        day = str(r.get("day") or (str(r.get("created_at", ""))[:10]))
        if day and day not in data_map:
            data_map[day] = float(r.get("person_count") or 0)
        elif day:
            data_map[day] = data_map.get(day, 0) + float(r.get("person_count") or 0)
    if not data_map:
        today = datetime.now().date()
        for i in range(30):
            d = (today - timedelta(days=i)).isoformat()
            data_map[d] = random.randint(0, 8)
    data = [[k, v] for k, v in sorted(data_map.items())]
    vmax = max([v for _, v in data] + [1])
    return {
        "title": {"text": "日历热力图 · 每日检出行人数", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"formatter": "{c}"},
        "visualMap": {
            "min": 0, "max": vmax, "calculable": True, "orient": "horizontal", "left": "center", "bottom": 20,
            "textStyle": {"color": "#e2e8f0"},
            "inRange": {"color": ["#12263a", "#38bdf8", "#fbbf24"]},
        },
        "calendar": {
            "range": str(year),
            "cellSize": ["auto", 16],
            "top": 80,
            "left": 40,
            "right": 30,
            "itemStyle": {"borderWidth": 0.5, "borderColor": "#334155"},
            "yearLabel": {"color": "#e2e8f0"},
            "monthLabel": {"color": "#94a3b8"},
            "dayLabel": {"color": "#94a3b8"},
        },
        "series": [{"type": "heatmap", "coordinateSystem": "calendar", "data": data}],
    }


def _cartesian_graph(by_day, recent) -> dict:
    nodes = []
    links = []
    for i, d in enumerate(by_day[-8:] or [{"day": "D", "persons": 1, "avg_conf": 0.5}]):
        nodes.append({
            "id": f"d{i}",
            "name": str(d.get("day", ""))[-5:],
            "x": i * 80,
            "y": float(d.get("persons") or 0) * 20,
            "symbolSize": 20 + float(d.get("avg_conf") or 0) * 30,
            "itemStyle": {"color": "#38bdf8"},
        })
        if i:
            links.append({"source": f"d{i-1}", "target": f"d{i}"})
    for j, r in enumerate((recent or [])[-5:]):
        nodes.append({
            "id": f"r{j}",
            "name": f"R{j+1}",
            "x": j * 60 + 40,
            "y": 120 + float(r.get("avg_conf") or 0) * 80,
            "symbolSize": 14,
            "itemStyle": {"color": "#f472b6"},
        })
        if by_day:
            links.append({"source": f"d{min(j, len(by_day[-8:])-1)}", "target": f"r{j}"})
    return {
        "title": {"text": "笛卡尔坐标系 Graph · 日节点与识别节点", "left": "center", "textStyle": _dark_text()},
        "tooltip": {},
        "xAxis": {"show": False, "min": -20, "max": 700},
        "yAxis": {"show": False, "min": -20, "max": 280},
        "series": [{
            "type": "graph",
            "coordinateSystem": "cartesian2d",
            "data": nodes,
            "links": links,
            "edgeSymbol": ["none", "arrow"],
            "label": {"show": True, "color": "#e2e8f0"},
            "lineStyle": {"color": "#64748b", "curveness": 0.15},
        }],
    }


def _graph_hide_overlap(by_day, runs) -> dict:
    categories = [{"name": "日期"}, {"name": "识别"}, {"name": "行人"}]
    nodes = [{"id": "root", "name": "行人识别", "symbolSize": 40, "category": 0, "label": {"show": True}}]
    links = []
    for i, d in enumerate((by_day or [{"day": "今日", "persons": 1}])[-6:]):
        nid = f"day{i}"
        nodes.append({"id": nid, "name": str(d.get("day", ""))[-5:], "symbolSize": 28, "category": 0})
        links.append({"source": "root", "target": nid})
        for j in range(min(3, int(d.get("cnt") or 1))):
            rid = f"{nid}_r{j}"
            nodes.append({"id": rid, "name": f"识别{j+1}", "symbolSize": 18, "category": 1})
            links.append({"source": nid, "target": rid})
            for k in range(min(2, max(1, int((d.get("persons") or 1) // max(1, int(d.get("cnt") or 1)))))):
                pid = f"{rid}_p{k}"
                nodes.append({"id": pid, "name": f"人{k+1}", "symbolSize": 12, "category": 2})
                links.append({"source": rid, "target": pid})
    return {
        "title": {"text": "关系图 · 自动隐藏重叠标签", "left": "center", "textStyle": _dark_text()},
        "tooltip": {},
        "legend": [{"data": [c["name"] for c in categories], "textStyle": _dark_text()}],
        "series": [{
            "type": "graph",
            "layout": "force",
            "roam": True,
            "categories": categories,
            "data": nodes,
            "links": links,
            "label": {"show": True, "position": "right", "formatter": "{b}", "color": "#e2e8f0"},
            "labelLayout": {"hideOverlap": True},
            "force": {"repulsion": 120, "edgeLength": 60},
            "lineStyle": {"color": "source", "curveness": 0.1},
        }],
    }


def _dependency_graph(by_day, runs) -> dict:
    # NPM 风格依赖：配置 → 检测 → 结果 → 存储
    nodes = [
        {"id": "cfg", "name": "参数配置", "symbolSize": 36, "itemStyle": {"color": "#a78bfa"}},
        {"id": "yolo", "name": "YOLOv8", "symbolSize": 42, "itemStyle": {"color": "#38bdf8"}},
        {"id": "img", "name": "图片/视频", "symbolSize": 34, "itemStyle": {"color": "#fbbf24"}},
        {"id": "seg", "name": "行人分割", "symbolSize": 30, "itemStyle": {"color": "#34d399"}},
        {"id": "db", "name": "SQLite", "symbolSize": 28, "itemStyle": {"color": "#f472b6"}},
        {"id": "log", "name": "日志归档", "symbolSize": 28, "itemStyle": {"color": "#94a3b8"}},
        {"id": "chart", "name": "图表分析", "symbolSize": 30, "itemStyle": {"color": "#22d3ee"}},
    ]
    for i, d in enumerate((by_day or [])[-4:]):
        nodes.append({"id": f"day{i}", "name": str(d.get("day", ""))[-5:], "symbolSize": 20, "itemStyle": {"color": "#64748b"}})
    links = [
        {"source": "cfg", "target": "yolo"},
        {"source": "img", "target": "yolo"},
        {"source": "yolo", "target": "seg"},
        {"source": "yolo", "target": "db"},
        {"source": "yolo", "target": "log"},
        {"source": "db", "target": "chart"},
        {"source": "seg", "target": "chart"},
    ]
    for i, d in enumerate((by_day or [])[-4:]):
        links.append({"source": "db", "target": f"day{i}"})
    return {
        "title": {"text": "依赖关系图 · 系统模块（NPM 风格）", "left": "center", "textStyle": _dark_text()},
        "tooltip": {},
        "series": [{
            "type": "graph",
            "layout": "force",
            "roam": True,
            "data": nodes,
            "links": links,
            "label": {"show": True, "color": "#e2e8f0"},
            "force": {"repulsion": 180, "edgeLength": [50, 120]},
            "lineStyle": {"color": "#64748b", "curveness": 0.2},
            "edgeSymbol": ["none", "arrow"],
        }],
    }


def _tree_children(by_day, runs) -> list:
    children = []
    for d in (by_day or [{"day": "今日", "persons": 1, "cnt": 1, "avg_conf": 0.5}])[-5:]:
        day_name = str(d.get("day", "日"))
        kids = []
        for j in range(min(3, max(1, int(d.get("cnt") or 1)))):
            kids.append({
                "name": f"识别#{j+1}",
                "value": float(d.get("avg_conf") or 0) * 100,
                "children": [
                    {"name": f"行人*{max(1, int((d.get('persons') or 1)/(d.get('cnt') or 1)))}", "value": float(d.get("persons") or 1)},
                ],
            })
        children.append({"name": day_name, "children": kids})
    return children


def _multi_tree(by_day, runs) -> dict:
    left = {"name": "按日期", "children": _tree_children(by_day, runs)}
    right = {
        "name": "按准确率",
        "children": [
            {"name": "高≥50%", "value": 50},
            {"name": "中35-50%", "value": 30},
            {"name": "低<35%", "value": 20},
        ],
    }
    return {
        "title": {"text": "多棵树 · 日期树 / 准确率树", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"trigger": "item"},
        "series": [
            {
                "type": "tree",
                "data": [left],
                "left": "2%",
                "right": "52%",
                "symbolSize": 10,
                "label": {"position": "left", "color": "#e2e8f0"},
                "leaves": {"label": {"position": "right"}},
                "expandAndCollapse": True,
                "animationDuration": 550,
            },
            {
                "type": "tree",
                "data": [right],
                "left": "52%",
                "right": "2%",
                "orient": "RL",
                "symbolSize": 10,
                "label": {"position": "right", "color": "#e2e8f0"},
                "leaves": {"label": {"position": "left"}},
                "expandAndCollapse": True,
            },
        ],
    }


def _radial_tree(by_day, runs) -> dict:
    return {
        "title": {"text": "径向树状图 · 识别结构", "left": "center", "textStyle": _dark_text()},
        "tooltip": {"trigger": "item"},
        "series": [{
            "type": "tree",
            "data": [{"name": "行人识别系统", "children": _tree_children(by_day, runs)}],
            "layout": "radial",
            "symbol": "emptyCircle",
            "symbolSize": 10,
            "initialTreeDepth": 3,
            "animationDurationUpdate": 750,
            "label": {"color": "#e2e8f0"},
        }],
    }


def _treemap_sunburst(by_day, confidences) -> dict:
    high = sum(1 for c in confidences if c >= 0.5) or 1
    mid = sum(1 for c in confidences if 0.35 <= c < 0.5) or 1
    low = sum(1 for c in confidences if c < 0.35) or 1
    data = [
        {
            "name": "识别数据",
            "children": [
                {
                    "name": "准确率",
                    "children": [
                        {"name": "高", "value": high, "itemStyle": {"color": "#34d399"}},
                        {"name": "中", "value": mid, "itemStyle": {"color": "#fbbf24"}},
                        {"name": "低", "value": low, "itemStyle": {"color": "#f87171"}},
                    ],
                },
                {
                    "name": "日期",
                    "children": [
                        {"name": str(d.get("day", ""))[-5:] or f"D{i}", "value": max(1, float(d.get("persons") or 1))}
                        for i, d in enumerate((by_day or [{"day": "今日", "persons": 3}])[-6:])
                    ],
                },
            ],
        }
    ]
    return {
        "title": {"text": "矩形树图 / 旭日图（工具栏切换动画过渡）", "left": "center", "textStyle": _dark_text()},
        "tooltip": {},
        "toolbox": {
            "right": 20,
            "feature": {
                "myTreemap": {
                    "show": True,
                    "title": "矩形树图",
                    "icon": "path://M0,0h10v10h-10z",
                },
                "mySunburst": {
                    "show": True,
                    "title": "旭日图",
                    "icon": "path://M5,0 A5,5 0 1,1 4.9,0 Z",
                },
            },
            "iconStyle": {"borderColor": "#e2e8f0"},
        },
        "series": [{
            "type": "treemap",
            "id": "viz",
            "animationDurationUpdate": 1000,
            "roam": False,
            "nodeClick": False,
            "data": data,
            "label": {"color": "#0f172a", "fontSize": 13},
            "breadcrumb": {"itemStyle": {"color": "#1e293b"}, "textStyle": {"color": "#e2e8f0"}},
        }],
        "_treemap_sunburst": True,
        "_tree_data": data,
    }
