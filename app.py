import streamlit as st
import random
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import re

st.set_page_config(page_title="Smart Farm Calculator", page_icon="🌾",
                   layout="wide", initial_sidebar_state="expanded")

# ---------- Data ----------
CROP_RECOMMENDATIONS = {
    "Maize": {"ideal_temp": "18–32°C", "water_need": "High during flowering",
             "tip": "Avoid water stress during tasseling stage."},
    "Beans": {"ideal_temp": "15–25°C", "water_need": "Moderate",
              "tip": "Sensitive to waterlogging. Ensure good drainage."},
    "Tomatoes": {"ideal_temp": "20–30°C", "water_need": "Consistent moisture",
                 "tip": "Irregular watering causes fruit cracking."},
    "Wheat": {"ideal_temp": "15–25°C", "water_need": "Moderate",
              "tip": "Critical water need during flowering and grain filling."},
    "Cabbage": {"ideal_temp": "15–20°C", "water_need": "High and regular",
                "tip": "Keep soil consistently moist for good head formation."},
    "Other": {"ideal_temp": "Varies", "water_need": "Check crop guide",
              "tip": "Monitor soil moisture regularly."}
}

def new_farm():
    return {
        "crop": "Maize", "field_size": 5.0, "pump_type": "Electrical",
        "pump_power_kw": 2.2, "flow_rate": 50.0,
        "electricity_price": 0.15, "fertilizer_cost": 0.0,
        "solar_percentage": 70, "entry_mode": "Manual", "n_runs": 1,
        "runs": [{"start": "06:00", "end": "08:00"}],
        "temp_mode": "Manual", "temperatures": [25.0] * 5,
        "min_t": 18.0, "max_t": 35.0,
        "required_water": 5000.0, "rainfall": 0.0, "notes": "",
        "history": []
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "farms" not in st.session_state:
    st.session_state.farms = {"My Farm": new_farm()}
if "current_farm" not in st.session_state:
    st.session_state.current_farm = "My Farm"
if "theme" not in st.session_state:
    st.session_state.theme = "Light"

# ---------- Login ----------
if not st.session_state.logged_in:
    st.title("🌾 Smart Farm Calculator")
    st.subheader("Login")
    username = st.text_input("Enter your name / farm username")
    if st.button("Login", type="primary") and username.strip():
        st.session_state.username = username.strip()
        st.session_state.logged_in = True
        st.rerun()
    st.stop()

# ---------- Theme ----------
theme = st.sidebar.radio("Theme", ["Light", "Dark"],
    index=0 if st.session_state.theme == "Light" else 1)
st.session_state.theme = theme
dark = theme == "Dark"

# Avoid text over a busy photo; use solid, high-contrast surfaces.
page_bg = "#101820" if dark else "#f3f7f2"
panel_bg = "#1d2935" if dark else "#ffffff"
text_color = "#f5f7fa" if dark else "#17231b"
muted = "#c2ccd6" if dark else "#4d5b50"
accent = "#7bc67e" if dark else "#236b35"
plot_template = "plotly_dark" if dark else "plotly_white"

st.markdown(f""" <style> .stApp {{ background: {page_bg}; color: {text_color}; }} [data-testid="stHeader"] {{ background: {page_bg}; }} [data-testid="stSidebar"] {{ background: {panel_bg}; }} .stApp, .stApp p, .stApp label, .stApp span, .stApp [data-testid="stMarkdownContainer"] {{ color: {text_color}; }} h1, h2, h3 {{ color: {accent} !important; }} [data-testid="stMetric"] {{ background: {panel_bg}; border: 1px solid {accent}; border-radius: 12px; padding: 14px; }} [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{ color: {text_color} !important; }} div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{ color: {text_color} !important; }} .stCaption {{ color: {muted} !important; }} </style> """, unsafe_allow_html=True)

# ---------- Farm selection / creation ----------
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.username}")
    st.markdown("### 🚜 Farms")
    farm_names = list(st.session_state.farms.keys())
    if st.session_state.current_farm not in farm_names:
        st.session_state.current_farm = farm_names[0]
    selected = st.selectbox("Select farm", farm_names,
        index=farm_names.index(st.session_state.current_farm), key="farm_picker")
    st.session_state.current_farm = selected

    with st.form("add_farm_form", clear_on_submit=True):
        requested_name = st.text_input("New farm name")
        add_clicked = st.form_submit_button("➕ Create separate farm")
    if add_clicked:
        clean_name = requested_name.strip()
        if not clean_name:
            st.warning("Enter a farm name.")
        elif clean_name in st.session_state.farms:
            st.warning("A farm with that name already exists.")
        else:
            st.session_state.farms[clean_name] = new_farm()
            st.session_state.current_farm = clean_name
            st.session_state.farm_picker = clean_name
            st.rerun()

