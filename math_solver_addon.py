"""
math_solver_addon.py
Additions to math_solver_engine.py:
  - Function plotter (matplotlib)
  - Matrix operations
  - Statistics calculator
  - Number theory tools
  - Unit converter (math-heavy)
  - AI step-by-step explainer
"""
import streamlit as st
import math
import random

def _safe_eval(expr: str):
    """Safely evaluate a math expression."""
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith('_')}
    allowed.update({'abs': abs, 'round': round, 'min': min, 'max': max, 'sum': sum})
    try:
        return eval(expr, {"__builtins__": {}}, allowed)
    except Exception as e:
        return f"Error: {e}"

def _matrix_ops(mat_str: str):
    """Parse a matrix string like [[1,2],[3,4]]."""
    try:
        return eval(mat_str)
    except Exception:
        return None

def _det_2x2(m):
    return m[0][0]*m[1][1] - m[0][1]*m[1][0]

def _det_3x3(m):
    return (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
           -m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
           +m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))

def _mat_add(a, b):
    return [[a[i][j]+b[i][j] for j in range(len(a[0]))] for i in range(len(a))]

def _mat_mul(a, b):
    rows_a, cols_a = len(a), len(a[0])
    cols_b = len(b[0])
    result = [[sum(a[i][k]*b[k][j] for k in range(cols_a)) for j in range(cols_b)] for i in range(rows_a)]
    return result

def _transpose(m):
    return [[m[j][i] for j in range(len(m))] for i in range(len(m[0]))]

