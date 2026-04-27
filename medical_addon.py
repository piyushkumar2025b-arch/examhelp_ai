"""
medical_addon.py — Steps 13-14
Additions: Enhanced symptom checker, Drug interaction checker, BMI + health metrics,
First Aid guide, Medical glossary
"""
import streamlit as st

BODY_SYSTEMS = ["Cardiovascular","Respiratory","Digestive","Neurological",
                "Musculoskeletal","Endocrine","Immune","Reproductive","Urinary","Skin"]

FIRST_AID = {
    "Heart Attack": {
        "steps":["Call 108/112 immediately","Have person sit/lie down comfortably",
                 "Loosen tight clothing","Give aspirin 325mg if not allergic (chew, don't swallow)",
                 "If unconscious & not breathing: start CPR","Use AED if available"],
        "color":"#ef4444"
    },
    "Choking (Adult)": {
        "steps":["Ask 'Are you choking?' — if can't speak/cough","Stand behind person",
                 "Give 5 firm back blows between shoulder blades","Give 5 abdominal thrusts (Heimlich)",
                 "Alternate until object expelled or unconscious","If unconscious: CPR + check airway"],
        "color":"#f59e0b"
    },
    "Severe Bleeding": {
        "steps":["Apply direct firm pressure with clean cloth","Elevate injured area above heart",
                 "Do NOT remove cloth — add more on top","Apply pressure bandage",
                 "For limbs: tourniquet 5cm above wound if bleeding uncontrolled",
                 "Call emergency services immediately"],
        "color":"#dc2626"
    },
    "Seizure": {
        "steps":["Stay calm — most seizures stop in 1-3 min","Clear area of sharp objects",
                 "DO NOT restrain or put anything in mouth","Turn person to recovery position",
                 "Time the seizure","Call ambulance if >5 min or no recovery in 5 min"],
        "color":"#8b5cf6"
    },
    "Burn": {
        "steps":["Cool burn under cool (not cold) running water for 10-20 min",
                 "Do NOT use ice, butter, or toothpaste","Remove jewellery near burn",
                 "Cover with clean non-fluffy material","Do NOT burst blisters",
                 "Seek medical attention for large/deep/face burns"],
        "color":"#f97316"
    },
    "Fracture (Suspected)": {
        "steps":["Do NOT try to straighten it","Immobilize with splint or padding",
                 "Apply ice pack wrapped in cloth","Elevate if possible",
                 "Do NOT remove shoes if foot/ankle injured",
                 "Seek immediate medical attention"],
        "color":"#06b6d4"
    },
}

DRUG_INTERACTIONS = {
    ("aspirin","warfarin"):("HIGH RISK","Increased bleeding risk. Do not combine without doctor supervision.","#ef4444"),
    ("aspirin","ibuprofen"):("MODERATE","Reduces aspirin's heart-protective effect.","#f59e0b"),
    ("metformin","alcohol"):("MODERATE","Risk of lactic acidosis. Limit alcohol with metformin.","#f59e0b"),
    ("simvastatin","grapefruit"):("HIGH RISK","Grapefruit massively increases statin levels. Avoid.","#ef4444"),
    ("ssri","tramadol"):("HIGH RISK","Risk of serotonin syndrome. Potentially fatal.","#ef4444"),
    ("warfarin","vitamin k"):("MODERATE","Vitamin K reduces warfarin effectiveness.","#f59e0b"),
    ("lithium","ibuprofen"):("HIGH RISK","NSAIDs increase lithium toxicity risk.","#ef4444"),
    ("digoxin","amiodarone"):("HIGH RISK","Amiodarone increases digoxin toxicity significantly.","#ef4444"),
}

