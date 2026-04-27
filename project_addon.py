"""
project_addon.py — Steps 15-16
Additions: Gantt chart, Tech stack recommender, Risk matrix, Project cost estimator
"""
import streamlit as st, io, datetime, random

def render_project_addon():
    st.markdown("""
    <style>
    .pa-gantt-task { background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);
        border-radius:8px;padding:8px 12px;margin-bottom:6px;display:flex;align-items:center;gap:12px; }
    .pa-risk-hi { background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.25);
        border-radius:10px;padding:10px;margin-bottom:6px; }
    .pa-risk-md { background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);
        border-radius:10px;padding:10px;margin-bottom:6px; }
    .pa-risk-lo { background:rgba(16,185,129,0.07);border:1px solid rgba(16,185,129,0.2);
        border-radius:10px;padding:10px;margin-bottom:6px; }
    </style>""", unsafe_allow_html=True)

    pa1,pa2,pa3,pa4 = st.tabs([
        "📅 Gantt Chart","🛠️ Tech Stack AI","⚠️ Risk Matrix","💰 Cost Estimator"
    ])

    with pa1:
        st.markdown("**📅 Gantt Chart Generator**")
        proj_name = st.text_input("Project Name:", value="My Project", key="pa_proj_name")
        start_date = st.date_input("Project Start:", value=datetime.date.today(), key="pa_start")

        st.markdown("**Add Tasks:**")
        if "pa_tasks" not in st.session_state:
            st.session_state.pa_tasks = [
                {"name":"Planning","days":5,"color":"#6366f1"},
                {"name":"Design","days":7,"color":"#8b5cf6"},
                {"name":"Development","days":14,"color":"#06b6d4"},
                {"name":"Testing","days":5,"color":"#10b981"},
                {"name":"Deployment","days":3,"color":"#f59e0b"},
            ]

        tc1,tc2,tc3 = st.columns([3,2,1])
        new_task = tc1.text_input("Task name:", key="pa_new_task")
        new_days = tc2.number_input("Duration (days):", min_value=1, max_value=365, value=5, key="pa_new_days")
        colors = ["#6366f1","#8b5cf6","#06b6d4","#10b981","#f59e0b","#ec4899","#f97316"]
        new_col = tc3.selectbox("Color:", colors, key="pa_new_col")

        if st.button("➕ Add Task", key="pa_add_task", use_container_width=True):
            if new_task:
                st.session_state.pa_tasks.append({"name":new_task,"days":new_days,"color":new_col})
                st.rerun()

        # Render Gantt
        if st.session_state.pa_tasks:
            try:
                import matplotlib; matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                import matplotlib.patches as mpatches
                import numpy as np

                fig, ax = plt.subplots(figsize=(12,max(4,len(st.session_state.pa_tasks)*0.7+2)), facecolor='#0a0e1e')
                ax.set_facecolor('#0f172a')

                current_day = 0
                y_labels = []
                for i, task in enumerate(st.session_state.pa_tasks):
                    rect = mpatches.FancyBboxPatch((current_day, i*1.2), task["days"], 0.8,
                                                    boxstyle="round,pad=0.05",
                                                    facecolor=task["color"]+"55",
                                                    edgecolor=task["color"], linewidth=1.5)
                    ax.add_patch(rect)
                    ax.text(current_day+task["days"]/2, i*1.2+0.4, f"{task['name']} ({task['days']}d)",
                            ha='center', va='center', color='white', fontsize=8.5, fontweight='bold')
                    y_labels.append(task["name"])
                    current_day += task["days"]

                total_days = sum(t["days"] for t in st.session_state.pa_tasks)
                ax.set_xlim(0, total_days+1)
                ax.set_ylim(-0.5, len(st.session_state.pa_tasks)*1.2)
                ax.set_yticks([i*1.2+0.4 for i in range(len(st.session_state.pa_tasks))])
                ax.set_yticklabels(y_labels, color='#ffffff80', fontsize=9)
                ax.set_xlabel('Days', color='#ffffff80')
                ax.grid(True, axis='x', color='#ffffff15', linewidth=0.5)
                for sp in ax.spines.values(): sp.set_edgecolor('#ffffff15')
                ax.tick_params(colors='#ffffff80')
                ax.set_title(f'Gantt Chart — {proj_name} ({total_days} days total)', color='#c7d2fe', fontsize=12)
                plt.tight_layout()

                buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0); plt.close(); st.image(buf, use_container_width=True)
                st.download_button("📥 Download Gantt Chart", buf.getvalue(), "gantt_chart.png", key="pa_gantt_dl")
            except Exception as e:
                st.error(f"Chart error: {e}")
                for t in st.session_state.pa_tasks:
                    st.markdown(f'<div class="pa-gantt-task"><span style="color:{t["color"]};font-weight:700;">{t["name"]}</span> · {t["days"]} days</div>', unsafe_allow_html=True)

        if st.button("🗑️ Reset Tasks", key="pa_reset", use_container_width=True):
            st.session_state.pa_tasks = []; st.rerun()

        # AI project plan
        if st.button("🤖 Generate Full Project Plan with AI", key="pa_ai_plan", use_container_width=True, type="primary"):
            with st.spinner("Planning..."):
                try:
                    from utils.ai_engine import generate
                    tasks_str = ", ".join(t["name"] for t in st.session_state.pa_tasks)
                    ans = generate(f"Generate a complete project plan for '{proj_name}' with tasks: {tasks_str}. Include: milestones, dependencies, resources needed, risks, and success criteria.")
                    st.markdown(ans)
                    st.download_button("📥 Save Plan", ans, "project_plan.txt", key="pa_ai_dl")
                except Exception as e: st.error(str(e))

    with pa2:
        st.markdown("**🛠️ AI Tech Stack Recommender**")
        proj_type = st.selectbox("Project Type:", [
            "Web Application","Mobile App","Data Science / ML","API / Backend",
            "Desktop Application","Game","IoT","Blockchain / Web3","DevOps / Infrastructure"
        ], key="pa_proj_type")
        proj_desc = st.text_area("Describe your project:", placeholder="e.g. E-commerce marketplace with real-time chat and AI recommendations", height=80, key="pa_proj_desc")
        scale = st.selectbox("Expected Scale:", ["Personal/Hobby","Startup (<1000 users)","Medium (10K-100K users)","Large (1M+ users)"], key="pa_scale")
        budget = st.selectbox("Budget:", ["Free/Open-source only","Low ($0-$500/mo)","Medium ($500-$5000/mo)","Enterprise"], key="pa_budget")
        team_size = st.selectbox("Team Size:", ["Solo","2-5 devs","6-20 devs","Large team 20+"], key="pa_team")

        if st.button("🛠️ Recommend Tech Stack", type="primary", use_container_width=True, key="pa_tech_btn"):
            with st.spinner("Analyzing requirements..."):
                try:
                    from utils.ai_engine import generate
                    p = f"Recommend the best tech stack for: Type={proj_type}, Description={proj_desc}, Scale={scale}, Budget={budget}, Team={team_size}. Provide: Frontend, Backend, Database, Deployment, Testing, DevOps tools. Explain why each is chosen. Give alternatives. Include estimated learning curve and setup time."
                    ans = generate(p, max_tokens=2500, temperature=0.3)
                    st.markdown(ans)
                    st.download_button("📥 Save Tech Stack", ans, "tech_stack.txt", key="pa_tech_dl")
                except Exception as e: st.error(str(e))

    with pa3:
        st.markdown("**⚠️ Project Risk Matrix**")
        proj_for_risk = st.text_area("Describe your project:", height=80, key="pa_risk_desc")
        if proj_for_risk and st.button("⚠️ Generate Risk Matrix", type="primary", use_container_width=True, key="pa_risk_btn"):
            with st.spinner("Analyzing risks..."):
                try:
                    from utils.ai_engine import generate
                    p = f"Create a comprehensive risk matrix for this project: {proj_for_risk}. Format each risk as:\nRISK: [name]\nLIKELIHOOD: [Low/Medium/High]\nIMPACT: [Low/Medium/High]\nSEVERITY: [Low/Medium/High]\nMITIGATION: [strategy]\n---"
                    risks_raw = generate(p, max_tokens=2000, temperature=0.4)
                    blocks = [b.strip() for b in risks_raw.split("---") if b.strip()]
                    for b in blocks:
                        lines = {l.split(":")[0].strip(): ":".join(l.split(":")[1:]).strip()
                                 for l in b.split("\n") if ":" in l}
                        sev = lines.get("SEVERITY","Low")
                        css = "pa-risk-hi" if "High" in sev else "pa-risk-md" if "Medium" in sev else "pa-risk-lo"
                        st.markdown(f"""
                        <div class="{css}">
                            <div style="font-weight:700;color:rgba(255,255,255,0.9);margin-bottom:4px;">{lines.get('RISK','')}</div>
                            <div style="font-size:0.8rem;color:rgba(255,255,255,0.55);">
                                Likelihood: {lines.get('LIKELIHOOD','')} · Impact: {lines.get('IMPACT','')} · Severity: <strong>{sev}</strong>
                            </div>
                            <div style="font-size:0.82rem;color:rgba(255,255,255,0.6);margin-top:6px;">🛡️ {lines.get('MITIGATION','')}</div>
                        </div>""", unsafe_allow_html=True)
                except Exception as e: st.error(str(e))

    with pa4:
        st.markdown("**💰 Project Cost Estimator**")
        ce1,ce2 = st.columns(2)
        dev_count = ce1.number_input("Number of developers:", min_value=1, max_value=100, value=2, key="pa_devs")
        dev_rate  = ce2.number_input("Daily rate per dev ($):", min_value=10, max_value=2000, value=200, key="pa_rate")
        duration_m = st.number_input("Project duration (months):", min_value=1, max_value=60, value=3, key="pa_duration_m")
        infra_mo = st.number_input("Monthly infrastructure cost ($):", min_value=0, value=100, key="pa_infra")
        other = st.number_input("Other costs ($, one-time):", min_value=0, value=500, key="pa_other")

        if st.button("💰 Calculate Project Cost", type="primary", use_container_width=True, key="pa_cost_btn"):
            dev_cost = dev_count * dev_rate * duration_m * 22
            infra_cost = infra_mo * duration_m
            total = dev_cost + infra_cost + other
            buffer = total * 0.2

            st.markdown(f"""
            <div style="background:rgba(10,14,30,0.85);border:1px solid rgba(99,102,241,0.25);
                border-radius:18px;padding:24px;">
                <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:16px;">
                    {"".join(f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:14px;"><div style="font-size:1.1rem;font-weight:800;color:#818cf8;">${v:,.0f}</div><div style="font-size:0.62rem;color:rgba(255,255,255,0.3);letter-spacing:2px;">{k}</div></div>'
                    for k,v in [("DEV COSTS",dev_cost),("INFRASTRUCTURE",infra_cost),("OTHER COSTS",other),("20% BUFFER",buffer)])}
                </div>
                <div style="background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(6,182,212,0.1));
                    border:1px solid rgba(99,102,241,0.3);border-radius:14px;padding:18px;text-align:center;">
                    <div style="font-size:0.62rem;letter-spacing:3px;color:#818cf8;font-family:JetBrains Mono,monospace;">TOTAL ESTIMATED BUDGET</div>
                    <div style="font-family:'Syne',sans-serif;font-size:2.2rem;font-weight:800;color:#fff;margin-top:8px;">${total+buffer:,.0f}</div>
                    <div style="font-size:0.78rem;color:rgba(255,255,255,0.4);">(including 20% contingency buffer)</div>
                </div>
            </div>""", unsafe_allow_html=True)
