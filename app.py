import streamlit as st
import random
from datetime import datetime, timedelta
import csv
import io

# Page config
st.set_page_config(
    page_title="Smart Farm Calculator",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with your background + white text outside boxes
st.markdown("""
<style>
    /* Background image */
    .stApp {
        background-image: url("https://i.postimg.cc/LXKLTyHb/0d6c7a347198fcd057634a3dba8a8526.jpg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }

    .stApp > header {
        background-color: transparent;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: rgba(232, 245, 233, 0.97) !important;
        border-right: 2px solid #a5d6a7;
    }

    /* Metric cards - solid white */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.96) !important;
        padding: 18px 15px;
        border-radius: 12px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.12);
        border: 1px solid #c8e6c9;
    }

    /* Titles - strong green with white glow */
    h1 {
        color: #1b5e20 !important;
        font-weight: 800 !important;
        text-shadow: 0 2px 4px rgba(255,255,255,0.95), 0 0 8px rgba(255,255,255,0.7) !important;
    }

    h2, h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.7) !important;
    }

    /* Plain text outside boxes → WHITE */
    p, .stMarkdown, .stCaption, .stWrite {
        color: #ffffff !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.8) !important;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 2.8em;
        font-weight: 600;
        background-color: #2e7d32 !important;
        color: white !important;
        border: none;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }
    .stButton > button:hover {
        background-color: #1b5e20 !important;
        color: white !important;
    }

    /* Tables */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        background-color: rgba(255,255,255,0.97) !important;
    }

    /* Alerts and info boxes */
    .stAlert, div[data-testid="stAlert"] {
        background-color: rgba(255,255,255,0.95) !important;
        border-radius: 10px;
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background-color: rgba(255,255,255,0.95) !important;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🌾 Smart Farm Calculator")
st.caption("Water • Energy • Temperature • Cost Analysis")
st.markdown("---")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### 📋 Farm Details")
    farm_name = st.text_input("Farm name", value="My Farm")
    crop_name = st.text_input("Crop", value="Maize")
    field_size = st.number_input("Field size (acres)", min_value=0.1, value=5.0, step=0.1)

    st.markdown("### ⚙️ Pump Settings")
    pump_type = st.selectbox("Energy source", ["Electrical", "Solar", "Hybrid"])
    pump_power_kw = st.number_input("Power rating (kW)", min_value=0.1, value=2.2, step=0.1)
    flow_rate = st.number_input("Flow rate (L/min)", min_value=1.0, value=50.0, step=1.0)

    st.markdown("### 💰 Energy Cost")
    electricity_price = st.number_input("Electricity price ($/kWh)", min_value=0.0, value=0.15, step=0.01)
    
    if pump_type == "Hybrid":
        solar_percentage = st.slider("Solar contribution (%)", 0, 100, 70)
    else:
        solar_percentage = 100 if pump_type == "Solar" else 0

    st.markdown("### ⏱️ Pump Runs")
    entry_mode = st.radio("Entry mode", ["Manual", "Automatic"], horizontal=True)

    pump_records = []
    
    if entry_mode == "Manual":
        number_of_runs = st.number_input("Number of runs", min_value=1, max_value=8, value=1)
        
        for i in range(int(number_of_runs)):
            with st.expander(f"Run #{i+1}", expanded=(i==0)):
                c1, c2 = st.columns(2)
                start = c1.text_input("Start (HH:MM)", value="06:00", key=f"s_{i}")
                end = c2.text_input("End (HH:MM)", value="08:00", key=f"e_{i}")
                
                try:
                    start_dt = datetime.strptime(start, "%H:%M")
                    end_dt = datetime.strptime(end, "%H:%M")
                    if end_dt < start_dt:
                        end_dt += timedelta(days=1)
                    runtime = (end_dt - start_dt).total_seconds() / 3600
                    pump_records.append({
                        "run": i+1, "start": start, "end": end, "runtime": runtime
                    })
                except:
                    st.error("Use HH:MM format")
    else:
        number_of_runs = st.number_input("Number of runs", min_value=1, max_value=8, value=2)
        min_rt = st.number_input("Min hours", value=1.0, step=0.5)
        max_rt = st.number_input("Max hours", value=3.0, step=0.5)
        
        for i in range(int(number_of_runs)):
            runtime = round(random.uniform(min_rt, max_rt), 2)
            pump_records.append({
                "run": i+1, "start": "Auto", "end": "Auto", "runtime": runtime
            })

    st.markdown("### 🌡️ Temperature")
    temp_mode = st.radio("Mode", ["Manual", "Automatic"], horizontal=True, key="temp_mode")
    
    temperature_hours = ["06:00", "09:00", "12:00", "15:00", "18:00"]
    temperature_records = []
    
    if temp_mode == "Manual":
        for hour in temperature_hours:
            temp = st.number_input(f"{hour}", value=25.0, key=f"t_{hour}")
            temperature_records.append({"time": hour, "temperature": temp})
    else:
        min_t = st.number_input("Min °C", value=18.0)
        max_t = st.number_input("Max °C", value=35.0)
        for hour in temperature_hours:
            temp = round(random.uniform(min_t, max_t), 1)
            temperature_records.append({"time": hour, "temperature": temp})

    st.markdown("### 💧 Irrigation Target")
    required_water = st.number_input("Required water today (L)", min_value=0.0, value=5000.0, step=100.0)

# ==================== CALCULATIONS ====================
total_runtime = sum(r["runtime"] for r in pump_records) if pump_records else 0
water_per_hour = flow_rate * 60
total_water = total_runtime * water_per_hour
total_energy = total_runtime * pump_power_kw

electrical_energy = total_energy * (100 - solar_percentage) / 100
solar_energy = total_energy * solar_percentage / 100
electricity_cost = electrical_energy * electricity_price

temps = [r["temperature"] for r in temperature_records] if temperature_records else [0]
avg_temp = sum(temps) / len(temps)
max_temp = max(temps)
min_temp = min(temps)

hottest = max(temperature_records, key=lambda x: x["temperature"]) if temperature_records else {"time": "-", "temperature": 0}
coolest = min(temperature_records, key=lambda x: x["temperature"]) if temperature_records else {"time": "-", "temperature": 0}

ratio = (total_water / required_water * 100) if required_water > 0 else 0
if ratio > 120:
    status = "Possible over-irrigation"
elif ratio >= 90:
    status = "Within target range"
else:
    status = "Possible under-irrigation"

# ==================== MAIN CONTENT ====================
st.subheader("📊 Today's Key Results")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Water Used", f"{total_water:,.0f} L")
m2.metric("Energy Used", f"{total_energy:.2f} kWh")
m3.metric("Est. Cost", f"${electricity_cost:.2f}")
m4.metric("Runtime", f"{total_runtime:.2f} hrs")

st.markdown("")

st.markdown("### 🏡 Farm Summary")
st.info(f"""
**Farm:** {farm_name}  
**Crop:** {crop_name} • **Size:** {field_size} acres  
**Pump:** {pump_type} • {pump_power_kw} kW • {flow_rate} L/min  
**Irrigation Status:** {status} ({ratio:.1f}% of target)
""")

st.markdown("### 🌡️ Temperature Overview")
t1, t2, t3 = st.columns(3)
t1.metric("Average", f"{avg_temp:.1f} °C")
t2.metric("Highest", f"{max_temp:.1f} °C")
t3.metric("Lowest", f"{min_temp:.1f} °C")

st.write(f"**Hottest:** {hottest['time']} ({hottest['temperature']:.1f}°C)  •  **Coolest:** {coolest['time']} ({coolest['temperature']:.1f}°C)")

HIGH, LOW = 32, 15
alerts = []
for r in temperature_records:
    if r["temperature"] >= HIGH:
        alerts.append(f"⚠️ High temperature at {r['time']}: **{r['temperature']:.1f}°C**")
    elif r["temperature"] <= LOW:
        alerts.append(f"⚠️ Low temperature at {r['time']}: **{r['temperature']:.1f}°C**")

if alerts:
    st.warning("Temperature Alerts")
    for a in alerts:
        st.markdown(a)
else:
    st.success("✓ No temperature alerts — all readings normal")

st.markdown("### 🔧 Pump Run Details")
if pump_records:
    table_data = []
    for r in pump_records:
        table_data.append({
            "Run": r["run"],
            "Start": r["start"],
            "End": r["end"],
            "Hours": round(r["runtime"], 2),
            "Water (L)": round(r["runtime"] * water_per_hour, 1),
            "Energy (kWh)": round(r["runtime"] * pump_power_kw, 2)
        })
    st.dataframe(table_data, use_container_width=True, hide_index=True)
else:
    st.info("No pump runs recorded yet.")

st.markdown("### 📅 Temperature Log")
temp_data = []
for r in temperature_records:
    status_t = "HIGH" if r["temperature"] >= HIGH else ("LOW" if r["temperature"] <= LOW else "Normal")
    temp_data.append({
        "Time": r["time"],
        "Temperature (°C)": r["temperature"],
        "Status": status_t
    })
st.dataframe(temp_data, use_container_width=True, hide_index=True)

st.markdown("### 🔮 What-If Simulator")
st.write("See potential savings if you reduce pump runtime:")
reduction = st.slider("Reduce runtime by (%)", 0, 100, 20)

factor = 1 - (reduction / 100)
saved_water = total_water * (1 - factor)
saved_energy = total_energy * (1 - factor)
saved_cost = electricity_cost * (1 - factor)

s1, s2, s3 = st.columns(3)
s1.metric("Water Saved", f"{saved_water:,.0f} L")
s2.metric("Energy Saved", f"{saved_energy:.2f} kWh")
s3.metric("Money Saved", f"${saved_cost:.2f}")

st.markdown("### 📥 Download Reports")
col_a, col_b = st.columns(2)

with col_a:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Timestamp", "Farm", "Crop", "Field Size", "Pump Type", "Power (kW)",
                     "Runtime (h)", "Water (L)", "Energy (kWh)", "Electrical (kWh)",
                     "Solar (kWh)", "Cost ($)", "Avg Temp", "Max Temp", "Min Temp",
                     "Required Water", "Ratio %", "Status"])
    writer.writerow([
        datetime.now().strftime("%Y-%m-%d %H:%M"), farm_name, crop_name, field_size,
        pump_type, pump_power_kw, round(total_runtime,2), round(total_water,1),
        round(total_energy,2), round(electrical_energy,2), round(solar_energy,2),
        round(electricity_cost,2), round(avg_temp,1), round(max_temp,1), round(min_temp,1),
        round(required_water,1), round(ratio,1), status
    ])
    st.download_button("📄 Download Full Farm Report", buffer.getvalue(),
                       file_name="farm_report.csv", mime="text/csv", use_container_width=True)

with col_b:
    buffer2 = io.StringIO()
    writer2 = csv.writer(buffer2)
    writer2.writerow(["Date", "Farm", "Time", "Temperature (°C)"])
    for r in temperature_records:
        writer2.writerow([datetime.now().strftime("%Y-%m-%d"), farm_name, r["time"], r["temperature"]])
    st.download_button("🌡️ Download Temperature Log", buffer2.getvalue(),
                       file_name="temperature_log.csv", mime="text/csv", use_container_width=True)

st.markdown("---")
st.caption("Smart Farm Calculator • Designed for mobile • Ready for future sensor integration")
