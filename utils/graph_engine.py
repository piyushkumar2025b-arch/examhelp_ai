import numpy as np
import plotly.graph_objects as go
from sympy import sympify, symbols, lambdify, diff

def _safe_lambdify(expr_str, var_symbols):
    try:
        safe_str = expr_str.replace('^', '**').replace('×', '*').replace('÷', '/').replace('−', '-')
        expr = sympify(safe_str)
        return expr, lambdify(var_symbols, expr, modules=["numpy", "math"])
    except Exception as e:
        return None, str(e)

def plot_2d_graph(functions, x_min=-10, x_max=10, points=1000, theme="dark", show_derivative=False, shade_area=False):
    x_vals = np.linspace(x_min, x_max, points)
    fig = go.Figure()
    x_sym = symbols('x')
    
    colors = ['#60a5fa', '#f87171', '#4ade80', '#facc15', '#c084fc', '#2dd4bf']
    errors = []
    
    for idx, f_str in enumerate(functions):
        if not f_str.strip():
            continue
            
        expr, fun = _safe_lambdify(f_str, x_sym)
        if fun is None:
            errors.append(f"Invalid function '{f_str}': {expr}")
            continue
            
        try:
            y_vals = fun(x_vals)
            if np.isscalar(y_vals):
                y_vals = np.full_like(x_vals, y_vals)
                
            y_vals = np.real(y_vals)
            y_vals = np.where(np.abs(y_vals) > 1e6, np.nan, y_vals)
                
            color = colors[idx % len(colors)]
            
            # Fill area under curve
            fill_mode = 'tozeroy' if shade_area else 'none'
            
            fig.add_trace(go.Scatter(
                x=x_vals, y=y_vals, 
                mode='lines', 
                name=f"f(x) = {f_str}",
                line=dict(color=color, width=2.5),
                fill=fill_mode,
                fillcolor=color.replace('rgb', 'rgba').replace(')', ', 0.1)') if 'rgb' in color else color
            ))
            
            if show_derivative:
                d_expr = diff(expr, x_sym)
                d_fun = lambdify(x_sym, d_expr, modules=["numpy"])
                dy_vals = d_fun(x_vals)
                if np.isscalar(dy_vals): dy_vals = np.full_like(x_vals, dy_vals)
                dy_vals = np.where(np.abs(dy_vals) > 1e6, np.nan, dy_vals)
                
                fig.add_trace(go.Scatter(
                    x=x_vals, y=dy_vals, 
                    mode='lines', 
                    name=f"f'(x) = {d_expr}",
                    line=dict(color=color, width=1.5, dash='dot')
                ))
                
        except Exception as e:
            errors.append(f"Error computing '{f_str}': {str(e)}")

    _setup_layout(fig, theme, "", "x", "f(x)")
    return fig, errors

def plot_3d_graph(function_str, x_min=-5, x_max=5, y_min=-5, y_max=5, resolution=50, theme="dark"):
    x_sym, y_sym = symbols('x y')
    expr, fun = _safe_lambdify(function_str, (x_sym, y_sym))
    if fun is None:
        return None, [f"Invalid function: {expr}"]
        
    x_vals = np.linspace(x_min, x_max, resolution)
    y_vals = np.linspace(y_min, y_max, resolution)
    X, Y = np.meshgrid(x_vals, y_vals)
    
    try:
        Z = fun(X, Y)
        if np.isscalar(Z):
            Z = np.full_like(X, Z)
        Z = np.real(Z)
        Z = np.where(np.abs(Z) > 1e6, np.nan, Z)
        
        cmax, cmin = np.nanmax(Z), np.nanmin(Z)
        c_step = (cmax - cmin) / 10 if cmax != cmin else 1
        
        fig = go.Figure(data=[go.Surface(
            z=Z, x=X, y=Y,
            contours = {
                "z": {"show": True, "start": cmin, "end": cmax, "size": c_step, "color":"white"}
            },
            colorscale='Viridis' if theme == "dark" else 'Plasma',
            showscale=False
        )])
        
        _setup_layout(fig, theme, "", "X Axis", "Y Axis", "Z Axis")
        return fig, []
    except Exception as e:
        return None, [f"Error computing 3D function: {str(e)}"]

def _setup_layout(fig, theme, title, xaxis_title, yaxis_title, zaxis_title=None):
    is_dark = theme == "dark"
    bg_color = "rgba(0,0,0,0)"
    text_color = "#fafafa" if is_dark else "#1c1917"
    grid_color = "#3f3f46" if is_dark else "#d6d3d1"
    
    if zaxis_title:
        fig.update_layout(
            scene=dict(
                xaxis_title=xaxis_title,
                yaxis_title=yaxis_title,
                zaxis_title=zaxis_title,
                xaxis=dict(gridcolor=grid_color, backgroundcolor=bg_color, showbackground=False),
                yaxis=dict(gridcolor=grid_color, backgroundcolor=bg_color, showbackground=False),
                zaxis=dict(gridcolor=grid_color, backgroundcolor=bg_color, showbackground=False)
            ),
            paper_bgcolor=bg_color,
            plot_bgcolor=bg_color,
            font=dict(color=text_color),
            margin=dict(l=0, r=0, b=0, t=0),
            title=title
        )
    else:
        fig.update_layout(
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            paper_bgcolor=bg_color,
            plot_bgcolor=bg_color,
            font=dict(color=text_color, family="Inter"),
            xaxis=dict(gridcolor=grid_color, zerolinecolor=text_color, zerolinewidth=1.5),
            yaxis=dict(gridcolor=grid_color, zerolinecolor=text_color, zerolinewidth=1.5),
            margin=dict(l=20, r=20, b=20, t=20),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0.4)"),
            hovermode="x unified"
        )