def render_medical_addon():
    st.markdown("""
    <style>
    .med-card { background:rgba(10,14,30,0.8);border:1px solid rgba(16,185,129,0.15);
        border-radius:14px;padding:16px 18px;margin-bottom:10px; }
    .med-step { background:rgba(16,185,129,0.06);border-left:2px solid #10b981;
        padding:8px 14px;margin:6px 0;border-radius:0 8px 8px 0;
        font-size:0.87rem;color:rgba(255,255,255,0.78); }
    .med-risk-hi { background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
        border-radius:8px;padding:12px;color:#fca5a5; }
    .med-risk-md { background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);
        border-radius:8px;padding:12px;color:#fde68a; }
    </style>""", unsafe_allow_html=True)

    m1,m2,m3,m4,m5 = st.tabs([
        "🩺 Symptom Checker","💊 Drug Interactions","📊 Health Metrics","🚑 First Aid Guide","📚 Medical Glossary"
    ])

    with m1:
        st.markdown("**🩺 Advanced Symptom Checker**")
        symptoms = st.text_area("Describe all symptoms in detail:",
                                 placeholder="e.g. sharp chest pain for 2 days, gets worse when breathing deep, fever 101°F, dry cough",
                                 height=100, key="med_symptoms")
        sys_col = st.columns(5)
        affected = st.multiselect("Body system(s) affected:", BODY_SYSTEMS, key="med_systems")
        c1,c2,c3 = st.columns(3)
        age = c1.number_input("Age:", min_value=0, max_value=120, value=25, key="med_age")
        gender = c2.selectbox("Gender:", ["Male","Female","Other"], key="med_gender")
        duration = c3.text_input("Duration:", placeholder="e.g. 3 days", key="med_duration")
        existing = st.text_input("Existing conditions:", placeholder="e.g. diabetes, hypertension", key="med_existing")

        if symptoms and st.button("🔍 Analyze Symptoms", type="primary", use_container_width=True, key="med_analyze"):
            with st.spinner("Analyzing symptoms..."):
                try:
                    from utils.ai_engine import generate
                    prompt = f"""Patient: {age}yo {gender}, symptoms: {symptoms}. Systems: {', '.join(affected) or 'not specified'}. Duration: {duration}. Existing conditions: {existing or 'none'}.

Provide:
1. Most likely diagnoses (top 3-5) with probability
2. Red flag symptoms to watch for
3. Immediate action required?
4. When to see a doctor
5. What specialist to consult
6. Common tests that may be ordered

IMPORTANT: Add disclaimer that this is for educational purposes only and not medical advice."""
                    result = generate(prompt, max_tokens=2000, temperature=0.3)
                    st.markdown(f"""
                    <div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.2);
                        border-radius:10px;padding:12px;margin-bottom:16px;font-size:0.82rem;color:#fca5a5;">
                        ⚠️ Educational purposes only. Always consult a qualified doctor for medical advice.
                    </div>""", unsafe_allow_html=True)
                    st.markdown(result)
                except Exception as e: st.error(str(e))

    with m2:
        st.markdown("**💊 Drug Interaction Checker**")
        d1 = st.text_input("Drug / Substance 1:", placeholder="e.g. aspirin, metformin, alcohol", key="med_drug1").lower()
        d2 = st.text_input("Drug / Substance 2:", placeholder="e.g. warfarin, ibuprofen, grapefruit", key="med_drug2").lower()
        if d1 and d2 and st.button("🔍 Check Interaction", type="primary", use_container_width=True, key="med_drug_btn"):
            found = False
            for (a,b),(level,desc,clr) in DRUG_INTERACTIONS.items():
                if (d1 in a or a in d1) and (d2 in b or b in d2) or (d2 in a or a in d2) and (d1 in b or b in d1):
                    css_class = "med-risk-hi" if level=="HIGH RISK" else "med-risk-md"
                    st.markdown(f'<div class="{css_class}"><strong>⚠️ {level}</strong><br>{desc}</div>', unsafe_allow_html=True)
                    found = True; break
            if not found:
                with st.spinner("Checking interaction with AI..."):
                    try:
                        from utils.ai_engine import generate
                        ans = generate(f"Explain the interaction between {d1} and {d2}. Include: severity level, mechanism, what happens, who is at risk, and what to do. Add disclaimer.")
                        st.markdown(ans)
                    except Exception as e: st.error(str(e))

        st.markdown("**Quick Reference Interactions:**")
        for (a,b),(level,desc,clr) in list(DRUG_INTERACTIONS.items())[:4]:
            css = "med-risk-hi" if level=="HIGH RISK" else "med-risk-md"
            st.markdown(f'<div class="{css}" style="margin-bottom:6px;"><strong>{a.title()} + {b.title()}</strong>: {desc}</div>', unsafe_allow_html=True)

    with m3:
        st.markdown("**📊 Health Metrics Calculator**")
        hc1,hc2,hc3 = st.columns(3)
        weight = hc1.number_input("Weight (kg):", value=70.0, key="med_weight")
        height = hc2.number_input("Height (cm):", value=170.0, key="med_height")
        h_age  = hc3.number_input("Age:", value=25, key="med_h_age")
        h_gender = st.radio("Gender:", ["Male","Female"], horizontal=True, key="med_h_gender")

        if st.button("📊 Calculate All Health Metrics", type="primary", use_container_width=True, key="med_calc"):
            bmi = weight / ((height/100)**2)
            bmi_cat = "Underweight" if bmi<18.5 else "Normal" if bmi<25 else "Overweight" if bmi<30 else "Obese"
            bmr = (10*weight + 6.25*height - 5*h_age + (5 if h_gender=="Male" else -161))
            ideal_weight = 22 * (height/100)**2
            body_fat_approx = (1.20*bmi + 0.23*h_age - (5.4 if h_gender=="Male" else 0))

            metrics = [
                ("BMI", f"{bmi:.1f}", f"({bmi_cat})", "#6366f1"),
                ("BMR", f"{bmr:.0f} kcal", "Daily base calories", "#06b6d4"),
                ("Ideal Weight", f"{ideal_weight:.1f} kg", "BMI=22 target", "#10b981"),
                ("Est. Body Fat", f"{body_fat_approx:.1f}%", "Approximate", "#f59e0b"),
            ]
            cols = st.columns(4)
            for i,(lbl,val,sub,clr) in enumerate(metrics):
                with cols[i]:
                    st.markdown(f"""
                    <div style="background:rgba(10,14,30,0.8);border:1px solid {clr}22;border-top:2px solid {clr};
                        border-radius:12px;padding:14px;text-align:center;">
                        <div style="font-size:1.3rem;font-weight:800;color:{clr};">{val}</div>
                        <div style="font-size:0.62rem;color:rgba(255,255,255,0.3);letter-spacing:2px;">{lbl}</div>
                        <div style="font-size:0.68rem;color:rgba(255,255,255,0.35);">{sub}</div>
                    </div>""", unsafe_allow_html=True)

    with m4:
        sel = st.selectbox("Choose emergency:", list(FIRST_AID.keys()), key="med_fa_sel")
        info = FIRST_AID[sel]
        st.markdown(f"""
        <div style="background:rgba(10,14,30,0.85);border:1px solid {info['color']}44;
            border-top:3px solid {info['color']};border-radius:18px;padding:24px;">
            <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;
                color:{info['color']};margin-bottom:16px;">🚑 {sel}</div>
            {"".join(f'<div class="med-step">Step {i+1}. {s}</div>' for i,s in enumerate(info['steps']))}
        </div>""", unsafe_allow_html=True)
        st.markdown("---")
        fa_q = st.text_input("Ask AI about any emergency:", placeholder="What to do if someone is drowning?", key="med_fa_q")
        if fa_q and st.button("🚑 Get First Aid Instructions", key="med_fa_btn", use_container_width=True):
            with st.spinner("Getting instructions..."):
                try:
                    from utils.ai_engine import generate
                    ans = generate(f"Step-by-step first aid for: {fa_q}. Be clear, numbered, actionable. State when to call emergency services.")
                    st.markdown(ans)
                except Exception as e: st.error(str(e))

    with m5:
        med_term = st.text_input("Search medical term:", placeholder="e.g. tachycardia, dyspnea, prognosis", key="med_gloss")
        if med_term and st.button("📚 Explain Term", type="primary", use_container_width=True, key="med_gloss_btn"):
            with st.spinner("Looking up..."):
                try:
                    from utils.ai_engine import generate
                    ans = generate(f"Explain the medical term '{med_term}': definition, etymology, pronunciation, clinical significance, related terms, and an example of how it's used in a clinical context.")
                    st.markdown(ans)
                except Exception as e: st.error(str(e))
