# -*- coding: utf-8 -*-
"""
구글 시트에서 복사(Ctrl+C)한 여러 줄의 데이터(탭으로 열이 구분됨)를
파싱해서, 이미지 렌더링에 필요한 딕셔너리 리스트로 바꿔줍니다.

입력 예시 (탭으로 구분된 여러 줄, 슬랙 메시지 그대로):
    힐스테이트메디알레	OO건설	프리미엄	20	51	304,500	239,000	191,000	376,000 ...
    힐스테이트메디알레	OO건설	프리미엄	24	59	333,500	249,000	199,000	384,000 ...
    ...

지원하는 예외 케이스:
- 헤더 행(컬럼명이 적힌 첫 줄)이 섞여 있어도 숫자 파싱이 안 되는 줄은 자동으로 건너뜀
- 구글시트에서 셀 안에 줄바꿈이 들어간 경우(예: 단지명이 두 줄로 표시)도 정상 인식
  (탭 구분 CSV 규칙에 따라 큰따옴표로 감싸진 셀은 안의 줄바꿈을 그대로 유지)
- 단지명이 첫 줄(병합된 셀)에만 있고 이후 데이터 줄들은 비어있는 경우, 마지막으로
  나온 단지명을 그대로 이어받아 사용함
- 평형에 "45평"처럼 단위가 이미 붙어 있거나, 전용면적에 "116m²"처럼 단위가 붙어
  있어도 자동으로 숫자만 추출함
"""

import csv
import io

from config import COL_IDX


class ParseError(Exception):
    pass


def _clean_number(raw: str) -> int:
    """'304,500' 같은 문자열에서 콤마/공백/원 등을 제거하고 정수로 변환."""
    if raw is None:
        raise ParseError("빈 값입니다.")
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    if not digits:
        raise ParseError(f"숫자를 찾을 수 없습니다: '{raw}'")
    return int(digits)


def _clean_unit_text(raw: str) -> str:
    """'45평', '116m²', '74㎡' 처럼 이미 단위가 붙어 있으면 숫자만 남기고,
    그 외(순수 숫자만 있는 경우)에는 그대로 반환한다."""
    text = (raw or "").strip()
    for unit in ("평형", "평", "m²", "㎡", "m2"):
        if text.endswith(unit):
            text = text[: -len(unit)].strip()
            break
    return text


def parse_sheet_text(text: str):
    """
    슬랙 메시지 원문(text)을 받아서, 아래 형태의 dict 리스트를 반환한다.

    {
        "complex_name": "힐스테이트메디알레",
        "pyeong": "20",          # 평형 (D열)
        "area": "51",            # 전용면적 (E열)
        "price": 304500,         # 정가 (G열)
        "time_deal": 191000,     # 타임특가 (I열)
        "receipt_strike": 241000,# 사전점검 취소선 = 타임특가 + 5만원
        "total_before": 376000,  # 전체총합 (J열)
        "promo_final": 276000,   # 프로모션 최종가 (M열)
    }

    반환값의 첫 요소의 complex_name 이 전체 단지명으로 사용됩니다.
    """
    if not text or not text.strip():
        raise ParseError("입력된 데이터가 없습니다. 시트에서 행을 복사해 붙여넣어 주세요.")

    need_cols = max(COL_IDX.values()) + 1
    rows = []
    last_complex_name = ""

    reader = csv.reader(io.StringIO(text.strip("\n")), delimiter="\t")
    for cols in reader:
        if not cols or all(not c.strip() for c in cols):
            continue

        # 컬럼 수가 부족하면 빈 칸으로 채워서라도 인덱스 접근이 가능하게 함
        if len(cols) < need_cols:
            cols = cols + [""] * (need_cols - len(cols))

        # 단지명 칸에 값이 있으면 갱신, 없으면(빈 칸으로 내려오는 병합 셀 등)
        # 이전에 나온 단지명을 그대로 이어받음. 셀 안에 줄바꿈이 들어있으면
        # (예: "단지명\n(블록 상세)") 제목으로는 첫 줄만 사용한다.
        name_cell = cols[COL_IDX["단지명"]].strip()
        if name_cell:
            last_complex_name = name_cell.replace("\r", "").split("\n")[0].strip()

        try:
            time_deal = _clean_number(cols[COL_IDX["타임특가"]])
            total_before = _clean_number(cols[COL_IDX["전체총합"]])
            promo_final = _clean_number(cols[COL_IDX["프로모션최종가"]])
        except ParseError:
            # 숫자가 아닌 줄(헤더, 안내 문구, 사후점검 안내줄 등)은 조용히 건너뜀
            continue

        try:
            # G열(정가)은 더 이상 화면에 표시하지 않지만 참고용으로 함께 보관
            price = _clean_number(cols[COL_IDX["정가"]])
        except ParseError:
            price = time_deal

        row = {
            "complex_name": last_complex_name,
            "pyeong": _clean_unit_text(cols[COL_IDX["평형"]]),
            "area": _clean_unit_text(cols[COL_IDX["전용면적"]]),
            "price": price,
            "time_deal": time_deal,
            "receipt_strike": time_deal + 50000,
            "total_before": total_before,
            "promo_final": promo_final,
        }
        rows.append(row)

    if not rows:
        raise ParseError(
            "표에서 유효한 데이터 행을 찾지 못했습니다. "
            "구글시트에서 헤더(컬럼명) 줄을 빼고 데이터 행만 복사했는지 확인해주세요."
        )

    if not rows[0]["complex_name"]:
        raise ParseError(
            "단지명을 찾지 못했습니다. 데이터 어느 줄에도 A열(단지명)이 채워져 있지 않아요. "
            "최소 한 줄에는 단지명이 들어있어야 합니다."
        )

    return rows
