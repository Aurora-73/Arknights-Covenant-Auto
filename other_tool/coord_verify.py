import cv2
import numpy as np
from pathlib import Path


def find_and_mark_subimages(
    main_path: str = "Arknights.png",
    sub_paths: list[str] | None = None,
    threshold: float = 0.8,
    sub_range: range = range(1, 5),
):
    if sub_paths is None:
        sub_paths = [f"{i}.png" for i in sub_range]

    main = cv2.imread(main_path)
    if main is None:
        print(f"无法读取主图: {main_path}")
        return

    result = main.copy()

    for sub_path in sub_paths:
        template = cv2.imread(sub_path)
        if template is None:
            print(f"无法读取模板: {sub_path}")
            continue

        th, tw = template.shape[:2]
        res = cv2.matchTemplate(main, template, cv2.TM_CCOEFF_NORMED)
        matches = list(zip(*np.where(res >= threshold)[::-1]))  # (x, y) 格式

        if not matches:
            print(f"{sub_path}: 未找到匹配")
            continue

        # 去重（合并相近的匹配点）
        filtered = []
        for pt in matches:
            if all(abs(pt[0] - p[0]) > tw // 2 or abs(pt[1] - p[1]) > th // 2 for p in filtered):
                filtered.append(pt)

        for x, y in filtered:
            cx, cy = x + tw // 2, y + th // 2
            print(f"{sub_path}: 左上角=({x}, {y})  中心=({cx}, {cy})")
            cv2.rectangle(result, (x, y), (x + tw, y + th), (0, 255, 0), 2)
            cv2.putText(result, Path(sub_path).stem, (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    out_path = Path(main_path).with_stem(Path(main_path).stem + "_marked")
    cv2.imwrite(str(out_path), result)
    print(f"已保存标注图: {out_path}")


find_and_mark_subimages()