"""
Visual Diff Engine — Compares screenshots for visual regression detection.
Supports baseline management, pixel-level diff, heatmap generation, and layout shift detection.
"""

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from PIL import Image, ImageChops, ImageDraw


@dataclass
class DiffResult:
    """Result of a visual comparison."""
    match: bool
    mismatch_percentage: float
    diff_pixel_count: int
    total_pixels: int
    diff_image: Optional[Image.Image] = None
    baseline_path: str = ""
    current_path: str = ""

    def to_dict(self) -> dict:
        return {
            "match": self.match,
            "mismatch_percentage": round(self.mismatch_percentage, 2),
            "diff_pixel_count": self.diff_pixel_count,
            "total_pixels": self.total_pixels,
            "baseline_path": self.baseline_path,
            "current_path": self.current_path,
        }


@dataclass
class LayoutShift:
    """Detected layout shift between two versions."""
    element_id: str
    element_tag: str
    before: dict  # {x, y, width, height}
    after: dict
    delta_x: float
    delta_y: float
    delta_width: float
    delta_height: float

    def to_dict(self) -> dict:
        return {
            "element": f"{self.element_tag}#{self.element_id}",
            "delta_x": self.delta_x,
            "delta_y": self.delta_y,
            "delta_width": self.delta_width,
            "delta_height": self.delta_height,
        }


class VisualDiff:
    """Compares screenshots for visual regression."""

    DIFF_THRESHOLD = 0.1  # 0.1% mismatch is acceptable
    DIFF_COLOR = (255, 0, 100)  # Magenta for diff overlay

    def __init__(self, baselines_dir: str = "baselines"):
        self.baselines_dir = Path(baselines_dir)
        self.baselines_dir.mkdir(parents=True, exist_ok=True)

    def capture_baseline(
        self, image_bytes: bytes, name: str, viewport: str = "desktop"
    ) -> str:
        """Store a screenshot as a baseline reference."""
        filename = f"{name}_{viewport}.png"
        path = self.baselines_dir / filename
        path.write_bytes(image_bytes)
        return str(path)

    def compare_with_baseline(
        self,
        current_bytes: bytes,
        name: str,
        viewport: str = "desktop",
        threshold: Optional[float] = None,
    ) -> DiffResult:
        """Compare current screenshot with stored baseline."""
        filename = f"{name}_{viewport}.png"
        baseline_path = self.baselines_dir / filename

        if not baseline_path.exists():
            return DiffResult(
                match=False,
                mismatch_percentage=100.0,
                diff_pixel_count=0,
                total_pixels=0,
                baseline_path="",
                current_path="(no baseline found)",
            )

        baseline_bytes = baseline_path.read_bytes()
        return self.compare_images(
            baseline_bytes, current_bytes, threshold=threshold
        )

    def compare_images(
        self,
        image_a_bytes: bytes,
        image_b_bytes: bytes,
        threshold: Optional[float] = None,
    ) -> DiffResult:
        """Compare two images pixel-by-pixel."""
        img_a = Image.open(io.BytesIO(image_a_bytes)).convert("RGB")
        img_b = Image.open(io.BytesIO(image_b_bytes)).convert("RGB")

        # Resize to same dimensions if needed
        if img_a.size != img_b.size:
            img_b = img_b.resize(img_a.size, Image.LANCZOS)

        # Pixel diff
        diff_img = ImageChops.difference(img_a, img_b)
        total_pixels = img_a.size[0] * img_a.size[1]

        # Count non-zero pixels
        diff_pixels = 0
        diff_data = diff_img.getdata()
        for pixel in diff_data:
            if any(c > 10 for c in pixel):  # Small tolerance
                diff_pixels += 1

        mismatch_pct = (diff_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        thresh = threshold or self.DIFF_THRESHOLD
        is_match = mismatch_pct <= thresh

        # Generate highlighted diff image
        highlight = self._generate_highlight(img_a, img_b, diff_img)

        return DiffResult(
            match=is_match,
            mismatch_percentage=mismatch_pct,
            diff_pixel_count=diff_pixels,
            total_pixels=total_pixels,
            diff_image=highlight,
        )

    def generate_heatmap(self, diff_result: DiffResult) -> Optional[Image.Image]:
        """Generate a heatmap highlighting changed regions."""
        return diff_result.diff_image

    def save_diff_image(
        self, diff_result: DiffResult, output_path: str
    ) -> Optional[str]:
        """Save the diff image to disk."""
        if diff_result.diff_image:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            diff_result.diff_image.save(str(path))
            return str(path)
        return None

    def detect_layout_shift(
        self, before_boxes: list[dict], after_boxes: list[dict]
    ) -> list[LayoutShift]:
        """Compare bounding boxes between two versions to detect layout shifts."""
        shifts = []

        # Index after boxes by id
        after_by_id = {}
        for box in after_boxes:
            if box.get("id"):
                after_by_id[box["id"]] = box

        for before_box in before_boxes:
            bid = before_box.get("id")
            if not bid or bid not in after_by_id:
                continue

            after_box = after_by_id[bid]
            dx = after_box.get("x", 0) - before_box.get("x", 0)
            dy = after_box.get("y", 0) - before_box.get("y", 0)
            dw = after_box.get("width", 0) - before_box.get("width", 0)
            dh = after_box.get("height", 0) - before_box.get("height", 0)

            if abs(dx) > 2 or abs(dy) > 2 or abs(dw) > 2 or abs(dh) > 2:
                shifts.append(
                    LayoutShift(
                        element_id=bid,
                        element_tag=before_box.get("tag", ""),
                        before={
                            "x": before_box.get("x", 0),
                            "y": before_box.get("y", 0),
                            "width": before_box.get("width", 0),
                            "height": before_box.get("height", 0),
                        },
                        after={
                            "x": after_box.get("x", 0),
                            "y": after_box.get("y", 0),
                            "width": after_box.get("width", 0),
                            "height": after_box.get("height", 0),
                        },
                        delta_x=dx,
                        delta_y=dy,
                        delta_width=dw,
                        delta_height=dh,
                    )
                )

        return shifts

    def detect_missing_elements(
        self, before_boxes: list[dict], after_boxes: list[dict]
    ) -> list[dict]:
        """Find elements present in before but missing in after."""
        after_ids = {b.get("id") for b in after_boxes if b.get("id")}
        missing = []
        for box in before_boxes:
            if box.get("id") and box["id"] not in after_ids:
                missing.append(box)
        return missing

    # --- Private ---

    def _generate_highlight(
        self,
        img_a: Image.Image,
        img_b: Image.Image,
        diff: Image.Image,
    ) -> Image.Image:
        """Generate a side-by-side comparison with diff overlay."""
        w, h = img_a.size

        # Create a combined image: [before] [diff overlay] [after]
        combined = Image.new("RGB", (w * 3, h), (30, 30, 30))
        combined.paste(img_a, (0, 0))
        combined.paste(img_b, (w * 2, 0))

        # Create diff overlay on top of before image
        overlay = img_a.copy()
        draw = ImageDraw.Draw(overlay)
        diff_data = list(diff.getdata())

        for i, pixel in enumerate(diff_data):
            if any(c > 10 for c in pixel):
                x = i % w
                y = i // w
                draw.point((x, y), fill=self.DIFF_COLOR)

        combined.paste(overlay, (w, 0))
        return combined
