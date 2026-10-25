import streamlit as st
import random
from datetime import datetime, timedelta
import csv
import io

st.set_page_config(page_title="Smart Farm Calculator", page_icon="🌾", layout="wide")

st.title("🌾 Smart Farm Water, Energy & Temperature Calculator")
st.markdown("---")

# ---------- HELPERS ----------
def calculate_runtime(start_time, end_time):
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")
    if end < start:
        end += timedelta(days=1)
    return (end - start).total_seconds() / 3600

# ---------- SIDEBAR INPUTS ----------
with st.sidebar:
    st.header("Farm Information")
    farm_name = st.text_input("Farm name", "My Farm")
    crop_name = st.text_input("Crop being monitored", "Maize")
    field_size = st.number_input("Field size (acres)", min_value=0.0, value=5.0, step=0.1)

    st.header("Pump Information")
    pump_type = st.selectbox("Pump energy source", ["Electrical", "Solar", "Hybrid"])
    pump_power_kw = st.number_input("Pump power (kW)", min_value=0.1, value=2.2, step=0.1)
    flow_rate = st.number_input("Flow rate (L/min)", min_value=1.0, value=50.0, step=1.0)

    st.header("Energy Settings")
    electricity_price = st.number_input("Electricity price ($/kWh)", min_value=0.0, value=0.15, step=0.01)
    solar_efficiency = st.number_input("Solar efficiency (%)", min_value=1.0, value=80.0, step=1.0)

    st.header("Pump Runs")
    entry_mode = st.radio("Pump data entry", ["Manual", "Automatic"])
    
    pump_records = []
    if entry_mode == "Manual":
        num_runs = st.number_input("Number of pump runs", min_value=1, value=1, step=1)
        for i in range(int(num_runs)):
            st.markdown(f"**Run {i+1}**")
            col1, col2 = st.columns(2)
            start = col1.text_input(f"Start (HH:MM)", "06:00", key=f"start_{i}")
            end = col2.text_input(f"End (HH:MM)", "08:00", key=f"end_{i}")
            try:
                runtime = calculate_runtime(start, end)
                pump_records.append({"run": i+1, "start": start, "end": end, "runtime": runtime})
            except:
                st.warning("Use HH:MM format")
    else:
        num_runs = st.number_input("Number of automatic runs", min_value=1, value=2, step=1)
        min_rt = st.number_input("Min runtime (hours)", value=1.0)
        max_rt = st.number_input("Max runtime (hours)", value=3.0)
        for i in range(int(num_runs)):
            runtime = round(random.uniform(min_rt, max_rt), 2)
            pump_records.append({"run": i+1, "start": "Auto", "end": "Auto", "runtime": runtime})

    st.header("Temperature")
    temp_mode = st.radio("Temperature entry", ["Manual", "Automatic"])
    temperature_hours = ["06:00", "09:00", "12:00", "15:00", "18:00"]
    temperature_records = []
    
    if temp_mode == "Manual":
        for hour in temperature_hours:
            temp = st.number_input(f"Temp at {hour} (°C)", value=25.0, key=hour)
            temperature_records.append({"time": hour, "temperature": temp})
    else:
        min_t = st.number_input("Min temp (°C)", value=18.0)
        max_t = st.number_input("Max temp (°C)", value=35.0)
        for hour in temperature_hours:
            temp = round(random.uniform(min_t, max_t), 1)
            temperature_records.append({"time": hour, "temperature": temp})

    required_water = st.number_input("Estimated water required today (L)", value=5000.0)

# ---------- CALCULATIONS ----------
total_runtime = sum(r["runtime"] for r in pump_records) if pump_records else 0
water_per_hour = flow_rate * 60
total_water = total_runtime * water_per_hour
total_energy = total_runtime * pump_power_kw

electrical_energy = solar_energy = 0
if pump_type == "Electrical":
    electrical_energy = total_energy
elif pump_type == "Solar":
    solar_energy = total_energy
else:
    solar_pct = st.sidebar.slider("Solar percentage in hybrid", 0, 100, 70)
    solar_energy = total_energy * solar_pct / 100
    electrical_energy = total_energy - solar_energy

electricity_cost = electrical_energy * electricity_price

temperatures = [r["temperature"] for r in temperature_records]
avg_temp = sum(temperatures)/len(temperatures) if temperatures else 0
max_temp = max(temperatures) if temperatures else 0
min_temp = min(temperatures) if temperatures else 0

irrigation_ratio = (total_water / required_water * 100) if required_water > 0 else 0
if irrigation_ratio > 120:
    status = "Possible over-irrigation"
elif irrigation_ratio >= 90:
    status = "Within target range"
else:
    status = "Possible under-irrigation"

# ---------- MAIN DISPLAY ----------
col1, col2, col3 = st.columns(3)
col1.metric("Total Water Used", f"{total_water:,.0f} L")
col2.metric("Total Energy", f"{total_energy:.2f} kWh")
col3.metric("Electricity Cost", f"${electricity_cost:.2f}")

st.subheader("Farm Summary")
st.write(f"**Farm:** {farm_name} | **Crop:** {crop_name} | **Size:** {field_size} acres")
st.write(f"**Pump type:** {pump_type} | **Power:** {pump_power_kw} kW | **Runtime:** {total_runtime:.2f} h")
st.write(f"**Irrigation status:** {status} ({irrigation_ratio:.1f}%)")

st.subheader("Temperature Overview")
st.write(f"Average: {avg_temp:.1f}°C | Max: {max_temp:.1f}°C | Min: {min_temp:.1f}°C")

# Alerts
HIGH, LOW = 32, 15
alerts = []
for r in temperature_records:
    if r["temperature"] >= HIGH:
        alerts.append(f"⚠️ High temp at {r['time']}: {r['temperature']}°C")
    elif r["temperature"] <= LOW:
        alerts.append(f"⚠️ Low temp at {r['time']}: {r['temperature']}°C")

if alerts:
    st.warning("Temperature Alerts")
    for a in alerts:
        st.write(a)
else:
    st.success("No temperature alerts")

# What-if simulator
st.subheader("What-If Irrigation Simulator")
reduction = st.slider("Reduce runtime by (%)", 0, 100, 20)
factor = 1 - reduction/100
st.write(f"Water saved: {(total_water - total_water*factor):,.0f} L")
st.write(f"Energy saved: {(total_energy - total_energy*factor):.2f} kWh")
st.write(f"Cost saved: ${(electricity_cost - electricity_cost*factor):.2f}")

# Temperature table
st.subheader("Daily Temperature Data")
st.table([{"Time": r["time"], "Temperature (°C)": r["temperature"]} for r in temperature_records])

# Download reports
st.subheader("Download Reports")
if st.button("Generate CSV Report"):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Farm", "Crop", "Water (L)", "Energy (kWh)", "Cost ($)", "Avg Temp"])
    writer.writerow([farm_name, crop_name, round(total_water,1), round(total_energy,2), round(electricity_cost,2), round(avg_temp,1)])
    st.download_button("Download Farm Report", buffer.getvalue(), "farm_report.csv", "text/csv")
