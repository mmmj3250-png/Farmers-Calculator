import streamlit as st
import random
from datetime import datetime, timedelta
import csv
import io

# Page configuration
st.set_page_config(
    page_title="Smart Farm Calculator",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better mobile look
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    h1, h2, h3 {
        color: #1b5e20;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌾 Smart Farm Water, Energy & Temperature Calculator")
st.caption("Calculate water use, energy consumption, costs and temperature alerts")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("📋 Farm Information")
    farm_name = st.text_input("Farm name", value="My Farm")
    crop_name = st.text_input("Crop being monitored", value="Maize")
    field_size = st.number_input("Field size (acres)", min_value=0.1, value=5.0, step=0.1)

    st.header("⚙️ Pump Settings")
    pump_type = st.selectbox("Pump energy source", ["Electrical", "Solar", "Hybrid"])
    pump_power_kw = st.number_input("Pump power rating (kW)", min_value=0.1, value=2.2, step=0.1)
    flow_rate = st.number_input("Water flow rate (L/min)", min_value=1.0, value=50.0, step=1.0)

    st.header("💰 Energy Prices")
    electricity_price = st.number_input("Electricity price ($ per kWh)", min_value=0.0, value=0.15, step=0.01)
    
    if pump_type == "Hybrid":
        solar_percentage = st.slider("Solar contribution (%)", 0, 100, 70)
    else:
        solar_percentage = 100 if pump_type == "Solar" else 0

    st.header("⏱️ Pump Operation")
    entry_mode = st.radio("How do you want to enter pump data?", ["Manual", "Automatic"], horizontal=True)

    pump_records = []
    
    if entry_mode == "Manual":
        number_of_runs = st.number_input("How many times did the pump run?", min_value=1, max_value=10, value=1)
        
        for i in range(int(number_of_runs)):
            with st.expander(f"Pump Run #{i+1}", expanded=True):
                col1, col2 = st.columns(2)
                start = col1.text_input("Start time (HH:MM)", value="06:00", key=f"start_{i}")
                end = col2.text_input("End time (HH:MM)", value="08:00", key=f"end_{i}")
                
                try:
                    start_dt = datetime.strptime(start, "%H:%M")
                    end_dt = datetime.strptime(end, "%H:%M")
                    if end_dt < start_dt:
                        end_dt += timedelta(days=1)
                    runtime = (end_dt - start_dt).total_seconds() / 3600
                    pump_records.append({
                        "run": i+1,
                        "start": start,
                        "end": end,
                        "runtime": runtime
                    })
                except:
                    st.error("Please use HH:MM format (example: 06:30)")
    else:
        number_of_runs = st.number_input("Number of automatic runs", min_value=1, max_value=10, value=2)
        min_runtime = st.number_input("Minimum runtime (hours)", value=1.0, step=0.5)
        max_runtime = st.number_input("Maximum runtime (hours)", value=3.0, step=0.5)
        
        for i in range(int(number_of_runs)):
            runtime = round(random.uniform(min_runtime, max_runtime), 2)
            pump_records.append({
                "run": i+1,
                "start": "Automatic",
                "end": "Automatic",
                "runtime": runtime
            })

    st.header("🌡️ Temperature Data")
    temp_mode = st.radio("Temperature entry mode", ["Manual", "Automatic"], horizontal=True)
    
    temperature_hours = ["06:00", "09:00", "12:00", "15:00", "18:00"]
    temperature_records = []
    
    if temp_mode == "Manual":
        for hour in temperature_hours:
            temp = st.number_input(f"Temperature at {hour} (°C)", value=25.0, key=f"temp_{hour}")
            temperature_records.append({"time": hour, "temperature": temp})
    else:
        min_temp = st.number_input("Minimum temperature (°C)", value=18.0)
        max_temp = st.number_input("Maximum temperature (°C)", value=35.0)
        for hour in temperature_hours:
            temp = round(random.uniform(min_temp, max_temp), 1)
            temperature_records.append({"time": hour, "temperature": temp})

    st.header("💧 Irrigation Target")
    required_water = st.number_input("Estimated water required today (litres)", min_value=0.0, value=5000.0, step=100.0)

# ==================== CALCULATIONS ====================
total_runtime = sum(r["runtime"] for r in pump_records) if pump_records else 0
water_per_hour = flow_rate * 60
total_water = total_runtime * water_per_hour
total_energy = total_runtime * pump_power_kw

electrical_energy = total_energy * (100 - solar_percentage) / 100
solar_energy = total_energy * solar_percentage / 100
electricity_cost = electrical_energy * electricity_price

temperatures = [r["temperature"] for r in temperature_records] if temperature_records else [0]
avg_temp = sum(temperatures) / len(temperatures)
max_temp = max(temperatures)
min_temp = min(temperatures)

hottest = max(temperature_records, key=lambda x: x["temperature"]) if temperature_records else {"time": "-", "temperature": 0}
coolest = min(temperature_records, key=lambda x: x["temperature"]) if temperature_records else {"time": "-", "temperature": 0}

irrigation_ratio = (total_water / required_water * 100) if required_water > 0 else 0
if irrigation_ratio > 120:
    irrigation_status = "Possible over-irrigation"
elif irrigation_ratio >= 90:
    irrigation_status = "Within target range"
else:
    irrigation_status = "Possible under-irrigation"

# ==================== MAIN DISPLAY ====================
st.subheader("📊 Key Results")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Water Used", f"{total_water:,.0f} L")
col2.metric("Total Energy", f"{total_energy:.2f} kWh")
col3.metric("Electricity Cost", f"${electricity_cost:.2f}")
col4.metric("Pump Runtime", f"{total_runtime:.2f} h")

st.markdown("---")

# Farm Summary
st.subheader("🏡 Farm Summary")
st.write(f"**Farm:** {farm_name}  |  **Crop:** {crop_name}  |  **Field size:** {field_size} acres")
st.write(f"**Pump type:** {pump_type}  |  **Power:** {pump_power_kw} kW  |  **Flow rate:** {flow_rate} L/min")
st.write(f"**Irrigation status:** {irrigation_status} ({irrigation_ratio:.1f}% of target)")

# Temperature section
st.subheader("🌡️ Temperature Overview")
t1, t2, t3 = st.columns(3)
t1.metric("Average", f"{avg_temp:.1f} °C")
t2.metric("Maximum", f"{max_temp:.1f} °C")
t3.metric("Minimum", f"{min_temp:.1f} °C")

st.write(f"**Hottest time:** {hottest['time']} ({hottest['temperature']:.1f}°C)")
st.write(f"**Coolest time:** {coolest['time']} ({coolest['temperature']:.1f}°C)")

# Temperature Alerts
HIGH_TEMP = 32
LOW_TEMP = 15
alerts = []
for r in temperature_records:
    if r["temperature"] >= HIGH_TEMP:
        alerts.append(f"⚠️ High temperature at {r['time']}: {r['temperature']:.1f}°C")
    elif r["temperature"] <= LOW_TEMP:
        alerts.append(f"⚠️ Low temperature at {r['time']}: {r['temperature']:.1f}°C")

if alerts:
    st.warning("Temperature Alerts")
    for a in alerts:
        st.write(a)
else:
    st.success("✓ No temperature alerts")

# Pump Run Details
st.subheader("🔧 Pump Run Details")
if pump_records:
    pump_table = []
    for r in pump_records:
        water = r["runtime"] * water_per_hour
        energy = r["runtime"] * pump_power_kw
        pump_table.append({
            "Run": r["run"],
            "Start": r["start"],
            "End": r["end"],
            "Runtime (h)": round(r["runtime"], 2),
            "Water (L)": round(water, 1),
            "Energy (kWh)": round(energy, 2)
        })
    st.dataframe(pump_table, use_container_width=True)
else:
    st.info("No pump runs entered yet.")

# Temperature table
st.subheader("📅 Daily Temperature Log")
temp_table = []
for r in temperature_records:
    status = "HIGH" if r["temperature"] >= HIGH_TEMP else ("LOW" if r["temperature"] <= LOW_TEMP else "NORMAL")
    temp_table.append({
        "Time": r["time"],
        "Temperature (°C)": r["temperature"],
        "Status": status
    })
st.dataframe(temp_table, use_container_width=True)

# What-If Simulator
st.subheader("🔮 What-If Irrigation Simulator")
reduction = st.slider("Reduce pump runtime by what percentage?", 0, 100, 20)
factor = 1 - (reduction / 100)

new_runtime = total_runtime * factor
new_water = total_water * factor
new_energy = total_energy * factor
new_cost = electricity_cost * factor

c1, c2, c3 = st.columns(3)
c1.metric("Water Saved", f"{total_water - new_water:,.0f} L")
c2.metric("Energy Saved", f"{total_energy - new_energy:.2f} kWh")
c3.metric("Cost Saved", f"${electricity_cost - new_cost:.2f}")

# Download Reports
st.subheader("📥 Download Reports")

col_a, col_b = st.columns(2)

with col_a:
    if st.button("Generate Full Farm Report"):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "Timestamp", "Farm", "Crop", "Field Size (acres)", "Pump Type",
            "Pump Power (kW)", "Total Runtime (h)", "Water Used (L)",
            "Total Energy (kWh)", "Electrical Energy (kWh)", "Solar Energy (kWh)",
            "Electricity Cost ($)", "Average Temp (°C)", "Max Temp (°C)",
            "Min Temp (°C)", "Required Water (L)", "Irrigation Ratio (%)", "Status"
        ])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            farm_name, crop_name, field_size, pump_type,
            pump_power_kw, round(total_runtime, 2), round(total_water, 1),
            round(total_energy, 2), round(electrical_energy, 2), round(solar_energy, 2),
            round(electricity_cost, 2), round(avg_temp, 1), round(max_temp, 1),
            round(min_temp, 1), round(required_water, 1), round(irrigation_ratio, 1),
            irrigation_status
        ])
        st.download_button(
            "Download Farm Report (CSV)",
            buffer.getvalue(),
            file_name="farm_report.csv",
            mime="text/csv"
        )

with col_b:
    if st.button("Generate Temperature Log"):
        buffer2 = io.StringIO()
        writer2 = csv.writer(buffer2)
        writer2.writerow(["Date", "Farm", "Time", "Temperature (°C)"])
        for r in temperature_records:
            writer2.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                farm_name,
                r["time"],
                r["temperature"]
            ])
        st.download_button(
            "Download Temperature Log (CSV)",
            buffer2.getvalue(),
            file_name="temperature_log.csv",
            mime="text/csv"
        )

st.markdown("---")
st.caption("Smart Farm Calculator • Built with Streamlit • Ready for future hardware integration")
