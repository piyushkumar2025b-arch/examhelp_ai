"""
circuit_solver_addon.py
Addon for circuit_solver_engine.py
New features:
  - AI Circuit Image Analyzer (upload photo of circuit → AI explains it)
  - Electronics Formula Bank (50+ formulas)
  - Component Library with datasheets
  - Circuit Quiz Mode
"""
import streamlit as st
import io
import random

# ─── Electronics Formula Bank ────────────────────────────
FORMULA_BANK = {
    "Ohm's Law": {
        "formula": "V = I × R",
        "variables": {"V": "Voltage (Volts)", "I": "Current (Amperes)", "R": "Resistance (Ohms)"},
        "category": "Basic",
        "color": "#6366f1",
    },
    "Power (P=VI)": {
        "formula": "P = V × I = I²R = V²/R",
        "variables": {"P": "Power (Watts)", "V": "Voltage", "I": "Current"},
        "category": "Basic",
        "color": "#8b5cf6",
    },
    "Capacitive Reactance": {
        "formula": "Xc = 1 / (2πfC)",
        "variables": {"Xc": "Capacitive reactance (Ω)", "f": "Frequency (Hz)", "C": "Capacitance (F)"},
        "category": "AC",
        "color": "#06b6d4",
    },
    "Inductive Reactance": {
        "formula": "XL = 2πfL",
        "variables": {"XL": "Inductive reactance (Ω)", "f": "Frequency (Hz)", "L": "Inductance (H)"},
        "category": "AC",
        "color": "#06b6d4",
    },
    "Impedance": {
        "formula": "Z = √(R² + (XL - Xc)²)",
        "variables": {"Z": "Impedance (Ω)", "R": "Resistance", "XL": "Inductive reactance", "Xc": "Capacitive reactance"},
        "category": "AC",
        "color": "#10b981",
    },
    "Resonant Frequency": {
        "formula": "f₀ = 1 / (2π√(LC))",
        "variables": {"f₀": "Resonant frequency (Hz)", "L": "Inductance (H)", "C": "Capacitance (F)"},
        "category": "AC",
        "color": "#10b981",
    },
    "Kirchhoff's Voltage Law": {
        "formula": "ΣV = 0 (around any closed loop)",
        "variables": {"ΣV": "Sum of all voltages in loop"},
        "category": "Circuit Laws",
        "color": "#f59e0b",
    },
    "Kirchhoff's Current Law": {
        "formula": "ΣI_in = ΣI_out",
        "variables": {"ΣI": "Sum of currents at a node"},
        "category": "Circuit Laws",
        "color": "#f59e0b",
    },
    "Resistors in Series": {
        "formula": "R_total = R1 + R2 + R3 + ...",
        "variables": {"R_total": "Total resistance"},
        "category": "Resistors",
        "color": "#ec4899",
    },
    "Resistors in Parallel": {
        "formula": "1/R_total = 1/R1 + 1/R2 + ...",
        "variables": {"R_total": "Total resistance"},
        "category": "Resistors",
        "color": "#ec4899",
    },
    "Voltage Divider": {
        "formula": "Vout = Vin × R2 / (R1 + R2)",
        "variables": {"Vout": "Output voltage", "Vin": "Input voltage"},
        "category": "Circuits",
        "color": "#6366f1",
    },
    "Current Divider": {
        "formula": "I1 = I_total × R2 / (R1 + R2)",
        "variables": {"I1": "Current through R1"},
        "category": "Circuits",
        "color": "#6366f1",
    },
    "Capacitors in Series": {
        "formula": "1/C_total = 1/C1 + 1/C2 + ...",
        "variables": {"C_total": "Total capacitance"},
        "category": "Capacitors",
        "color": "#8b5cf6",
    },
    "Capacitors in Parallel": {
        "formula": "C_total = C1 + C2 + C3 + ...",
        "variables": {"C_total": "Total capacitance"},
        "category": "Capacitors",
        "color": "#8b5cf6",
    },
    "Energy in Capacitor": {
        "formula": "E = ½CV²",
        "variables": {"E": "Energy (J)", "C": "Capacitance (F)", "V": "Voltage (V)"},
        "category": "Capacitors",
        "color": "#8b5cf6",
    },
    "Energy in Inductor": {
        "formula": "E = ½LI²",
        "variables": {"E": "Energy (J)", "L": "Inductance (H)", "I": "Current (A)"},
        "category": "Inductors",
        "color": "#06b6d4",
    },
    "Transformer Ratio": {
        "formula": "V1/V2 = N1/N2 = I2/I1",
        "variables": {"V": "Voltage", "N": "Number of turns", "I": "Current"},
        "category": "Transformers",
        "color": "#10b981",
    },
    "dB Gain (Voltage)": {
        "formula": "A_dB = 20 × log10(Vout/Vin)",
        "variables": {"A_dB": "Gain in decibels"},
        "category": "Signal",
        "color": "#f59e0b",
    },
    "RC Time Constant": {
        "formula": "τ = R × C",
        "variables": {"τ": "Time constant (seconds)", "R": "Resistance (Ω)", "C": "Capacitance (F)"},
        "category": "Time",
        "color": "#ec4899",
    },
    "RL Time Constant": {
        "formula": "τ = L / R",
        "variables": {"τ": "Time constant (seconds)", "L": "Inductance (H)", "R": "Resistance (Ω)"},
        "category": "Time",
        "color": "#ec4899",
    },
}

