import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Tuple

import altair as alt
import pandas as pd
import streamlit as st

# --------- 設定値 ---------
# デフォルトはアプリと同じディレクトリ配下の jmadata
DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "jmadata"
MAPPING_MD = Path("station_code_mapping.md")
YEAR = 2026
DATE_MIN = date(YEAR, 1, 1)
DATE_MAX = date(YEAR, 12, 31)


# --------- データ読み込みユーティリティ ---------
@st.cache_data(show_spinner=False)
def load_station_mapping() -> Dict[str, str]:
    """station_code_mapping.md に含まれる JSON を辞書として読み込む。"""
    text = MAPPING_MD.read_text(encoding="utf-8")
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("station_code_mapping.md から JSON を抽出できません。")
    return json.loads(text[start : end + 1])


def list_available_stations(data_dir_str: str) -> List[Tuple[str, str, Path]]:
    """利用可能なステーションの (name, code, path) のリストを返す。"""
    mapping = load_station_mapping()
    stations: List[Tuple[str, str, Path]] = []
    pattern = re.compile(rf"^{YEAR}_(?P<code>.{{2}})\.txt$")
    data_dir = Path(data_dir_str).expanduser().resolve()
    for path in data_dir.glob(f"{YEAR}_*.txt"):
        m = pattern.match(path.name)
        if not m:
            continue
        code = m.group("code")
        name = mapping.get(code, f"コード未定義 ({code})")
        stations.append((name, code, path))
    return sorted(stations, key=lambda x: x[0])


def _parse_time(raw: str) -> str:
    """4 桁の HHMM（空白は 0 とみなす）を HH:MM 文字列にする。"""
    digits = "".join(ch if ch.isdigit() else "0" for ch in raw)
    if digits == "9999":
        return ""
    return f"{digits[:2]}:{digits[2:]}"


def _parse_height(raw: str) -> int:
    """潮位の 3 桁整数を返す。999 は欠損。"""
    raw = raw.strip()
    if raw == "999":
        return None  # type: ignore[return-value]
    return int(raw)


def parse_tide_line(line: str) -> Dict:
    """TXT の 1 行（1 日分）を辞書に変換する。仕様は tide_txt_format_spec.md に従う。"""
    hourly_raw = line[0:72]
    date_str = line[72:78].replace(" ", "0")  # 空白が入る場合は 0 で埋める
    station_code = line[78:80]
    high_raw = line[80:108]
    low_raw = line[108:136]

    hourly = [int(hourly_raw[i : i + 3].strip()) for i in range(0, 72, 3)]
    yy, mm, dd = date_str[0:2], date_str[2:4], date_str[4:6]
    parsed_date = date(2000 + int(yy), int(mm), int(dd))

    def parse_tides(raw: str):
        tides = []
        for i in range(0, 28, 7):
            time_raw = raw[i : i + 4]
            height_raw = raw[i + 4 : i + 7]
            time_fmt = _parse_time(time_raw)
            height = _parse_height(height_raw)
            if not time_fmt or height is None:
                continue
            tides.append({"time": time_fmt, "height_cm": height})
        return tides

    return {
        "date": parsed_date,
        "station_code": station_code,
        "hourly": hourly,
        "high_tides": parse_tides(high_raw),
        "low_tides": parse_tides(low_raw),
    }


def load_day_data(path: Path, target_date: date) -> Dict:
    """ファイルから指定日付のデータを検索して返す。見つからなければ None。"""
    yy = f"{target_date.year - 2000:02d}"
    mm = f"{target_date.month:02d}"
    dd = f"{target_date.day:02d}"
    needle = yy + mm + dd

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if len(line) < 80:
                continue
            day_raw = line[72:78].replace(" ", "0")
            if day_raw == needle:
                return parse_tide_line(line.rstrip("\n"))
    return None


# --------- UI ---------
st.set_page_config(page_title="潮汐検索 2026", page_icon="🌊", layout="centered")
st.title("2026年 潮汐情報検索")
st.caption("jmadata 配布の 2026 年潮汐データをローカル参照します。")

st.markdown(
    "- デプロイ時は **リポジトリに jmadata フォルダごと同梱** してください。アプリと同じ階層に置けば自動で読み込みます。\n"
    "- ローカル開発で別パスに置いた場合のみ、下のチェックを入れてパスを指定してください。"
)

