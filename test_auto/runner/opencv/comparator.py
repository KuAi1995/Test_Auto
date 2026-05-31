"""OpenCV UI 对比 - SSIM 相似度计算 + 差异标注."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger(__name__)


@dataclass
class CompareResult:
    """对比结果."""

    similarity: float  # 0.0 ~ 1.0
    passed: bool
    diff_image_path: Optional[str] = None
    baseline_path: str = ""
    actual_path: str = ""
    threshold: float = 0.95


class OpenCVComparator:
    """OpenCV UI 截图对比器."""

    def __init__(self, threshold: float = 0.95, output_dir: Optional[Path] = None) -> None:
        """初始化.

        Args:
            threshold: 相似度阈值（低于此值判定为失败）
            output_dir: 差异图输出目录
        """
        self._threshold = threshold
        self._output_dir = output_dir or Path("data/diff")
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def compare(self, baseline_path: Path, actual_path: Path,
                mask_regions: Optional[list[dict]] = None) -> CompareResult:
        """对比两张截图.

        Args:
            baseline_path: 基线截图路径
            actual_path: 实际截图路径
            mask_regions: 需要排除的区域 [{"x": 0, "y": 0, "w": 100, "h": 50}]

        Returns:
            对比结果
        """
        baseline = cv2.imread(str(baseline_path))
        actual = cv2.imread(str(actual_path))

        if baseline is None:
            raise FileNotFoundError(f"基线图片不存在: {baseline_path}")
        if actual is None:
            raise FileNotFoundError(f"实际图片不存在: {actual_path}")

        # 尺寸对齐
        if baseline.shape != actual.shape:
            actual = cv2.resize(actual, (baseline.shape[1], baseline.shape[0]))

        # 应用 mask
        if mask_regions:
            for region in mask_regions:
                x, y, w, h = region["x"], region["y"], region["w"], region["h"]
                baseline[y:y+h, x:x+w] = 0
                actual[y:y+h, x:x+w] = 0

        # 转灰度计算 SSIM
        gray_baseline = cv2.cvtColor(baseline, cv2.COLOR_BGR2GRAY)
        gray_actual = cv2.cvtColor(actual, cv2.COLOR_BGR2GRAY)

        score, diff = ssim(gray_baseline, gray_actual, full=True)
        passed = score >= self._threshold

        # 生成差异图
        diff_path = None
        if not passed:
            diff_path = self._generate_diff_image(baseline, actual, diff, actual_path.stem)

        result = CompareResult(
            similarity=score,
            passed=passed,
            diff_image_path=str(diff_path) if diff_path else None,
            baseline_path=str(baseline_path),
            actual_path=str(actual_path),
            threshold=self._threshold,
        )

        level = logging.INFO if passed else logging.WARNING
        logger.log(level, "UI 对比: %.4f (%s) %s vs %s",
                   score, "PASS" if passed else "FAIL",
                   baseline_path.name, actual_path.name)
        return result

    def _generate_diff_image(self, baseline: np.ndarray, actual: np.ndarray,
                             diff: np.ndarray, name: str) -> Path:
        """生成差异标注图."""
        # 将差异转为 0-255
        diff_uint8 = (255 - diff * 255).astype(np.uint8)

        # 阈值化找差异区域
        thresh = cv2.threshold(diff_uint8, 30, 255, cv2.THRESH_BINARY)[1]
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 在实际图上标注差异区域
        annotated = actual.copy()
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 5 and h > 5:  # 过滤噪点
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # 拼接：基线 | 实际 | 差异
        combined = np.hstack([baseline, annotated])
        output_path = self._output_dir / f"diff_{name}.png"
        cv2.imwrite(str(output_path), combined)
        logger.info("差异图: %s", output_path)
        return output_path
