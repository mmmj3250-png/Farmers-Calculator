import streamlit as st
import random
from datetime import datetime, timedelta
import csv
import io
import pandas as pd

st.set_page_config(
    page_title="Smart Farm Calculator",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== CSS ======================
st.markdown("""
<style>
    .stApp {
        background-image: url("https://i.postimg.cc/ZqdBQrn9/Farmers.jpg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }
    .stApp > header { background-color: transparent; }

    section[data-testid="stSidebar"] {
        background-color: rgba(232, 245, 233, 0.97) !important;
        border-right: 2px solid #81c784;
    }

    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.97) !important;
        padding: 16px 12px;
        border-radius: 12px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.15);
        border: 1px solid #a5d6a7;
    }

    h1 {
        color: #1b5e20 !important;
        font-weight: 800 !important;
        -webkit-text-stroke: 0.6px #ffffff;
    }
    h2, h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
        -webkit-text-stroke: 0.5px #1b5e20;
    }
    .stMarkdown p, .stCaption {
        color: #ffffff !important;
        -webkit-text-stroke: 0.3px #1b5e20;
    }

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 2.8em;
        font-weight: 600;
        background-color: #2e7d32 !important;
        color: white !important;
        border: none;
    }
    .stDataFrame {
        background-color: rgba(255,255,255,0.97) !important;
        border-radius: 10px;
    }
    .stAlert {
        background-color: rgba(255,255,255,0.96) !important;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ====================== TITLE ======================
st.title("🌾 Smart Farm Calculator")
st.caption("Water • Energy • Temperature • Cost Analysis • Efficiency")
st.markdown("---")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.markdown("### 📋 Farm Details")
    farm_name = st.text_input("Farm name", value="My Farm")
    crop_name = st.text_input("Crop", value="Maize")
    field_size = st.number_input("Field size (acres)", min_value=0.1, value=5.0, step=0.1)

    st.markdown("### ⚙️ Pump Settings")
    pump_type = st.selectbox("Energy source", ["Electrical", "Solar", "Hybrid"])
    pump_power_kw = st.number_input("Power rating (kW)", min_value=0.1, value=2.2, step=0.1)
    flow_rate = st.number_input("Flow rate (L/min)", min_value=1.0, value=50.0, step=1.0)

    st.markdown("### 💰 Costs")
    electricity_price = st.number_input("Electricity price ($/kWh)", min_value=0.0, value=0.15, step=0.01)
    fertilizer_cost = st.number_input("Fertilizer / Chemical cost today ($)", min_value=0.0, value=0.0, step=1.0)

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
                    pump_records.append({"run": i+1, "start": start, "end": end, "runtime": runtime})
                except:
                    st.error("Use HH:MM format")
    else:
        number_of_runs = st.number_input("Number of runs", min_value=1, max_value=8, value=2)
        min_rt = st.number_input("Min hours", value=1.0, step=0.5)
        max_rt = st.number_input("Max hours", value=3.0, step=0.5)
        for i in range(int(number_of_runs)):
            runtime = round(random.uniform(min_rt, max_rt), 2)
            pump_records.append({"run": i+1, "start": "Auto", "end": "Auto", "runtime": runtime})

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

    st.markdown("### 💧 Water & Rain")
    required_water = st.number_input("Required water today (L)", min_value=0.0, value=5000.0, step=100.0)
    rainfall = st.number_input("Rainfall today (mm)", min_value=0.0, value=0.0, step=0.5,
                              help="Rain reduces the need for irrigation")

    st.markdown("### 📝 Notes")
    notes = st.text_area("Additional notes (appears in report)", height=80)

    if st.button("🔄 Reset All Inputs"):
        st.rerun()

# ====================== CALCULATIONS ======================
total_runtime = sum(r["runtime"] for r in pump_records) if pump_records else 0
water_per_hour = flow_rate * 60
total_water = total_runtime * water_per_hour
total_energy = total_runtime * pump_power_kw

electrical_energy = total_energy * (100 - solar_percentage) / 100
solar_energy = total_energy * solar_percentage / 100
electricity_cost = electrical_energy * electricity_price
total_cost = electricity_cost + fertilizer_cost

# Adjusted water need after rainfall (simple estimation)
effective_required = max(0, required_water - (rainfall * field_size * 1000 * 0.7))  # rough conversion

temps = [r["temperature"] for r in temperature_records] if temperature_records else [0]
avg_temp = sum(temps) / len(temps) if temps else 0
max_temp = max(temps) if temps else 0
min_temp = min(temps) if temps else 0

hottest = max(temperature_records, key=lambda x: x["temperature"]) if temperature_records else {"time": "-", "temperature": 0}
coolest = min(temperature_records, key=lambda x: x["temperature"]) if temperature_records else {"time": "-", "temperature": 0}

ratio = (total_water / effective_required * 100) if effective_required > 0 else 0
if ratio > 120:
    status = "Possible over-irrigation"
    efficiency = "Poor"
elif ratio >= 90:
    status = "Within target range"
    efficiency = "Good"
else:
    status = "Possible under-irrigation"
    efficiency = "Average"

water_per_acre = total_water / field_size if field_size > 0 else 0
cost_per_litre = total_cost / total_water if total_water > 0 else 0

# Projections
daily_cost = total_cost
weekly_cost = total_cost * 7
monthly_cost = total_cost * 30

# ====================== MAIN DISPLAY ======================
st.subheader("📊 Today's Key Results")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Water Used", f"{total_water:,.0f} L")
c2.metric("Energy Used", f"{total_energy:.2f} kWh")
c3.metric("Total Cost", f"${total_cost:.2f}")
c4.metric("Runtime", f"{total_runtime:.2f} hrs")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Water per Acre", f"{water_per_acre:,.0f} L")
c6.metric("Cost per Litre", f"${cost_per_litre:.4f}")
c7.metric("Efficiency", efficiency)
c8.metric("Rainfall", f"{rainfall} mm")

st.markdown("")

# Farm Summary
st.markdown("### 🏡 Farm Summary")
st.info(f"""
**Farm:** {farm_name}  
**Crop:** {crop_name} • **Size:** {field_size} acres  
**Pump:** {pump_type} • {pump_power_kw} kW • {flow_rate} L/min  
**Irrigation Status:** {status} ({ratio:.1f}% of adjusted target)  
**Notes:** {notes if notes else "None"}
""")

# Temperature
st.markdown("### 🌡️ Temperature Overview")
t1, t2, t3 = st.columns(3)
t1.metric("Average", f"{avg_temp:.1f} °C")
t2.metric("Highest", f"{max_temp:.1f} °C")
t3.metric("Lowest", f"{min_temp:.1f} °C")

st.write(f"**Hottest:** {hottest['time']} ({hottest['temperature']:.1f}°C)  •  **Coolest:** {coolest['time']} ({coolest['temperature']:.1f}°C)")

# Alerts
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

# Charts
st.markdown("### 📈 Charts")
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    if temperature_records:
        temp_df = pd.DataFrame(temperature_records)
        st.bar_chart(temp_df.set_index("time")["temperature"], use_container_width=True)
        st.caption("Temperature during the day")

with col_chart2:
    chart_data = pd.DataFrame({
        "Metric": ["Water (1000 L)", "Energy (kWh)"],
        "Value": [total_water/1000, total_energy]
    })
    st.bar_chart(chart_data.set_index("Metric"), use_container_width=True)
    st.caption("Water vs Energy")

# Cost Projections
st.markdown("### 📅 Cost Projections")
p1, p2, p3 = st.columns(3)
p1.metric("Today", f"${daily_cost:.2f}")
p2.metric("This Week (est.)", f"${weekly_cost:.2f}")
p3.metric("This Month (est.)", f"${monthly_cost:.2f}")

# Pump details
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

# Temperature log
st.markdown("### 📅 Temperature Log")
temp_data = []
for r in temperature_records:
    status_t = "HIGH" if r["temperature"] >= HIGH else ("LOW" if r["temperature"] <= LOW else "Normal")
    temp_data.append({"Time": r["time"], "Temperature (°C)": r["temperature"], "Status": status_t})
st.dataframe(temp_data, use_container_width=True, hide_index=True)

# What-If
st.markdown("### 🔮 What-If Simulator")
reduction = st.slider("Reduce runtime by (%)", 0, 100, 20)
factor = 1 - (reduction / 100)

s1, s2, s3 = st.columns(3)
s1.metric("Water Saved", f"{total_water * (1-factor):,.0f} L")
s2.metric("Energy Saved", f"{total_energy * (1-factor):.2f} kWh")
s3.metric("Money Saved", f"${total_cost * (1-factor):.2f}")

# Downloads
st.markdown("### 📥 Download Reports")
col_a, col_b = st.columns(2)

with col_a:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Timestamp", "Farm", "Crop", "Field Size", "Pump Type", "Power (kW)",
                     "Runtime (h)", "Water (L)", "Energy (kWh)", "Electrical (kWh)",
                     "Solar (kWh)", "Electricity Cost", "Fertilizer Cost", "Total Cost",
                     "Water/Acre", "Cost/Litre", "Efficiency", "Rainfall (mm)",
                     "Avg Temp", "Max Temp", "Min Temp", "Status", "Notes"])
    writer.writerow([
        datetime.now().strftime("%Y-%m-%d %H:%M"), farm_name, crop_name, field_size,
        pump_type, pump_power_kw, round(total_runtime,2), round(total_water,1),
        round(total_energy,2), round(electrical_energy,2), round(solar_energy,2),
        round(electricity_cost,2), round(fertilizer_cost,2), round(total_cost,2),
        round(water_per_acre,1), round(cost_per_litre,4), efficiency, rainfall,
        round(avg_temp,1), round(max_temp,1), round(min_temp,1), status, notes
    ])
    st.download_button("📄 Download Full Report", buffer.getvalue(),
                       file_name="farm_full_report.csv", mime="text/csv", use_container_width=True)

with col_b:
    buffer2 = io.StringIO()
    writer2 = csv.writer(buffer2)
    writer2.writerow(["Date", "Farm", "Time", "Temperature (°C)"])
    for r in temperature_records:
        writer2.writerow([datetime.now().strftime("%Y-%m-%d"), farm_name, r["time"], r["temperature"]])
    st.download_button("🌡️ Download Temperature Log", buffer2.getvalue(),
                       file_name="temperature_log.csv", mime="text/csv", use_container_width=True)

st.markdown("---")
st.caption("Smart Farm Calculator • Built for farmers • Ready for future sensor integration")