use_custom_path = st.checkbox("ローカル開発でデータパスを指定する", value=False)
if use_custom_path:
    data_dir_input = st.text_input(
        "データフォルダ（jmadata を配置した場所）",
        value=str(DEFAULT_DATA_DIR),
        help="例: ./jmadata / C:\\data\\jmadata",
    )
    data_dir = Path(data_dir_input.strip()).expanduser().resolve()
else:
    data_dir = DEFAULT_DATA_DIR.resolve()

path_exists = data_dir.exists()
stations = list_available_stations(str(data_dir)) if path_exists else []

with st.expander("診断情報 (パス確認)", expanded=False):
    st.write(f"解決後パス: {data_dir}")
    st.write(f"存在するか: {path_exists}")
    sample_txt = sorted([p.name for p in data_dir.glob('*.txt')])[:5] if path_exists else []
    st.write(f"TXT サンプル: {sample_txt}")
    st.write(f"読み取れたステーション数: {len(stations)}")

if not path_exists:
    st.error(f"パスが存在しません: {data_dir}")
    st.stop()

if not stations:
    st.error("jmadata に対象ファイルが見つかりません。")
    st.info("データフォルダのパスを確認してください。TXT を含むフォルダを指定すると再読み込みします。")
    st.stop()

station_name_to_code = {name: code for name, code, _ in stations}
station_names = list(station_name_to_code.keys())
default_idx = station_names.index("東京") if "東京" in station_names else 0

col1, col2 = st.columns([2, 1])
with col1:
    selected_station = st.selectbox("地点", station_names, index=default_idx)
with col2:
    selected_date = st.date_input(
        "日付 (2026 年のみ)", value=DATE_MIN, min_value=DATE_MIN, max_value=DATE_MAX
    )

if st.button("検索"):
    code = station_name_to_code[selected_station]
    path = data_dir / f"{YEAR}_{code}.txt"
    if not path.exists():
        st.error(f"データファイルが存在しません: {path}")
        st.info("「データフォルダ」入力欄で正しいパスを指定してください。")
        st.stop()

    data = load_day_data(path, selected_date)
    if not data:
        st.warning("該当日のデータが見つかりませんでした。")
        st.stop()

    st.subheader(f"{selected_station} の潮汐 ({selected_date})")

    # 24 時間の潮位テーブル
    hourly_df = pd.DataFrame(
        {"時刻": list(range(24)), "潮位 (cm)": data["hourly"]},
    )
    st.dataframe(hourly_df, hide_index=True, use_container_width=True)

    # 満潮・干潮テーブル
    extremes = []
    for e in data["high_tides"]:
        extremes.append({"種別": "満潮", "時刻": e["time"], "潮位 (cm)": e["height_cm"]})
    for e in data["low_tides"]:
        extremes.append({"種別": "干潮", "時刻": e["time"], "潮位 (cm)": e["height_cm"]})
    if extremes:
        st.dataframe(pd.DataFrame(extremes), hide_index=True, use_container_width=True)
    else:
        st.info("満潮・干潮データはありません。")

    # グラフ描画
    hourly_df["時刻"] = hourly_df["時刻"].apply(
        lambda h: datetime.combine(selected_date, datetime.min.time()).replace(hour=h)
    )
    line = (
        alt.Chart(hourly_df)
        .mark_line(point=True, color="#1f77b4")
        .encode(x="時刻:T", y="潮位 (cm):Q")
    )

    layers = [line]
    if extremes:
        extremes_df = pd.DataFrame(extremes)
        extremes_df["時刻"] = extremes_df["時刻"].apply(
            lambda t: datetime.combine(
                selected_date,
                datetime.strptime(t, "%H:%M").time(),
            )
        )
        scatter = (
            alt.Chart(extremes_df)
            .mark_point(filled=True, size=80, color="#d62728")
            .encode(x="時刻:T", y="潮位 (cm):Q", shape="種別:N")
        )
        layers.append(scatter)

    chart = alt.layer(*layers).properties(width=700, height=400)
    st.altair_chart(chart, use_container_width=True)

st.divider()
st.caption("データソース: jmadata (TXT 原本をそのまま使用)")
