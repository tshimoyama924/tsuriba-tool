from datetime import date
import streamlit as st
import requests
API_KEY = "YOUR_WORLD_TIDES_API_KEY"

st.title("釣り場ツール（テスト版A）")

# -------- 入力エリア --------
st.header("条件の入力")

SPOTS = {
    "若洲海浜公園": {"lat": 35.628, "lon": 139.864},
    "検見川浜東突堤": {"lat": 35.634, "lon": 140.062},
    "塩浜三番瀬公園": {"lat": 35.682, "lon": 139.944},
    "東扇島西公園": {"lat": 35.515, "lon": 139.758},
}

spot_name = st.selectbox("釣り場を選択してください", list(SPOTS.keys()))
fish_date = st.date_input("日付を選択してください", value=date.today())
mode = st.radio("表示する情報", ["潮汐のみ", "天気のみ", "両方"], horizontal=True)

search = st.button("この条件で検索")

st.divider()
st.header("検索結果（テスト用）")


# -------- ここをあとでAPI実装に差し替える --------



def fetch_tide(spot_name, d):
    lat = SPOTS[spot_name]["lat"]
    lon = SPOTS[spot_name]["lon"]

    date_str = d.strftime("%Y-%m-%d")

    url = (
        "https://www.worldtides.info/api/v3?"
        f"extremes&lat={lat}&lon={lon}&date={date_str}&key={API_KEY}"
    )

    r = requests.get(url)
    data = r.json()

    if "extremes" not in data:
        return [{"時刻": "-", "潮位（cm）": "-", "種類": "-"}]

    result = []
    for e in data["extremes"]:
        result.append({
            "時刻": e["date"],
            "潮位（cm）": e["height"],
            "種類": "満潮" if e["type"] == "High" else "干潮",
        })

    return result



def fetch_weather(spot: str, d: date):
    return {
        "天気": "晴れ（テスト）",
        "最高気温": "15℃",
        "最低気温": "8℃",
        "風": "北風 3m/s",
    }
# ----------------------------------------------


if search:
    st.write(f"選択した釣り場：**{spot_name}**")
    st.write(f"選択した日付：**{fish_date}**")

    if mode in ("潮汐のみ", "両方"):
        st.subheader("潮汐")
        st.table(fetch_tide(spot_name, fish_date))

    if mode in ("天気のみ", "両方"):
        st.subheader("天気")
        w = fetch_weather(spot_name, fish_date)
        for k, v in w.items():
            st.write(f"- {k}: {v}")

    st.caption
