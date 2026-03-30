# ============================================================
# INTEGRATION REMOVED — This file has been fully commented out.
# All external service integrations, API keys, and credentials
# have been stripped for security. Do not re-enable.
# ============================================================

# """
# integrations/stripe_ui.py — Pricing & upgrade UI for ExamHelp AI.
# Beautiful plan cards with Stripe Checkout integration.
# """
# 
# import streamlit as st
# from integrations.stripe_payments import (
#     PLANS, create_checkout_session, create_billing_portal_session,
#     get_subscription_status,
# )
# from auth.supabase_auth import current_user, current_token, is_logged_in
# 
# PRICING_CSS = """
# <style>
# .plan-grid { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; }
# .plan-card {
#   flex: 1; min-width: 200px;
#   background: rgba(255,255,255,0.05);
#   border: 1px solid rgba(255,255,255,0.1);
#   border-radius: 18px; padding: 1.5rem 1.2rem;
#   transition: transform .2s, box-shadow .2s;
# }
# .plan-card:hover {
#   transform: translateY(-3px);
#   box-shadow: 0 12px 32px rgba(124,106,247,0.2);
# }
# .plan-card.popular {
#   border-color: rgba(124,106,247,0.5);
#   background: rgba(124,106,247,0.08);
#   box-shadow: 0 0 0 1px rgba(124,106,247,0.3);
# }
# .plan-badge {
#   background: linear-gradient(90deg,#7c6af7,#4f8ef7);
#   color:#fff; font-size:.7rem; font-weight:700;
#   padding:.2rem .6rem; border-radius:20px;
#   display:inline-block; margin-bottom:.6rem;
# }
# .plan-name { font-size:1.15rem; font-weight:800; color:#fff; }
# .plan-price { font-size:1.6rem; font-weight:900;
#   background:linear-gradient(90deg,#c8b8ff,#7c6af7);
#   -webkit-background-clip:text; -webkit-text-fill-color:transparent;
#   margin:.4rem 0; }
# .plan-feat { font-size:.8rem; color:rgba(255,255,255,0.6);
#   list-style:none; padding:0; margin:.8rem 0; }
# .plan-feat li { padding:.2rem 0; }
# .plan-feat li::before { content:"✓ "; color:#48c78e; font-weight:700; }
# </style>
# """
# 
# 
# def render_pricing_page():
#     """Full pricing page with plan cards and Stripe Checkout."""
#     st.markdown(PRICING_CSS, unsafe_allow_html=True)
#     st.markdown("## 💳 Plans & Pricing")
#     st.caption("Upgrade to unlock unlimited AI, Google integrations, and priority models.")
# 
#     if not is_logged_in():
#         st.warning("Please sign in to upgrade.")
#         return
# 
#     user = current_user() or {}
#     email = user.get("email", "")
# 
#     # Check current subscription
#     status = "none"
#     if email:
#         with st.spinner("Checking subscription…"):
#             status = get_subscription_status(email)
# 
#     # ── Plan cards ────────────────────────────────────────────────────────
#     cols = st.columns(3)
#     for i, (key, plan) in enumerate(PLANS.items()):
#         with cols[i]:
#             popular_badge = '<div class="plan-badge">⭐ Most Popular</div>' if key == "pro" else ""
#             feats_html = "".join(f"<li>{f}</li>" for f in plan["features"])
#             card_class = "plan-card popular" if key == "pro" else "plan-card"
# 
#             st.markdown(f"""
#             <div class="{card_class}">
#               {popular_badge}
#               <div class="plan-name">{plan['name']}</div>
#               <div class="plan-price">{plan['price']}</div>
#               <ul class="plan-feat">{feats_html}</ul>
#             </div>
#             """, unsafe_allow_html=True)
# 
#             if key == "free":
#                 is_current = status == "none"
#                 st.button(
#                     "✅ Current Plan" if is_current else plan["cta"],
#                     key=f"plan_btn_{key}",
#                     disabled=is_current,
#                     use_container_width=True,
#                 )
#             else:
#                 if status == "active" and key == "pro":
#                     if st.button("⚙️ Manage Subscription",
#                                  key=f"plan_btn_{key}", use_container_width=True):
#                         # This needs customer_id from Stripe — simplified here
#                         st.info("Visit stripe.com/billing to manage your subscription.")
#                 elif plan.get("price_id"):
#                     if st.button(plan["cta"], key=f"plan_btn_{key}",
#                                  use_container_width=True):
#                         with st.spinner("Creating checkout session…"):
#                             session = create_checkout_session(
#                                 price_id=plan["price_id"],
#                                 customer_email=email,
#                                 metadata={"user_id": user.get("id", "")},
#                             )
#                         if session.get("url"):
#                             st.markdown(
#                                 f'<a href="{session["url"]}" target="_blank" '
#                                 'style="color:#7c6af7;font-weight:700;">'
#                                 '→ Proceed to Checkout</a>',
#                                 unsafe_allow_html=True,
#                             )
#                         else:
#                             st.error(f"Checkout error: {session.get('error','?')}")
#                 else:
#                     st.button(plan["cta"], key=f"plan_btn_{key}",
#                               disabled=True, use_container_width=True)
# 
#     # Payment result handling
#     params = st.query_params
#     if params.get("payment") == "success":
#         st.success("🎉 Payment successful! Your Pro plan is now active.")
#         st.query_params.clear()
#     elif params.get("payment") == "cancel":
#         st.info("Payment cancelled. Your free plan remains active.")
#         st.query_params.clear()
# 
#     st.divider()
#     st.caption("🔒 Payments powered by Stripe · 100% secure · Cancel anytime")
# 
# 
# def render_upgrade_banner():
#     """Compact upgrade nudge for sidebar / free users."""
#     status = "none"
#     user = current_user()
#     if user:
#         status = get_subscription_status(user.get("email", ""))
# 
#     if status != "active":
#         st.markdown("""
#         <div style="background:linear-gradient(135deg,rgba(124,106,247,0.15),rgba(79,142,247,0.1));
#           border:1px solid rgba(124,106,247,0.3);border-radius:12px;
#           padding:.8rem;text-align:center;margin:.5rem 0;">
#           <div style="font-size:.82rem;font-weight:700;color:#c8b8ff;">⚡ Upgrade to Pro</div>
#           <div style="font-size:.73rem;color:rgba(255,255,255,0.5);margin:.3rem 0;">
#             Unlimited AI · Gmail · Drive · Calendar
#           </div>
#         </div>
#         """, unsafe_allow_html=True)
#         if st.button("View Plans →", key="upgrade_banner_btn", use_container_width=True):
#             st.session_state["app_mode"] = "pricing"
#             st.rerun()