farm_name = st.session_state.current_farm
farm = st.session_state.farms[farm_name]
# Prefix every widget key with the farm name so widget values do not bleed across farms.
prefix = "farm_" + str(abs(hash(farm_name)))

# ---------- Farm configuration ----------
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📋 Farm Details")
    crop_name = st.selectbox("Crop", list(CROP_RECOMMENDATIONS),
        index=list(CROP_RECOMMENDATIONS).index(farm["crop"]), key=f"{prefix}_crop")
    field_size = st.number_input("Field size (acres)", min_value=0.1,
        value=float(farm["field_size"]), step=0.1, key=f"{prefix}_area")

    st.markdown("### ⚙️ Pump Settings")
    pump_type = st.selectbox("Energy source", ["Electrical", "Solar", "Hybrid"],
        index=["Electrical", "Solar", "Hybrid"].index(farm["pump_type"]),
        key=f"{prefix}_pump_type")
    pump_power_kw = st.number_input("Power (kW)", min_value=0.1,
        value=float(farm["pump_power_kw"]), step=0.1, key=f"{prefix}_power")
    flow_rate = st.number_input("Flow rate (L/min)", min_value=1.0,
        value=float(farm["flow_rate"]), step=1.0, key=f"{prefix}_flow")

    st.markdown("### 💰 Costs")
    electricity_price = st.number_input("Electricity ($/kWh)", min_value=0.0,
        value=float(farm["electricity_price"]), step=0.01, key=f"{prefix}_elec")
    fertilizer_cost = st.number_input("Fertilizer cost ($)", min_value=0.0,
        value=float(farm["fertilizer_cost"]), step=1.0, key=f"{prefix}_fert")
    if pump_type == "Solar":
        solar_percentage = 100
        st.caption("Solar contribution: 100%")
    elif pump_type == "Electrical":
        solar_percentage = 0
        st.caption("Solar contribution: 0%")
    else:
        solar_percentage = st.slider("Solar %", 0, 100,
            int(farm["solar_percentage"]), key=f"{prefix}_solar")

    st.markdown("### ⏱️ Pump Runs")
    entry_mode = st.radio("Mode", ["Manual", "Automatic"],
        index=["Manual", "Automatic"].index(farm["entry_mode"]),
        horizontal=True, key=f"{prefix}_entry_mode")
    n_runs = int(st.number_input("Number of runs", 1, 8,
        int(farm["n_runs"]), key=f"{prefix}_nruns"))
    pump_records = []
    if entry_mode == "Manual":
        # Preserve individual run values per farm.
        old_runs = farm["runs"]
        for i in range(n_runs):
            previous = old_runs[i] if i < len(old_runs) else {"start": "06:00", "end": "08:00"}
            with st.expander(f"Run {i+1}", expanded=(i == 0)):
                a, b = st.columns(2)
                start = a.text_input("Start (HH:MM)", previous["start"], key=f"{prefix}_s{i}")
                end = b.text_input("End (HH:MM)", previous["end"], key=f"{prefix}_e{i}")
                try:
                    s = datetime.strptime(start, "%H:%M")
                    e = datetime.strptime(end, "%H:%M")
                    if e < s:
                        e += timedelta(days=1)
                    runtime = (e-s).total_seconds()/3600
                    pump_records.append({"run": i+1, "start": start, "end": end, "runtime": runtime})
                except ValueError:
                    st.error(f"Run {i+1}: use HH:MM (24-hour time).")
    else:
        min_rt = st.number_input("Min hours/run", min_value=0.0, value=1.0,
            step=0.5, key=f"{prefix}_minrt")
        max_rt = st.number_input("Max hours/run", min_value=0.0, value=3.0,
            step=0.5, key=f"{prefix}_maxrt")
        if max_rt < min_rt:
            st.warning("Maximum runtime must be at least the minimum.")
        else:
            # Randomized values stay fixed for this render, not re-randomized per widget.
            if farm.get("auto_runs_key") != (n_runs, min_rt, max_rt):
                farm["auto_runs"] = [round(random.uniform(min_rt, max_rt), 2)
                                     for _ in range(n_runs)]
                farm["auto_runs_key"] = (n_runs, min_rt, max_rt)
            for i, runtime in enumerate(farm["auto_runs"]):
                pump_records.append({"run": i+1, "start": "Auto", "end": "Auto", "runtime": runtime})

    st.markdown("### 🌡️ Temperature")
    temp_mode = st.radio("Temperature mode", ["Manual", "Automatic"],
        index=["Manual", "Automatic"].index(farm["temp_mode"]),
        horizontal=True, key=f"{prefix}_tmode")
    hours = ["06:00", "09:00", "12:00", "15:00", "18:00"]
    temperature_records = []
    if temp_mode == "Manual":
        for i, hour in enumerate(hours):
            val = st.number_input(hour, value=float(farm["temperatures"][i]),
                key=f"{prefix}_temp{i}")
            temperature_records.append({"time": hour, "temperature": val})
    else:
        min_t = st.number_input("Minimum °C", value=float(farm["min_t"]), key=f"{prefix}_mint")
        max_t = st.number_input("Maximum °C", value=float(farm["max_t"]), key=f"{prefix}_maxt")
        if max_t < min_t:
            st.warning("Maximum temperature must be at least minimum.")
        else:
            if farm.get("auto_temps_key") != (min_t, max_t):
                farm["auto_temps"] = [round(random.uniform(min_t, max_t), 1) for _ in hours]
                farm["auto_temps_key"] = (min_t, max_t)
            temperature_records = [{"time": h, "temperature": t}
                                   for h, t in zip(hours, farm["auto_temps"])]

    st.markdown("### 💧 Water & Rain")
    required_water = st.number_input("Required water (L)", min_value=0.0,
        value=float(farm["required_water"]), step=100.0, key=f"{prefix}_reqwater")
    rainfall = st.number_input("Rainfall (mm)", min_value=0.0,
        value=float(farm["rainfall"]), step=0.5, key=f"{prefix}_rain")
    notes = st.text_area("Notes", value=farm["notes"], key=f"{prefix}_notes")

