# -*- coding: utf-8 -*-
"""
슬랙 없이 로컬에서 결과 이미지를 바로 확인해보는 스크립트.

사용법:
    python3 test_render.py                 # 샘플 데이터로 렌더링 -> output.png
    python3 test_render.py --grid           # 50px 눈금이 그려진 버전도 함께 생성 (좌표 조정용)
    python3 test_render.py --file 내데이터.txt   # 직접 만든 탭 구분 텍스트 파일로 렌더링
"""

import sys

from parser import parse_sheet_text
from renderer import build_price_table, draw_debug_grid

# 시트 스크린샷 속 힐스테이트메디알레 샘플 데이터 (A~M열, 탭 구분)
# 컬럼 순서: A단지명 B주관사 C점검유형 D평형 E전용면적 F수식 G정가 H공동구매가 I타임특가 J전체총합 K- L- M프로모션최종가
SAMPLE = "\n".join([
    "\t".join(["힐스테이트메디알레", "주관사", "프리미엄", "20", "51", "304,500", "239,000", "-", "191,000", "376,000", "-", "-", "276,000"]),
    "\t".join(["힐스테이트메디알레", "주관사", "프리미엄", "24", "59", "333,500", "249,000", "-", "199,000", "384,000", "-", "-", "284,000"]),
    "\t".join(["힐스테이트메디알레", "주관사", "프리미엄", "29", "74", "420,500", "273,000", "-", "223,000", "408,000", "-", "-", "308,000"]),
    "\t".join(["힐스테이트메디알레", "주관사", "프리미엄", "33", "84", "478,500", "289,000", "-", "239,000", "424,000", "-", "-", "324,000"]),
    "\t".join(["힐스테이트메디알레", "주관사", "프리미엄", "45", "114", "652,500", "369,000", "-", "295,000", "480,000", "-", "-", "380,000"]),
])


def main():
    grid = "--grid" in sys.argv
    text = SAMPLE

    if "--file" in sys.argv:
        path = sys.argv[sys.argv.index("--file") + 1]
        with open(path, encoding="utf-8") as f:
            text = f.read()

    rows = parse_sheet_text(text)
    print(f"{len(rows)}개 행을 인식했습니다. 단지명: {rows[0]['complex_name']}")

    img = build_price_table(rows)
    img.save("output.png")
    print("output.png 생성 완료")

    if grid:
        draw_debug_grid(img).save("output_grid.png")
        print("output_grid.png 생성 완료 (좌표 조정용 눈금 포함)")


if __name__ == "__main__":
    main()