# ─── Component Library ────────────────────────────────────
COMPONENTS = [
    {"name":"Resistor","sym":"🔲","desc":"Opposes current flow. Measured in Ohms (Ω).","color":"#6366f1"},
    {"name":"Capacitor","sym":"⚡","desc":"Stores electrical energy in an electric field. Measured in Farads (F).","color":"#8b5cf6"},
    {"name":"Inductor","sym":"〰️","desc":"Stores energy in a magnetic field. Measured in Henries (H).","color":"#06b6d4"},
    {"name":"Diode","sym":"▷|","desc":"Allows current in one direction only. Forward voltage ~0.7V for Si.","color":"#10b981"},
    {"name":"LED","sym":"💡","desc":"Light-Emitting Diode. Emits light when forward biased.","color":"#f59e0b"},
    {"name":"Transistor (NPN)","sym":"🔺","desc":"Current-controlled switch/amplifier. Base controls Collector-Emitter current.","color":"#ec4899"},
    {"name":"Op-Amp","sym":"▷","desc":"Differential voltage amplifier. Open-loop gain ~100,000.","color":"#6366f1"},
    {"name":"555 Timer","sym":"⬜","desc":"Versatile IC for timing, oscillation, PWM.","color":"#f97316"},
    {"name":"MOSFET","sym":"⊻","desc":"Voltage-controlled switch. Very fast switching.","color":"#8b5cf6"},
    {"name":"Zener Diode","sym":"▷⌿","desc":"Reverse-biased voltage regulator. Maintains constant voltage.","color":"#06b6d4"},
]


