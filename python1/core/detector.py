# -*- coding: utf-8 -*-
"""YOLOv8 行人检测（Ultralytics 开源版，仅 person 类别）。"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Optional

import cv2
import numpy as np

from config import ROOT, load_config
from core.logger import app_logger
from core.preprocess import apply_preprocess
from core.segment import annotate_person_image, draw_redetect_boxes, extract_persons
from core.storage import storage


PERSON_CLASS_ID = 0


class PedestrianDetector:
    def __init__(self, model_path: Optional[str] = None) -> None:
        self._model = None
        self._model_path = model_path
        self._loaded_path: Optional[str] = None

    def load(self, model_path: Optional[str] = None) -> None:
        from ultralytics import YOLO

        cfg = load_config()
        configured = str(model_path or self._model_path or cfg.get("model_path") or "")

        # 优先本地分割模型，便于抠图；其次配置路径 / 本地检测模型；最后自动下载 seg
        candidates = [
            str(ROOT / "yolov8n-seg.pt"),
            configured,
            str(ROOT / "yolov8n.pt"),
            "yolov8n-seg.pt",
            "yolov8n.pt",
        ]
        chosen = "yolov8n.pt"
        for c in candidates:
            if not c:
                continue
            if Path(c).exists():
                chosen = c
                break
        else:
            # 无本地权重时下载开源分割权重
            chosen = "yolov8n-seg.pt"
            app_logger.warning("本地模型不存在，将下载/使用 yolov8n-seg.pt")

        if self._model is not None and self._loaded_path == chosen:
            return
        app_logger.info(f"加载 YOLO 模型: {chosen}")
        self._model = YOLO(chosen)
        self._loaded_path = chosen
        self._model_path = configured or chosen

    @property
    def model(self):
        if self._model is None:
            self.load()
        return self._model

    def _predict(self, image_bgr: np.ndarray, params: dict[str, Any]):
        conf = float(params.get("conf", 0.25))
        iou = float(params.get("iou", 0.45))
        imgsz = int(params.get("imgsz", 640))
        max_det = int(params.get("max_det", 300))
        return self.model.predict(
            source=image_bgr,
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            max_det=max_det,
            classes=[PERSON_CLASS_ID],
            verbose=False,
        )

    def _parse_boxes(self, result) -> list[dict[str, Any]]:
        boxes: list[dict[str, Any]] = []
        if result.boxes is None or len(result.boxes) == 0:
            return boxes
        xyxy = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        clss = result.boxes.cls.cpu().numpy().astype(int)
        names = result.names or {}
        for i in range(len(xyxy)):
            x1, y1, x2, y2 = map(float, xyxy[i])
            cid = int(clss[i])
            boxes.append(
                {
                    "class_id": cid,
                    "class_name": names.get(cid, "person"),
                    "conf": float(confs[i]),
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                }
            )
        return boxes

    def _draw(self, image_bgr: np.ndarray, boxes: list[dict[str, Any]], params: dict[str, Any]) -> np.ndarray:
        out = image_bgr.copy()
        lw = max(1, int(params.get("line_width", 2)))
        show_labels = bool(params.get("show_labels", True))
        show_conf = bool(params.get("show_conf", True))
        for b in boxes:
            x1, y1, x2, y2 = map(int, (b["x1"], b["y1"], b["x2"], b["y2"]))
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 200, 255), lw)
            if show_labels or show_conf:
                parts = []
                if show_labels:
                    parts.append(b.get("class_name", "person"))
                if show_conf:
                    parts.append(f"{b['conf']:.2f}")
                label = " ".join(parts)
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                cv2.rectangle(out, (x1, y1 - th - 8), (x1 + tw + 6, y1), (0, 200, 255), -1)
                cv2.putText(
                    out, label, (x1 + 3, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1, cv2.LINE_AA,
                )
        return out

    def _save_person_crops(
        self,
        persons: list[dict[str, Any]],
        source_path: str = "",
    ) -> list[str]:
        paths: list[str] = []
        for p in persons:
            out = storage.save_result_image(
                p["image"],
                source_path=source_path,
                suffix=f"person{p['index']}_re",
            )
            p["path"] = str(out)
            paths.append(str(out))
        return paths

    def redetect_persons(
        self,
        persons: list[dict[str, Any]],
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """对分割出的每个人物图再次 YOLO 识别，并更新展示图与准确率。"""
        out_list: list[dict[str, Any]] = []
        for p in persons:
            raw = p.get("raw_image")
            if raw is None:
                raw = p.get("image")
            if raw is None or not isinstance(raw, np.ndarray) or raw.size == 0:
                out_list.append(p)
                continue

            # 过小裁剪图放大，便于二次检测
            img = raw.copy()
            h, w = img.shape[:2]
            min_side = 320
            if min(h, w) < min_side:
                scale = min_side / float(min(h, w))
                img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

            results = self._predict(img, params)
            boxes = self._parse_boxes(results[0])
            # 若放大过，把框映射回原裁剪尺寸
            if img.shape[0] != h or img.shape[1] != w:
                sx = w / float(img.shape[1])
                sy = h / float(img.shape[0])
                for b in boxes:
                    b["x1"] *= sx
                    b["x2"] *= sx
                    b["y1"] *= sy
                    b["y2"] *= sy

            annotated = draw_redetect_boxes(raw.copy(), boxes, params)
            if boxes:
                best = max(boxes, key=lambda x: float(x.get("conf", 0)))
                re_conf = float(best["conf"])
            else:
                # 二次未检出时保留首次置信度，并标注未复核成功
                re_conf = float(p.get("first_conf", p.get("conf", 0)))

            person = dict(p)
            person["first_conf"] = float(p.get("first_conf", p.get("conf", 0)))
            person["conf"] = re_conf
            person["accuracy"] = re_conf * 100.0
            person["re_boxes"] = boxes
            person["redetected"] = True
            person["re_person_count"] = len(boxes)
            person["image"] = annotate_person_image(annotated, person)
            out_list.append(person)
            app_logger.info(
                f"分割图二次识别 #{person['index']}: "
                f"检出={len(boxes)}, 准确率={re_conf * 100:.1f}% "
                f"(首次 {person['first_conf'] * 100:.1f}%)"
            )
        return out_list

    def detect_image(
        self,
        image_bgr: np.ndarray,
        params: dict[str, Any],
        source_path: str = "",
        persist: bool = True,
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        processed = apply_preprocess(image_bgr, params)
        results = self._predict(processed, params)
        yolo_result = results[0]
        boxes = self._parse_boxes(yolo_result)
        annotated = self._draw(processed, boxes, params)
        # 1) 分割  2) 对分割图二次识别  3) 展示二次结果
        persons = extract_persons(processed, boxes, yolo_result=yolo_result, annotate=False)
        persons = self.redetect_persons(persons, params)
        duration_ms = (time.perf_counter() - t0) * 1000.0

        confs = [b["conf"] for b in boxes]
        re_confs = [float(p.get("conf", 0)) for p in persons]
        stats = {
            "person_count": len(boxes),
            "avg_conf": float(np.mean(confs)) if confs else 0.0,
            "max_conf": float(max(confs)) if confs else 0.0,
            "min_conf": float(min(confs)) if confs else 0.0,
            "duration_ms": duration_ms,
            "re_avg_conf": float(np.mean(re_confs)) if re_confs else 0.0,
            "re_person_count": len(persons),
        }

        result_path = ""
        run_id = None
        person_paths: list[str] = []
        if persist:
            storage.save_params_snapshot(params, note="开始识别前参数快照")
            out = storage.save_result_image(annotated, source_path=source_path)
            result_path = str(out)
            person_paths = self._save_person_crops(persons, source_path=source_path)
            run_id = storage.save_run(
                source_path=source_path,
                source_type="image",
                result_image_path=result_path,
                boxes=boxes,
                duration_ms=duration_ms,
                params=params,
                note=f"persons={len(persons)}; redetect=1; crops={person_paths}",
            )
            app_logger.info(f"已分割并二次识别保存 {len(persons)} 个行人")

        return {
            "annotated": annotated,
            "processed": processed,
            "boxes": boxes,
            "persons": persons,
            "stats": stats,
            "result_path": result_path,
            "person_paths": person_paths,
            "run_id": run_id,
        }

    def detect_video(
        self,
        video_path: str,
        params: dict[str, Any],
        progress_cb: Optional[Callable[[int, int, np.ndarray], None]] = None,
        cancel_flag: Optional[Callable[[], bool]] = None,
    ) -> dict[str, Any]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频: {video_path}")

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        sample_every = max(1, int(params.get("sample_every", 1)))

        from config import day_dirs

        dirs = day_dirs()
        stamp = time.strftime("%H%M%S")
        out_path = dirs["images"] / f"video_det_{stamp}.mp4"
        writer = cv2.VideoWriter(
            str(out_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            max(1.0, fps / sample_every),
            (w, h),
        )

        storage.save_params_snapshot(params, note="视频识别参数快照")
        all_boxes: list[dict[str, Any]] = []
        frame_idx = 0
        written = 0
        last_annotated = None
        last_processed = None
        last_result = None
        last_boxes: list[dict[str, Any]] = []
        t0 = time.perf_counter()

        while True:
            if cancel_flag and cancel_flag():
                app_logger.warning("视频识别已取消")
                break
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % sample_every != 0:
                frame_idx += 1
                continue

            processed = apply_preprocess(frame, params)
            # 旋转/翻转可能改变尺寸，需匹配 writer
            if processed.shape[1] != w or processed.shape[0] != h:
                processed = cv2.resize(processed, (w, h))

            results = self._predict(processed, params)
            boxes = self._parse_boxes(results[0])
            annotated = self._draw(processed, boxes, params)
            writer.write(annotated)
            last_annotated = annotated
            last_processed = processed
            last_result = results[0]
            last_boxes = boxes
            all_boxes.extend(boxes)
            written += 1
            frame_idx += 1
            if progress_cb:
                progress_cb(frame_idx, total, annotated)

        cap.release()
        writer.release()
        duration_ms = (time.perf_counter() - t0) * 1000.0

        confs = [b["conf"] for b in all_boxes]
        stats = {
            "person_count": len(all_boxes),
            "avg_conf": float(np.mean(confs)) if confs else 0.0,
            "max_conf": float(max(confs)) if confs else 0.0,
            "min_conf": float(min(confs)) if confs else 0.0,
            "duration_ms": duration_ms,
            "frames": written,
        }

        # 最后一帧：分割 + 二次识别
        persons: list[dict[str, Any]] = []
        person_paths: list[str] = []
        preview_path = ""
        if last_annotated is not None and last_processed is not None:
            preview = storage.save_result_image(last_annotated, source_path=video_path, suffix="video_preview")
            preview_path = str(preview)
            persons = extract_persons(
                last_processed, last_boxes, yolo_result=last_result, annotate=False
            )
            persons = self.redetect_persons(persons, params)
            person_paths = self._save_person_crops(persons, source_path=video_path)

        re_confs = [float(p.get("conf", 0)) for p in persons]
        stats["re_avg_conf"] = float(np.mean(re_confs)) if re_confs else 0.0
        stats["re_person_count"] = len(persons)

        run_id = storage.save_run(
            source_path=video_path,
            source_type="video",
            result_image_path=str(out_path),
            boxes=all_boxes,
            duration_ms=duration_ms,
            params=params,
            note=f"preview={preview_path}; persons={len(persons)}; redetect=1",
        )
        app_logger.info(
            f"视频识别完成: {out_path}, 帧数={written}, 末帧分割二次识别={len(persons)}"
        )
        return {
            "annotated": last_annotated,
            "boxes": all_boxes,
            "persons": persons,
            "stats": stats,
            "result_path": str(out_path),
            "preview_path": preview_path,
            "person_paths": person_paths,
            "run_id": run_id,
        }


detector = PedestrianDetector()