def _stats(data):
    n = len(data)
    mean = sum(data)/n
    sorted_d = sorted(data)
    med = sorted_d[n//2] if n%2 else (sorted_d[n//2-1]+sorted_d[n//2])/2
    mode_val = max(set(data), key=data.count)
    variance = sum((x-mean)**2 for x in data)/n
    std = variance**0.5
    return {"n":n,"mean":round(mean,4),"median":med,"mode":mode_val,
            "std":round(std,4),"variance":round(variance,4),
            "min":min(data),"max":max(data),"range":max(data)-min(data)}

def render_math_addon():
    st.markdown("""
    <style>
    .ma-card { background:rgba(10,14,30,0.8); border:1px solid rgba(99,102,241,0.2);
        border-radius:14px; padding:18px; margin-bottom:12px; }
    .ma-result { font-family:'JetBrains Mono',monospace; font-size:1.3rem;
        font-weight:700; color:#818cf8; text-align:center; padding:14px;
        background:rgba(99,102,241,0.08); border-radius:10px; margin-top:10px; }
    .ma-sec { font-family:'JetBrains Mono',monospace; font-size:0.62rem;
        letter-spacing:3px; color:#818cf8; text-transform:uppercase;
        margin:18px 0 10px; }
    </style>
    """, unsafe_allow_html=True)

    t1,t2,t3,t4,t5 = st.tabs([
        "📈 Grapher","🔢 Matrix Ops","📊 Statistics","🔬 Number Theory","🤖 AI Explainer"
    ])

    # ── Tab 1: Function Plotter ────────────────────────────
    with t1:
        st.markdown('<div class="ma-sec">Function Plotter</div>', unsafe_allow_html=True)
        fn_expr = st.text_input("f(x) =", value="sin(x)", placeholder="e.g. x**2 + 2*x - 1",
                                key="ma_fn_expr")
        c1,c2,c3 = st.columns(3)
        xmin = c1.number_input("x min", value=-10.0, key="ma_xmin")
        xmax = c2.number_input("x max", value=10.0,  key="ma_xmax")
        pts  = c3.number_input("Points", value=500, min_value=50, max_value=5000, key="ma_pts")

        fn2 = st.text_input("g(x) = (optional 2nd function)", placeholder="e.g. cos(x)",
                            key="ma_fn2")

        if st.button("📈 Plot Function", type="primary", use_container_width=True, key="ma_plot_btn"):
            try:
                import numpy as np
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt

                x_vals = np.linspace(xmin, xmax, int(pts))
                allowed = {k: getattr(np, k) for k in dir(np) if not k.startswith('_')}
                allowed['x'] = x_vals
                y_vals = eval(fn_expr.replace("^","**"), {"__builtins__":{}}, allowed)

                fig, ax = plt.subplots(figsize=(10,5), facecolor='#0a0e1e')
                ax.set_facecolor('#0f172a')
                ax.plot(x_vals, y_vals, color='#818cf8', linewidth=2.5, label=f"f(x) = {fn_expr}")

                if fn2.strip():
                    allowed2 = {k: getattr(np, k) for k in dir(np) if not k.startswith('_')}
                    allowed2['x'] = x_vals
                    y2 = eval(fn2.replace("^","**"), {"__builtins__":{}}, allowed2)
                    ax.plot(x_vals, y2, color='#06b6d4', linewidth=2.5, linestyle='--', label=f"g(x) = {fn2}")

                ax.axhline(y=0, color='rgba(255,255,255,0.2)', linewidth=0.8)
                ax.axvline(x=0, color='rgba(255,255,255,0.2)', linewidth=0.8)
                ax.grid(True, color='#ffffff15', linewidth=0.5)
                ax.tick_params(colors='#ffffff80')
                for spine in ax.spines.values(): spine.set_edgecolor('#ffffff20')
                ax.set_xlabel('x', color='#ffffff80'); ax.set_ylabel('f(x)', color='#ffffff80')
                ax.set_title(f'f(x) = {fn_expr}', color='#c7d2fe', fontsize=13, fontweight='bold')
                ax.legend(facecolor='#0f172a', edgecolor='#6366f155', labelcolor='#ffffff80')
                plt.tight_layout()

                import io
                buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0); plt.close()
                st.image(buf, use_container_width=True)
                st.download_button("⬇️ Download Graph", buf.getvalue(), "graph.png",
                                   "image/png", key="ma_graph_dl")
            except Exception as e:
                st.error(f"Plot error: {e}")

        # Quick function evaluator
        st.markdown('<div class="ma-sec">Evaluate at Point</div>', unsafe_allow_html=True)
        xval = st.number_input("Evaluate f(x) at x =", value=0.0, key="ma_xval")
        if st.button("= Evaluate", key="ma_eval_btn", use_container_width=True):
            allowed_eval = {k: getattr(math, k) for k in dir(math) if not k.startswith('_')}
            allowed_eval['x'] = xval
            try:
                result = eval(fn_expr.replace("^","**"), {"__builtins__":{}}, allowed_eval)
                st.markdown(f'<div class="ma-result">f({xval}) = {result:.6f}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(str(e))

    # ── Tab 2: Matrix Operations ────────────────────────────
    with t2:
        st.markdown('<div class="ma-sec">Matrix Calculator</div>', unsafe_allow_html=True)
        st.caption("Enter matrices as Python lists, e.g. [[1,2],[3,4]]")
        ma_a = st.text_area("Matrix A:", value="[[1,2],[3,4]]", height=80, key="ma_mat_a")
        ma_b = st.text_area("Matrix B (optional):", value="[[5,6],[7,8]]", height=80, key="ma_mat_b")
        op = st.selectbox("Operation:", [
            "Determinant of A","Transpose of A","A + B","A × B",
            "Trace of A","Row Echelon Form"
        ], key="ma_op")

        if st.button("= Calculate", type="primary", use_container_width=True, key="ma_mat_btn"):
            A = _matrix_ops(ma_a); B = _matrix_ops(ma_b)
            try:
                if op == "Determinant of A":
                    if len(A)==2: d = _det_2x2(A)
                    elif len(A)==3: d = _det_3x3(A)
                    else: d = "Only 2×2 and 3×3 supported"
                    st.markdown(f'<div class="ma-result">det(A) = {d}</div>', unsafe_allow_html=True)
                elif op == "Transpose of A":
                    t = _transpose(A)
                    st.write("**Transpose:**"); st.write(t)
                elif op == "A + B":
                    r = _mat_add(A,B); st.write("**A + B =**"); st.write(r)
                elif op == "A × B":
                    r = _mat_mul(A,B); st.write("**A × B =**"); st.write(r)
                elif op == "Trace of A":
                    tr = sum(A[i][i] for i in range(len(A)))
                    st.markdown(f'<div class="ma-result">tr(A) = {tr}</div>', unsafe_allow_html=True)
                elif op == "Row Echelon Form":
                    st.info("Row Echelon: Use AI Explainer tab for step-by-step Gaussian elimination.")
            except Exception as e:
                st.error(f"Matrix error: {e}")

    # ── Tab 3: Statistics Calculator ───────────────────────
    with t3:
        st.markdown('<div class="ma-sec">Statistics Calculator</div>', unsafe_allow_html=True)
        data_input = st.text_area("Enter numbers (comma or space separated):",
                                  placeholder="e.g. 12, 45, 67, 23, 89, 34",
                                  height=100, key="ma_stat_data")
        if st.button("📊 Calculate Statistics", type="primary", use_container_width=True, key="ma_stat_btn"):
            raw = data_input.replace(",", " ").split()
            try:
                nums = [float(x) for x in raw if x]
                if not nums: st.error("No numbers found."); st.stop()
                s = _stats(nums)
                cols = st.columns(4)
                tiles = [("n", str(s['n']),"#6366f1"),("Mean",str(s['mean']),"#06b6d4"),
                         ("Median",str(s['median']),"#10b981"),("Mode",str(s['mode']),"#f59e0b"),
                         ("Std Dev",str(s['std']),"#ec4899"),("Variance",str(s['variance']),"#8b5cf6"),
                         ("Min",str(s['min']),"#6366f1"),("Max",str(s['max']),"#06b6d4")]
                ccols = st.columns(4)
                for i,(lbl,val,clr) in enumerate(tiles):
                    with ccols[i%4]:
                        st.markdown(f"""
                        <div style="background:rgba(10,14,30,0.8);border:1px solid {clr}22;
                            border-top:2px solid {clr};border-radius:12px;padding:14px;text-align:center;margin-bottom:8px;">
                            <div style="font-family:'JetBrains Mono',monospace;font-size:1.2rem;
                                font-weight:800;color:{clr};">{val}</div>
                            <div style="font-size:0.62rem;letter-spacing:2px;color:rgba(255,255,255,0.3);
                                text-transform:uppercase;">{lbl}</div>
                        </div>""", unsafe_allow_html=True)

                # Histogram with matplotlib
                try:
                    import numpy as np, matplotlib; matplotlib.use("Agg")
                    import matplotlib.pyplot as plt, io as _io
                    fig,ax=plt.subplots(figsize=(9,4),facecolor='#0a0e1e')
                    ax.set_facecolor('#0f172a')
                    ax.hist(nums, bins=min(15,len(nums)), color='#6366f1', alpha=0.8, edgecolor='#818cf888')
                    ax.axvline(s['mean'],color='#06b6d4',linewidth=2,linestyle='--',label=f'Mean={s["mean"]}')
                    ax.axvline(s['median'],color='#10b981',linewidth=2,linestyle='-.',label=f'Median={s["median"]}')
                    ax.grid(True,color='#ffffff10'); ax.tick_params(colors='#ffffff80')
                    for sp in ax.spines.values(): sp.set_edgecolor('#ffffff20')
                    ax.legend(facecolor='#0f172a',edgecolor='#6366f155',labelcolor='#ffffff80')
                    ax.set_title('Distribution Histogram',color='#c7d2fe',fontsize=12)
                    plt.tight_layout(); buf=_io.BytesIO(); plt.savefig(buf,format='png',dpi=130,bbox_inches='tight')
                    buf.seek(0); plt.close(); st.image(buf,use_container_width=True)
                except Exception: pass
            except ValueError:
                st.error("Please enter valid numbers only.")

    # ── Tab 4: Number Theory ────────────────────────────────
    with t4:
        st.markdown('<div class="ma-sec">Number Theory Tools</div>', unsafe_allow_html=True)
        n4 = st.number_input("Enter a number:", value=12, min_value=1, max_value=10**9, key="ma_nt_n")
        nt_op = st.selectbox("Operation:", [
            "Prime Check","Prime Factorization","GCD & LCM","Fibonacci Sequence",
            "Pascal's Triangle Row","Euler's Totient","Divisors List"
        ], key="ma_nt_op")
        n4b = st.number_input("Second number (for GCD/LCM):", value=8, min_value=1, key="ma_nt_b")

        if st.button("= Calculate", key="ma_nt_btn", use_container_width=True, type="primary"):
            n = int(n4); m = int(n4b)
            def is_prime(x):
                if x<2: return False
                for i in range(2,int(x**0.5)+1):
                    if x%i==0: return False
                return True
            def prime_factors(x):
                fs=[]; d=2
                while d*d<=x:
                    while x%d==0: fs.append(d); x//=d
                    d+=1
                if x>1: fs.append(x)
                return fs
            def gcd(a,b):
                while b: a,b=b,a%b
                return a

            if nt_op=="Prime Check":
                r = f"{n} is {'✅ PRIME' if is_prime(n) else '❌ NOT prime'}"
                st.markdown(f'<div class="ma-result">{r}</div>',unsafe_allow_html=True)
            elif nt_op=="Prime Factorization":
                fs=prime_factors(n)
                st.markdown(f'<div class="ma-result">{n} = {" × ".join(map(str,fs))}</div>',unsafe_allow_html=True)
            elif nt_op=="GCD & LCM":
                g=gcd(n,m); l=n*m//g
                st.markdown(f'<div class="ma-result">GCD({n},{m}) = {g} | LCM({n},{m}) = {l}</div>',unsafe_allow_html=True)
            elif nt_op=="Fibonacci Sequence":
                fibs=[0,1]
                while fibs[-1]<n: fibs.append(fibs[-1]+fibs[-2])
                st.markdown(f'<div class="ma-result">{", ".join(map(str,fibs[:20]))}</div>',unsafe_allow_html=True)
            elif nt_op=="Euler's Totient":
                phi=sum(1 for i in range(1,n+1) if gcd(n,i)==1)
                st.markdown(f'<div class="ma-result">φ({n}) = {phi}</div>',unsafe_allow_html=True)
            elif nt_op=="Divisors List":
                divs=[i for i in range(1,n+1) if n%i==0]
                st.markdown(f'<div class="ma-result">Divisors of {n}: {divs}</div>',unsafe_allow_html=True)
            elif nt_op=="Pascal's Triangle Row":
                row=[1]
                for i in range(1,n+1): row.append(row[-1]*(n-i+1)//i)
                st.markdown(f'<div class="ma-result">Row {n}: {row}</div>',unsafe_allow_html=True)

    # ── Tab 5: AI Explainer ─────────────────────────────────
    with t5:
        st.markdown('<div class="ma-sec">AI Step-by-Step Math Explainer</div>', unsafe_allow_html=True)
        math_q = st.text_area("Enter any math problem or concept:",
                              placeholder="e.g. Solve 2x² + 5x - 3 = 0\nOr: Explain integration by parts\nOr: Find the eigenvalues of [[2,1],[1,3]]",
                              height=120, key="ma_ai_q")
        detail = st.selectbox("Explanation level:", ["Brief","Detailed","Beginner-friendly","Expert level"], key="ma_ai_detail")

        if math_q and st.button("🤖 Solve with AI", type="primary", use_container_width=True, key="ma_ai_btn"):
            with st.spinner("Solving step-by-step..."):
                try:
                    from utils.ai_engine import generate
                    prompt = f"Solve this math problem step-by-step at a {detail} level. Show ALL working clearly. Use proper mathematical notation.\n\nProblem: {math_q}"
                    ans = generate(prompt, max_tokens=3000, temperature=0.2)
                    st.markdown(f"""
                    <div style="background:rgba(10,14,30,0.85);border:1px solid rgba(99,102,241,0.22);
                        border-radius:18px;padding:24px;font-size:0.92rem;
                        color:rgba(255,255,255,0.82);line-height:1.9;white-space:pre-wrap;">{ans}</div>
                    """, unsafe_allow_html=True)
                    st.download_button("📥 Save Solution", ans, "math_solution.txt", key="ma_ai_dl")
                except Exception as e:
                    st.error(str(e))