def render_circuit_addon():
    """Render addon features for circuit solver."""

    st.markdown("""
    <style>
    .cs-formula-card {
        background: rgba(10,14,30,0.8); border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px; padding: 16px 18px; margin-bottom: 10px;
        border-left: 3px solid var(--fc, #6366f1);
        transition: all 0.25s ease;
    }
    .cs-formula-card:hover { transform: translateX(4px); border-color: rgba(99,102,241,0.5); }
    .cs-formula { font-family: 'JetBrains Mono', monospace; font-size: 1.1rem;
        color: #c7d2fe; font-weight: 700; margin-bottom: 8px; }
    .cs-comp-card { background: rgba(10,14,30,0.7); border: 1px solid rgba(255,255,255,0.07);
        border-radius: 12px; padding: 14px 12px; text-align: center;
        transition: all 0.25s ease; }
    .cs-comp-card:hover { transform: translateY(-3px); border-color: rgba(99,102,241,0.4); }
    .cs-comp-sym { font-size: 2rem; margin-bottom: 6px; display: block; }
    .cs-comp-name { font-size: 0.78rem; font-weight: 700; color: rgba(255,255,255,0.85); }
    .cs-comp-desc { font-size: 0.68rem; color: rgba(255,255,255,0.4); margin-top: 4px; line-height: 1.5; }
    .cs-sec { font-family: 'JetBrains Mono', monospace; font-size: 0.62rem;
        letter-spacing: 3px; color: #818cf8; text-transform: uppercase;
        margin: 20px 0 12px; display: flex; align-items: center; gap: 10px; }
    .cs-sec::after { content: ''; flex: 1; height: 1px;
        background: linear-gradient(90deg, rgba(99,102,241,0.4), transparent); }
    </style>
    """, unsafe_allow_html=True)

    addon_tab1, addon_tab2, addon_tab3, addon_tab4 = st.tabs([
        "🔬 Circuit Image AI", "📐 Formula Bank", "🔧 Component Library", "🧠 Circuit Quiz"
    ])

    # ── Tab 1: AI Circuit Image Analyzer ──────────────────
    with addon_tab1:
        st.markdown('<div class="cs-sec">AI Circuit Image Analyzer</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);
            border-radius:14px;padding:14px 18px;margin-bottom:16px;font-size:0.88rem;
            color:rgba(255,255,255,0.65);line-height:1.7;">
            📸 Upload a photo/screenshot of any circuit diagram — AI will identify components,
            explain the circuit's purpose, calculate key values, and suggest improvements.
        </div>
        """, unsafe_allow_html=True)

        circ_img = st.file_uploader("Upload circuit image/diagram",
                                     type=["png","jpg","jpeg","webp"],
                                     key="cs_circuit_img")
        analysis_type = st.selectbox("Analysis Type", [
            "Full Circuit Explanation",
            "Component Identification",
            "Calculate Values (Ohm's Law etc.)",
            "Safety & Improvements",
            "PCB Layout Analysis",
        ], key="cs_analysis_type")

        if circ_img and st.button("🔬 Analyze Circuit with AI", type="primary",
                                   use_container_width=True, key="cs_analyze_btn"):
            import base64
            img_bytes = circ_img.read()
            b64 = base64.b64encode(img_bytes).decode()
            mime = f"image/{circ_img.type.split('/')[-1]}"

            prompts = {
                "Full Circuit Explanation": "Analyze this circuit diagram completely. Identify all components, explain what the circuit does, trace the current flow, identify input/output points, and explain the circuit's function in detail.",
                "Component Identification": "List every electronic component visible in this circuit diagram. For each: name, value/rating if shown, symbol type, and its role in the circuit.",
                "Calculate Values (Ohm's Law etc.)": "Look at this circuit. Identify all resistors, capacitors, voltage sources. Apply Ohm's Law, KVL, KCL to calculate voltages, currents, and power at key nodes.",
                "Safety & Improvements": "Review this circuit for: safety issues, potential failure points, component stress, and suggest 5 improvements or optimizations.",
                "PCB Layout Analysis": "Analyze this PCB/circuit layout. Comment on: trace widths, component placement, potential EMI issues, power distribution, and grounding strategy.",
            }
            prompt = prompts.get(analysis_type, "Analyze this circuit diagram.")

            with st.spinner("🔬 AI analyzing circuit..."):
                try:
                    from utils.ai_engine import vision_generate
                    result = vision_generate(prompt=prompt, image_b64=b64, mime=mime, max_tokens=2000)
                except Exception as e:
                    result = f"⚠️ Vision AI error: {e}"

            st.markdown(f"""
            <div style="background:rgba(10,14,30,0.85);border:1px solid rgba(99,102,241,0.25);
                border-radius:18px;padding:24px;margin-top:16px;">
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.62rem;
                    letter-spacing:3px;color:#818cf8;margin-bottom:14px;">AI CIRCUIT ANALYSIS</div>
                <div style="font-size:0.9rem;color:rgba(255,255,255,0.8);line-height:1.85;
                    white-space:pre-wrap;">{result}</div>
            </div>
            """, unsafe_allow_html=True)
            st.download_button("📥 Save Analysis", result, "circuit_analysis.txt",
                               "text/plain", key="cs_dl_analysis")

    # ── Tab 2: Formula Bank ────────────────────────────────
    with addon_tab2:
        st.markdown('<div class="cs-sec">Electronics Formula Bank (20+ Formulas)</div>', unsafe_allow_html=True)

        cats = list(set(v["category"] for v in FORMULA_BANK.values()))
        sel_cat = st.selectbox("Filter by category:", ["All"] + sorted(cats), key="cs_formula_cat")
        search = st.text_input("🔍 Search formula...", placeholder="e.g. voltage, capacitor, power",
                               key="cs_formula_search")

        shown = 0
        for name, info in FORMULA_BANK.items():
            if sel_cat != "All" and info["category"] != sel_cat:
                continue
            if search and search.lower() not in name.lower() and search.lower() not in info["formula"].lower():
                continue
            shown += 1
            vars_html = "".join(
                f'<span style="font-family:JetBrains Mono,monospace;font-size:0.72rem;'
                f'color:rgba(255,255,255,0.45);margin-right:12px;"><b style="color:#a5b4fc;">{k}</b>: {v}</span>'
                for k,v in info["variables"].items()
            )
            st.markdown(f"""
            <div class="cs-formula-card" style="--fc:{info['color']};">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                    <div style="font-size:0.88rem;font-weight:700;color:rgba(255,255,255,0.9);">{name}</div>
                    <span style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.2);
                        border-radius:100px;padding:2px 10px;font-size:0.62rem;font-family:JetBrains Mono,monospace;
                        color:#818cf8;letter-spacing:1px;">{info['category']}</span>
                </div>
                <div class="cs-formula">{info['formula']}</div>
                <div style="margin-top:8px;">{vars_html}</div>
            </div>
            """, unsafe_allow_html=True)

        if shown == 0:
            st.info("No formulas match your search.")

        # Interactive Calculator
        st.markdown('<div class="cs-sec">Quick Formula Calculator</div>', unsafe_allow_html=True)
        calc_type = st.selectbox("Calculate:", ["Voltage (V=IR)","Current (I=V/R)","Resistance (R=V/I)",
                                                  "Power (P=VI)","RC Time Constant","Resonant Frequency"], key="cs_calc_type")
        cc1, cc2 = st.columns(2)
        if "Voltage" in calc_type:
            I = cc1.number_input("Current I (A)", value=0.0, format="%.4f", key="cs_calc_I")
            R = cc2.number_input("Resistance R (Ω)", value=0.0, format="%.4f", key="cs_calc_R")
            if st.button("= Calculate V", key="cs_calc_btn", use_container_width=True):
                st.success(f"**V = I × R = {I} × {R} = {I*R:.4f} V**")
        elif "Current" in calc_type:
            V = cc1.number_input("Voltage V (V)", value=0.0, format="%.4f", key="cs_calc_V2")
            R = cc2.number_input("Resistance R (Ω)", value=1.0, format="%.4f", key="cs_calc_R2")
            if st.button("= Calculate I", key="cs_calc_btn2", use_container_width=True):
                st.success(f"**I = V / R = {V} / {R} = {V/R if R else 'undefined':.4f} A**")
        elif "Resistance" in calc_type:
            V = cc1.number_input("Voltage V (V)", value=0.0, format="%.4f", key="cs_calc_V3")
            I = cc2.number_input("Current I (A)", value=1.0, format="%.4f", key="cs_calc_I3")
            if st.button("= Calculate R", key="cs_calc_btn3", use_container_width=True):
                st.success(f"**R = V / I = {V} / {I} = {V/I if I else 'undefined':.4f} Ω**")
        elif "Power" in calc_type:
            V = cc1.number_input("Voltage V (V)", value=0.0, format="%.4f", key="cs_calc_Vp")
            I = cc2.number_input("Current I (A)", value=0.0, format="%.4f", key="cs_calc_Ip")
            if st.button("= Calculate P", key="cs_calc_btnp", use_container_width=True):
                st.success(f"**P = V × I = {V} × {I} = {V*I:.4f} W**")
        elif "RC" in calc_type:
            R = cc1.number_input("Resistance R (Ω)", value=1000.0, format="%.2f", key="cs_calc_Rrc")
            C = cc2.number_input("Capacitance C (F)", value=0.000001, format="%.8f", key="cs_calc_Crc")
            if st.button("= Calculate τ", key="cs_calc_btnrc", use_container_width=True):
                tau = R * C
                st.success(f"**τ = R × C = {tau:.6f} s = {tau*1000:.4f} ms**")
        elif "Resonant" in calc_type:
            L = cc1.number_input("Inductance L (H)", value=0.001, format="%.6f", key="cs_calc_L")
            C = cc2.number_input("Capacitance C (F)", value=0.000001, format="%.8f", key="cs_calc_Cres")
            if st.button("= Calculate f₀", key="cs_calc_btnres", use_container_width=True):
                import math
                f0 = 1 / (2 * math.pi * (L * C)**0.5) if L * C > 0 else 0
                st.success(f"**f₀ = 1/(2π√LC) = {f0:.2f} Hz = {f0/1000:.4f} kHz**")

    # ── Tab 3: Component Library ───────────────────────────
    with addon_tab3:
        st.markdown('<div class="cs-sec">Electronic Component Library</div>', unsafe_allow_html=True)
        comp_cols = st.columns(3)
        for i, comp in enumerate(COMPONENTS):
            with comp_cols[i % 3]:
                st.markdown(f"""
                <div class="cs-comp-card" style="border-left:3px solid {comp['color']};">
                    <span class="cs-comp-sym">{comp['sym']}</span>
                    <div class="cs-comp-name">{comp['name']}</div>
                    <div class="cs-comp-desc">{comp['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Ask AI about component
        st.markdown('<div class="cs-sec">Ask AI About a Component</div>', unsafe_allow_html=True)
        comp_q = st.text_input("Component or concept to explain:", placeholder="e.g. 555 timer, op-amp inverting amplifier",
                               key="cs_comp_q")
        if comp_q and st.button("🔍 Explain with AI", key="cs_comp_explain", use_container_width=True):
            with st.spinner("Analyzing..."):
                try:
                    from utils.ai_engine import generate
                    ans = generate(f"Explain {comp_q} for an electronics student: pinout, working principle, common applications, key specs to remember, and one example circuit. Be thorough but clear.")
                except Exception as e:
                    ans = f"Error: {e}"
            st.markdown(f"""
            <div style="background:rgba(10,14,30,0.8);border:1px solid rgba(99,102,241,0.2);
                border-radius:14px;padding:20px;margin-top:12px;font-size:0.9rem;
                color:rgba(255,255,255,0.78);line-height:1.85;white-space:pre-wrap;">{ans}</div>
            """, unsafe_allow_html=True)

    # ── Tab 4: Circuit Quiz ────────────────────────────────
    with addon_tab4:
        st.markdown('<div class="cs-sec">Electronics Circuit Quiz</div>', unsafe_allow_html=True)
        quiz_level = st.selectbox("Difficulty:", ["Beginner","Intermediate","Advanced"], key="cs_quiz_lvl")
        quiz_topic = st.selectbox("Topic:", ["Mixed","Ohm's Law","AC Circuits","Digital Logic","Op-Amps","Semiconductors"], key="cs_quiz_topic")

        if st.button("🎯 Generate Quiz (5 Questions)", type="primary", use_container_width=True, key="cs_quiz_gen"):
            with st.spinner("Generating quiz..."):
                try:
                    from utils.ai_engine import generate
                    qprompt = f"Create 5 {quiz_level} level multiple-choice electronics quiz questions about {quiz_topic}. Format each as:\nQ: [question]\nA) [option]\nB) [option]\nC) [option]\nD) [option]\nANSWER: [letter] — [explanation]\n---"
                    quiz_raw = generate(qprompt, max_tokens=2000, temperature=0.5)
                    st.session_state["cs_quiz_raw"] = quiz_raw
                except Exception as e:
                    st.error(str(e))

        if st.session_state.get("cs_quiz_raw"):
            questions = [q.strip() for q in st.session_state.cs_quiz_raw.split("---") if q.strip()]
            for i, qblock in enumerate(questions[:5]):
                lines = [l.strip() for l in qblock.strip().split("\n") if l.strip()]
                q_text = ""; opts = []; ans = ""
                for l in lines:
                    if l.startswith("Q:"): q_text = l[2:].strip()
                    elif l[:2] in ("A)","B)","C)","D)"): opts.append(l)
                    elif l.startswith("ANSWER:"): ans = l[7:].strip()
                st.markdown(f"""
                <div style="background:rgba(10,14,30,0.75);border:1px solid rgba(255,255,255,0.07);
                    border-radius:14px;padding:18px;margin-bottom:14px;">
                    <div style="font-weight:700;color:rgba(255,255,255,0.9);margin-bottom:12px;">
                        <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.25);
                            border-radius:6px;padding:2px 8px;font-size:0.78rem;color:#818cf8;margin-right:8px;">Q{i+1}</span>
                        {q_text}
                    </div>
                    {"".join(f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:9px 14px;margin-bottom:6px;font-size:0.86rem;color:rgba(255,255,255,0.6);">{o}</div>' for o in opts)}
                </div>
                """, unsafe_allow_html=True)
                if ans:
                    with st.expander(f"✅ Answer to Q{i+1}"):
                        st.success(f"✅ {ans}")