# Save current settings back to this farm's independent data.
farm.update({
    "crop": crop_name, "field_size": field_size, "pump_type": pump_type,
    "pump_power_kw": pump_power_kw, "flow_rate": flow_rate,
    "electricity_price": electricity_price, "fertilizer_cost": fertilizer_cost,
    "solar_percentage": solar_percentage, "entry_mode": entry_mode, "n_runs": n_runs,
    "runs": [{"start": r["start"], "end": r["end"]} for r in pump_records
             if r["start"] != "Auto"],
    "temp_mode": temp_mode, "temperatures": [r["temperature"] for r in temperature_records],
    "required_water": required_water, "rainfall": rainfall, "notes": notes
})

# ---------- Calculations ----------
total_runtime = sum(r["runtime"] for r in pump_records)
total_water = total_runtime * flow_rate * 60
total_energy = total_runtime * pump_power_kw
electrical_energy = total_energy * (100-solar_percentage)/100
solar_energy = total_energy * solar_percentage/100
electricity_cost = electrical_energy * electricity_price
total_cost = electricity_cost + fertilizer_cost
temps = [r["temperature"] for r in temperature_records] or [0]
avg_temp, max_temp, min_temp = sum(temps)/len(temps), max(temps), min(temps)
ratio = total_water/required_water*100 if required_water > 0 else 0
if ratio > 120:
    status, efficiency = "Over-irrigation", "Poor"
elif ratio >= 90:
    status, efficiency = "On target", "Good"
else:
    status, efficiency = "Under-irrigation", "Average"
water_per_acre = total_water/field_size if field_size else 0
cost_per_litre = total_cost/total_water if total_water else 0

# ---------- Main ----------
st.title(f"🌾 {farm_name}")
st.caption(f"Logged in as {st.session_state.username} · Independent farm workspace")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Water Used", f"{total_water:,.0f} L")
m2.metric("Energy", f"{total_energy:.2f} kWh")
m3.metric("Total Cost", f"${total_cost:,.2f}")
m4.metric("Efficiency", efficiency)
m5, m6, m7, m8 = st.columns(4)
m5.metric("Water / Acre", f"{water_per_acre:,.0f} L")
m6.metric("Cost / Litre", f"${cost_per_litre:.4f}")
m7.metric("Runtime", f"{total_runtime:.2f} h")
m8.metric("Rainfall", f"{rainfall:g} mm")

