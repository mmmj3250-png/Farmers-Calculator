import streamlit as st
import random
from datetime import datetime, timedelta
import csv
import io
import pandas as pd
import plotly.express as px
from fpdf import FPDF

st.set_page_config(
    page_title="Smart Farm Calculator",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== SESSION STATE ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "farms" not in st.session_state:
    st.session_state.farms = {"My Farm": {}}
if "current_farm" not in st.session_state:
    st.session_state.current_farm = "My Farm"
if "history" not in st.session_state:
    st.session_state.history = []
if "theme" not in st.session_state:
    st.session_state.theme = "Light"

# ====================== CROP RECOMMENDATIONS ======================
CROP_RECOMMENDATIONS = {
    "Maize": {
        "ideal_temp": "18–32°C",
        "water_need": "High during flowering",
        "tip": "Avoid water stress during tasseling stage."
    },
    "Beans": {
        "ideal_temp": "15–25°C",
        "water_need": "Moderate",
        "tip": "Sensitive to waterlogging. Ensure good drainage."
    },
    "Tomatoes": {
        "ideal_temp": "20–30°C",
        "water_need": "Consistent moisture",
        "tip": "Irregular watering causes fruit cracking."
    },
    "Wheat": {
        "ideal_temp": "15–25°C",
        "water_need": "Moderate",
        "tip": "Critical water need during flowering and grain filling."
    },
    "Cabbage": {
        "ideal_temp": "15–20°C",
        "water_need": "High and regular",
        "tip": "Keep soil consistently moist for good head formation."
    },
    "Other": {
        "ideal_temp": "Varies",
        "water_need": "Check crop guide",
        "tip": "Monitor soil moisture regularly."
    }
}

# ====================== LOGIN ======================
if not st.session_state.logged_in:
    st.title("🌾 Smart Farm Calculator")
    st.subheader("Login")
    username = st.text_input("Enter your name / farm username")
    if st.button("Login") and username.strip():
        st.session_state.logged_in = True
        st.session_state.username = username.strip()
        st.rerun()
    st.stop()

# ====================== THEME TOGGLE ======================
theme = st.sidebar.radio("Theme", ["Light", "Dark"], index=0 if st.session_state.theme == "Light" else 1)
st.session_state.theme = theme

# Dynamic CSS based on theme
if theme == "Dark":
    bg_color = "#1e1e1e"
    text_color = "#ffffff"
    card_bg = "rgba(40,40,40,0.95)"
    sidebar_bg = "rgba(30,40,30,0.97)"
else:
    bg_color = "transparent"
    text_color = "#1a1a1a"
    card_bg = "rgba(255,255,255,0.97)"
    sidebar_bg = "rgba(232,245,233,0.97)"

st.markdown(f"""
<style>
    .stApp {{
        background-image: url("https://i.postimg.cc/ZqdBQrn9/Farmers.jpg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
    }}
    div[data-testid="stMetric"] {{
        background-color: {card_bg} !important;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #a5d6a7;
    }}
    h1, h2, h3 {{
        color: {"#ffffff" if theme=="Dark" else "#1b5e20"} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ====================== SIDEBAR ======================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.username}")
    
    st.markdown("### 🚜 Farms")
    farm_names = list(st.session_state.farms.keys())
    selected_farm = st.selectbox("Select Farm", farm_names, index=farm_names.index(st.session_state.current_farm))
    st.session_state.current_farm = selected_farm

    new_farm = st.text_input("Add new farm")
    if st.button("➕ Add Farm") and new_farm.strip():
        if new_farm not in st.session_state.farms:
            st.session_state.farms[new_farm] = {}
            st.session_state.current_farm = new_farm
            st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Farm Details")
    farm_name = st.text_input("Farm name", value=selected_farm)
    crop_name = st.selectbox("Crop", list(CROP_RECOMMENDATIONS.keys()), index=0)
    field_size = st.number_input("Field size (acres)", min_value=0.1, value=5.0, step=0.1)

    st.markdown("### ⚙️ Pump Settings")
    pump_type = st.selectbox("Energy source", ["Electrical", "Solar", "Hybrid"])
    pump_power_kw = st.number_input("Power (kW)", min_value=0.1, value=2.2, step=0.1)
    flow_rate = st.number_input("Flow rate (L/min)", min_value=1.0, value=50.0, step=1.0)

    st.markdown("### 💰 Costs")
    electricity_price = st.number_input("Electricity ($/kWh)", min_value=0.0, value=0.15, step=0.01)
    fertilizer_cost = st.number_input("Fertilizer cost ($)", min_value=0.0, value=0.0, step=1.0)

    solar_percentage = 100 if pump_type == "Solar" else (0 if pump_type == "Electrical" else st.slider("Solar %", 0, 100, 70))

    st.markdown("### ⏱️ Pump Runs")
    entry_mode = st.radio("Mode", ["Manual", "Automatic"], horizontal=True)
    pump_records = []

    if entry_mode == "Manual":
        n_runs = st.number_input("Number of runs", 1, 8, 1)
        for i in range(int(n_runs)):
            with st.expander(f"Run {i+1}"):
                c1, c2 = st.columns(2)
                start = c1.text_input("Start", "06:00", key=f"s{i}")
                end = c2.text_input("End", "08:00", key=f"e{i}")
                try:
                    s = datetime.strptime(start, "%H:%M")
                    e = datetime.strptime(end, "%H:%M")
                    if e < s: e += timedelta(days=1)
                    runtime = (e - s).total_seconds() / 3600
                    pump_records.append({"run": i+1, "start": start, "end": end, "runtime": runtime})
                except:
                    st.error("Use HH:MM")
    else:
        n_runs = st.number_input("Runs", 1, 8, 2)
        min_rt = st.number_input("Min hrs", 1.0, step=0.5)
        max_rt = st.number_input("Max hrs", 3.0, step=0.5)
        for i in range(int(n_runs)):
            rt = round(random.uniform(min_rt, max_rt), 2)
            pump_records.append({"run": i+1, "start": "Auto", "end": "Auto", "runtime": rt})

    st.markdown("### 🌡️ Temperature")
    temp_mode = st.radio("Temp Mode", ["Manual", "Automatic"], horizontal=True, key="tm")
    hours = ["06:00", "09:00", "12:00", "15:00", "18:00"]
    temperature_records = []
    if temp_mode == "Manual":
        for h in hours:
            t = st.number_input(h, value=25.0, key=f"t{h}")
            temperature_records.append({"time": h, "temperature": t})
    else:
        min_t = st.number_input("Min °C", 18.0)
        max_t = st.number_input("Max °C", 35.0)
        for h in hours:
            t = round(random.uniform(min_t, max_t), 1)
            temperature_records.append({"time": h, "temperature": t})

    st.markdown("### 💧 Water & Rain")
    required_water = st.number_input("Required water (L)", 0.0, value=5000.0, step=100.0)
    rainfall = st.number_input("Rainfall (mm)", 0.0, value=0.0, step=0.5)

    notes = st.text_area("Notes")

# ====================== CALCULATIONS ======================
total_runtime = sum(r["runtime"] for r in pump_records) if pump_records else 0
water_per_hour = flow_rate * 60
total_water = total_runtime * water_per_hour
total_energy = total_runtime * pump_power_kw
electrical_energy = total_energy * (100 - solar_percentage) / 100
solar_energy = total_energy * solar_percentage / 100
electricity_cost = electrical_energy * electricity_price
total_cost = electricity_cost + fertilizer_cost

temps = [r["temperature"] for r in temperature_records] or [0]
avg_temp = sum(temps)/len(temps)
max_temp = max(temps)
min_temp = min(temps)

ratio = (total_water / required_water * 100) if required_water > 0 else 0
if ratio > 120:
    status, efficiency = "Over-irrigation", "Poor"
elif ratio >= 90:
    status, efficiency = "On target", "Good"
else:
    status, efficiency = "Under-irrigation", "Average"

water_per_acre = total_water / field_size if field_size else 0
cost_per_litre = total_cost / total_water if total_water else 0

# ====================== SAVE TO HISTORY ======================
if st.sidebar.button("💾 Save This Calculation"):
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "farm": farm_name,
        "crop": crop_name,
        "water": round(total_water,1),
        "energy": round(total_energy,2),
        "cost": round(total_cost,2),
        "efficiency": efficiency,
        "notes": notes
    }
    st.session_state.history.insert(0, record)
    st.success("Saved to history!")

# ====================== MAIN PAGE ======================
st.title(f"🌾 {farm_name}")
st.caption(f"Logged in as **{st.session_state.username}**")

# Key Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Water Used", f"{total_water:,.0f} L")
m2.metric("Energy", f"{total_energy:.2f} kWh")
m3.metric("Total Cost", f"${total_cost:.2f}")
m4.metric("Efficiency", efficiency)

m5, m6, m7, m8 = st.columns(4)
m5.metric("Water/Acre", f"{water_per_acre:,.0f} L")
m6.metric("Cost/Litre", f"${cost_per_litre:.4f}")
m7.metric("Runtime", f"{total_runtime:.2f} h")
m8.metric("Rainfall", f"{rainfall} mm")

# Crop Recommendation
rec = CROP_RECOMMENDATIONS.get(crop_name, CROP_RECOMMENDATIONS["Other"])
st.info(f"**{crop_name} Recommendation**  \nIdeal Temp: {rec['ideal_temp']}  \nWater Need: {rec['water_need']}  \nTip: {rec['tip']}")

# Charts
st.subheader("📈 Charts")
col1, col2 = st.columns(2)

with col1:
    if temperature_records:
        df_temp = pd.DataFrame(temperature_records)
        fig = px.line(df_temp, x="time", y="temperature", markers=True, title="Temperature Over Time")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    df_bar = pd.DataFrame({
        "Metric": ["Water (×1000 L)", "Energy (kWh)", "Cost ($)"],
        "Value": [total_water/1000, total_energy, total_cost]
    })
    fig2 = px.bar(df_bar, x="Metric", y="Value", title="Water vs Energy vs Cost")
    st.plotly_chart(fig2, use_container_width=True)

# History
st.subheader("📜 Calculation History")
if st.session_state.history:
    hist_df = pd.DataFrame(st.session_state.history)
    st.dataframe(hist_df, use_container_width=True, hide_index=True)
else:
    st.info("No saved calculations yet. Click 'Save This Calculation' in the sidebar.")

# PDF Export
st.subheader("📄 Export PDF Report")
if st.button("Generate PDF Report"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(0, 10, f"Smart Farm Report - {farm_name}", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 8, f"User: {st.session_state.username}", ln=True)
    pdf.cell(0, 8, f"Crop: {crop_name}", ln=True)
    pdf.cell(0, 8, f"Water Used: {total_water:,.0f} L", ln=True)
    pdf.cell(0, 8, f"Energy: {total_energy:.2f} kWh", ln=True)
    pdf.cell(0, 8, f"Total Cost: ${total_cost:.2f}", ln=True)
    pdf.cell(0, 8, f"Efficiency: {efficiency}", ln=True)
    pdf.cell(0, 8, f"Status: {status}", ln=True)
    if notes:
        pdf.multi_cell(0, 8, f"Notes: {notes}")
    
    pdf_output = pdf.output(dest="S").encode("latin-1")
    st.download_button("⬇️ Download PDF", pdf_output, file_name=f"farm_report_{farm_name}.pdf", mime="application/pdf")

st.markdown("---")
st.caption("Smart Farm Calculator • Multi-farm • History • PDF Export • Crop Tips")
