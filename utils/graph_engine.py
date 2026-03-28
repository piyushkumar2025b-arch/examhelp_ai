import numpy as np
import plotly.graph_objects as go

try:
    from sympy import sympify, symbols, lambdify, diff
except ImportError:
    sympify = symbols = lambdify = diff = None

def _safe_lambdify(expr_str, var_symbols):
    if sympify is None:
        return None, "Error: Math engine (sympy) is not installed."
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
        
        colorscales = ['Viridis', 'Plasma', 'Inferno', 'Magma', 'Turbo']
        selected_cs = np.random.choice(colorscales) if theme == "dark" else 'IceFire'

        fig = go.Figure(data=[go.Surface(
            z=Z, x=X, y=Y,
            contours_z=dict(show=True, usecolormap=True, highlightcolor="limegreen", project_z=True),
            colorscale=selected_cs,
            lighting=dict(ambient=0.6, diffuse=0.8, roughness=0.1, specular=1.5, fresnel=0.2),
            showscale=True,
            colorbar=dict(title="Z Value", len=0.8, thickness=15)
        )])
        
        _setup_layout(fig, theme, "", "X Axis", "Y Axis", "Z Axis")
        
        # Next-level 3D camera angles
        fig.update_layout(scene_camera=dict(
            up=dict(x=0, y=0, z=1),
            center=dict(x=0, y=0, z=0),
            eye=dict(x=1.5, y=1.5, z=1.2)
        ))
        
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

def generate_advanced_chart(data, chart_type="bar", title="Advanced Data Chart", theme="dark"):
    """
    Generates extraordinary data charts: bar, line, pie, donut, scatter, 3d_scatter, radar, heatmap, area, box.
    Expects data as a dict: {"labels": [...], "values": [...], "values2": [...]} optionally.
    """
    import pandas as pd
    import plotly.express as px

    fig = go.Figure()
    labels = data.get("labels", [f"Item {i+1}" for i in range(len(data.get("values", [])))])
    values = data.get("values", [])
    values2 = data.get("values2", None)

    colors = px.colors.qualitative.Plotly if theme == "dark" else px.colors.qualitative.Pastel

    if chart_type == "bar":
        fig.add_trace(go.Bar(x=labels, y=values, marker_color=colors[0], name="Value 1", text=values, textposition='auto'))
        if values2:
            fig.add_trace(go.Bar(x=labels, y=values2, marker_color=colors[1], name="Value 2", text=values2, textposition='auto'))
        fig.update_layout(barmode='group')

    elif chart_type == "line" or chart_type == "area":
        fill_mode = 'tozeroy' if chart_type == "area" else 'none'
        fig.add_trace(go.Scatter(x=labels, y=values, mode='lines+markers', line=dict(width=3, color=colors[0]), fill=fill_mode, name="Value 1"))
        if values2:
            fig.add_trace(go.Scatter(x=labels, y=values2, mode='lines+markers', line=dict(width=3, color=colors[1]), fill=fill_mode, name="Value 2"))

    elif chart_type in ["pie", "donut"]:
        hole = 0.5 if chart_type == "donut" else 0
        fig.add_trace(go.Pie(labels=labels, values=values, hole=hole, marker=dict(colors=colors),
                             textinfo='label+percent', hoverinfo='label+value'))

    elif chart_type == "scatter":
        fig.add_trace(go.Scatter(x=labels, y=values, mode='markers', marker=dict(size=12, color=colors[2], line=dict(width=2, color='DarkSlateGrey')), name="Data"))

    elif chart_type == "radar":
        fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=labels + [labels[0]], fill='toself', name='Data 1', line_color=colors[0]))
        if values2:
            fig.add_trace(go.Scatterpolar(r=values2 + [values2[0]], theta=labels + [labels[0]], fill='toself', name='Data 2', line_color=colors[1]))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(max(values), max(values2) if values2 else 0)*1.2])))

    elif chart_type == "3d_scatter":
        if values2:
            fig.add_trace(go.Scatter3d(x=labels, y=values, z=values2, mode='markers',
                                       marker=dict(size=8, color=values, colorscale='Viridis', opacity=0.8)))

    elif chart_type == "heatmap":
        if values2:
            z_data = [values, values2]
            fig.add_trace(go.Heatmap(z=z_data, x=labels, y=["Metric 1", "Metric 2"], colorscale='Viridis'))

    elif chart_type == "box":
        fig.add_trace(go.Box(y=values, name="Group 1", marker_color=colors[0]))
        if values2:
            fig.add_trace(go.Box(y=values2, name="Group 2", marker_color=colors[1]))

    _setup_layout(fig, theme, title, "X Axis / Categories", "Y Axis / Values")
    return fig, []