recommendation = CROP_RECOMMENDATIONS[crop_name]
st.info(f"**{crop_name} recommendation** \n"
        f"Ideal temperature: {recommendation['ideal_temp']} \n"
        f"Water need: {recommendation['water_need']} \n"
        f"Tip: {recommendation['tip']}")

st.subheader("📈 Charts")
left, right = st.columns(2)
with left:
    if temperature_records:
        temp_df = pd.DataFrame(temperature_records)
        fig = px.line(temp_df, x="time", y="temperature", markers=True,
                      title="Temperature Through the Day", template=plot_template)
        fig.update_layout(font=dict(color=text_color), paper_bgcolor=panel_bg,
                          plot_bgcolor=panel_bg, yaxis_title="Temperature (°C)",
                          xaxis_title="Time", margin=dict(l=15, r=15, t=55, b=15))
        st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_temp_chart")
with right:
    # Separate charts by unit to avoid misleading mixed-unit comparisons.
    comparison = pd.DataFrame({
        "Measure": ["Water used", "Required water"],
        "Litres": [total_water, required_water]
    })
    fig2 = px.bar(comparison, x="Measure", y="Litres", text_auto=".0f",
                  title="Water Used vs Required", template=plot_template)
    fig2.update_layout(font=dict(color=text_color), paper_bgcolor=panel_bg,
                       plot_bgcolor=panel_bg, yaxis_title="Litres (L)",
                       xaxis_title="", margin=dict(l=15, r=15, t=55, b=15))
    st.plotly_chart(fig2, use_container_width=True, key=f"{prefix}_water_chart")

st.caption(f"Average temperature: {avg_temp:.1f}°C · Status: {status} · "
           f"Solar energy: {solar_energy:.2f} kWh · Electrical energy: {electrical_energy:.2f} kWh")

# ---------- Farm-specific history ----------
st.subheader("📜 Calculation History")
if st.button("💾 Save This Calculation", type="primary", key=f"{prefix}_save"):
    farm["history"].insert(0, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "farm": farm_name, "crop": crop_name,
        "water_L": round(total_water, 1), "energy_kWh": round(total_energy, 2),
        "cost": round(total_cost, 2), "efficiency": efficiency, "status": status,
        "runtime_h": round(total_runtime, 2), "notes": notes
    })
    st.success(f"Saved calculation for {farm_name}.")
history = farm["history"]
if history:
    st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
else:
    st.info("No saved calculations for this farm yet.")

# ---------- PDF ----------
st.subheader("📄 Export PDF Report")
if st.button("Generate PDF Report", key=f"{prefix}_pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    safe_name = farm_name.encode("latin-1", "replace").decode("latin-1")
    pdf.cell(0, 10, f"Smart Farm Report - {safe_name}", ln=True)
    pdf.set_font("Arial", size=11)
    rows = [
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"User: {st.session_state.username}", f"Crop: {crop_name}",
        f"Field size: {field_size:.1f} acres", f"Water used: {total_water:,.0f} L",
        f"Required water: {required_water:,.0f} L", f"Energy: {total_energy:.2f} kWh",
        f"Total cost: ${total_cost:.2f}", f"Efficiency: {efficiency}",
        f"Status: {status}", f"Runtime: {total_runtime:.2f} h",
        f"Rainfall: {rainfall:g} mm"
    ]
    for row in rows:
        pdf.cell(0, 8, row.encode("latin-1", "replace").decode("latin-1"), ln=True)
    if notes:
        pdf.multi_cell(0, 8, ("Notes: " + notes).encode("latin-1", "replace").decode("latin-1"))
    pdf_result = pdf.output(dest="S")
    pdf_data = pdf_result.encode("latin-1") if isinstance(pdf_result, str) else bytes(pdf_result)
    file_slug = re.sub(r"[^A-Za-z0-9_-]+", "_", farm_name).strip("_") or "farm"
    st.download_button("⬇️ Download PDF", data=pdf_data,
        file_name=f"farm_report_{file_slug}.pdf", mime="application/pdf",
        key=f"{prefix}_download_pdf")

st.markdown("---")
st.caption("Smart Farm Calculator · Separate farms · Per-farm history · PDF reports · Crop tips")
