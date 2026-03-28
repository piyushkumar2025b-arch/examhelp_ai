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

    elif chart_type == "waterfall":
        fig.add_trace(go.Waterfall(x=labels, y=values, measure=["relative"] * len(values),
                                   decreasing=dict(marker=dict(color="#f87171")),
                                   increasing=dict(marker=dict(color="#4ade80")),
                                   totals=dict(marker=dict(color="#60a5fa"))))
                                   
    elif chart_type == "funnel":
        fig.add_trace(go.Funnel(y=labels, x=values, marker=dict(color=colors)))

    elif chart_type == "treemap":
        # Simplified flat treemap
        fig.add_trace(go.Treemap(labels=labels, parents=[""]*len(labels), values=values, marker_colors=colors))
        
    elif chart_type == "sunburst":
        # Simplified flat sunburst
        fig.add_trace(go.Sunburst(labels=labels, parents=[""]*len(labels), values=values, marker_colors=colors))
        
    elif chart_type == "polar_scatter":
        # theta should be categories/angles, r is values
        fig.add_trace(go.Scatterpolar(r=values, theta=labels, mode='markers', marker=dict(size=12, color=colors[0])))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True)))

    elif chart_type == "violin":
        fig.add_trace(go.Violin(y=values, name="Group 1", line_color=colors[0]))
        if values2: fig.add_trace(go.Violin(y=values2, name="Group 2", line_color=colors[1]))
        
    elif chart_type == "bubble":
        sizes = data.get("sizes", values) if not values2 else values2
        fig.add_trace(go.Scatter(x=labels, y=values, mode='markers', marker=dict(size=sizes, color=colors[0], sizemode='area', sizeref=2.*max(sizes)/(40.**2), sizemin=4)))

    elif chart_type == "histogram":
        fig.add_trace(go.Histogram(x=values, marker_color=colors[0]))
        
    elif chart_type == "contour":
        fig.add_trace(go.Contour(z=[values, values2] if values2 else [values], colorscale='Viridis'))

    elif chart_type == "candlestick":
        o = data.get("open", values)
        h = data.get("high", [v*1.1 for v in values])
        l = data.get("low", [v*0.9 for v in values])
        c = data.get("close", values2 if values2 else values)
        fig.add_trace(go.Candlestick(x=labels, open=o, high=h, low=l, close=c))
        
    elif chart_type == "ohlc":
        o = data.get("open", values)
        h = data.get("high", [v*1.1 for v in values])
        l = data.get("low", [v*0.9 for v in values])
        c = data.get("close", values2 if values2 else values)
        fig.add_trace(go.Ohlc(x=labels, open=o, high=h, low=l, close=c))

    elif chart_type == "gauge":
        fig.add_trace(go.Indicator(mode="gauge+number", value=values[0] if values else 0, title={'text': "Gauge"}, gauge={'axis': {'range': [None, max(values) * 1.5] if values else [0, 100]}}))

    elif chart_type == "bullet":
        fig.add_trace(go.Indicator(mode="number+gauge+delta", value=values[0] if values else 0, title={'text': "Bullet"}, gauge={'shape': "bullet"}))

    elif chart_type == "scattergeo":
        fig.add_trace(go.Scattergeo(locations=labels, locationmode="country names", marker=dict(size=values, color=colors[0])))

    elif chart_type == "choropleth":
        fig.add_trace(go.Choropleth(locations=labels, locationmode="country names", z=values, colorscale="Viridis"))

    elif chart_type == "density_heatmap":
        fig.add_trace(go.Histogram2d(x=labels, y=values, colorscale='Viridis'))

    elif chart_type == "density_contour":
        fig.add_trace(go.Histogram2dContour(x=labels, y=values, colorscale='Viridis'))

    elif chart_type == "parcoords":
        fig.add_trace(go.Parcoords(line=dict(color=colors[0]), dimensions=[dict(label="D1", values=values), dict(label="D2", values=values2 if values2 else values)]))

    elif chart_type == "scatterternary":
        a = data.get("a", values)
        b = data.get("b", values2 if values2 else values)
        c_vals = data.get("c", [max(0, 100 - x - y) for x, y in zip(a, b)])
        fig.add_trace(go.Scatterternary(a=a, b=b, c=c_vals, mode='markers', marker=dict(color=colors[0], size=10)))

    elif chart_type == "carpet":
        fig.add_trace(go.Carpet(a=labels, b=values, y=values2 if values2 else values))

    elif chart_type == "funnelarea":
        fig.add_trace(go.Funnelarea(labels=labels, values=values, marker=dict(colors=colors)))

    elif chart_type == "icicle":
        fig.add_trace(go.Icicle(labels=labels, parents=[""]*len(labels), values=values))

    elif chart_type == "barpolar":
        fig.add_trace(go.Barpolar(r=values, theta=labels, marker_color=colors))

    elif chart_type == "error_bar":
        fig.add_trace(go.Scatter(x=labels, y=values, error_y=dict(type='data', array=values2 if values2 else [v*0.1 for v in values], visible=True), mode='markers', marker=dict(size=8, color=colors[0])))

    elif chart_type == "contourcarpet":
        fig.add_trace(go.Contourcarpet(a=labels, b=values, z=values2 if values2 else values))

    elif chart_type == "scattercarpet":
        fig.add_trace(go.Scattercarpet(a=labels, b=values, marker=dict(color=colors[0], size=10)))

    elif chart_type == "parcats":
        fig.add_trace(go.Parcats(dimensions=[dict(label="Cat 1", values=labels), dict(label="Cat 2", values=values)]))

    elif chart_type == "sankey":
        fig.add_trace(go.Sankey(node=dict(pad=15, thickness=20, label=labels, color=colors), link=dict(source=[0]*len(values), target=list(range(1, len(values)+1)), value=values)))

    elif chart_type == "table":
        fig.add_trace(go.Table(header=dict(values=["<b>Categories</b>", "<b>Values</b>"], fill_color=colors[0], font=dict(color="white")), cells=dict(values=[labels, values], fill_color=colors[1] if len(colors)>1 else "#333")))

    elif chart_type == "splom":
        fig.add_trace(go.Splom(dimensions=[dict(label="D1", values=labels), dict(label="D2", values=values), dict(label="D3", values=values2 if values2 else values)], marker=dict(color=colors[0], size=7)))

    elif chart_type == "scattermapbox":
        fig.add_trace(go.Scattermapbox(lat=values, lon=values2 if values2 else values, mode='markers', marker=dict(size=14, color=colors[0])))
        fig.update_layout(mapbox_style="carto-darkmatter" if theme=="dark" else "carto-positron")

    elif chart_type == "densitymapbox":
        fig.add_trace(go.Densitymapbox(lat=values, lon=values2 if values2 else values, z=[1]*len(values), radius=10))
        fig.update_layout(mapbox_style="carto-darkmatter" if theme=="dark" else "carto-positron")

    elif chart_type == "cone":
        fig.add_trace(go.Cone(x=labels, y=values, z=values2 if values2 else values, u=values, v=values, w=values, colorscale='Turbo'))

    elif chart_type == "streamtube":
        fig.add_trace(go.Streamtube(x=labels, y=values, z=values2 if values2 else values, u=values, v=values, w=values, colorscale='Turbo'))

    elif chart_type == "mesh3d":
        fig.add_trace(go.Mesh3d(x=labels, y=values, z=values2 if values2 else values, opacity=0.5, color=colors[0]))

    elif chart_type == "volume":
        fig.add_trace(go.Volume(x=labels, y=values, z=values2 if values2 else values, value=values, isomin=0.1, isomax=0.8, opacity=0.1, surface_count=17))

    elif chart_type == "isosurface":
        fig.add_trace(go.Isosurface(x=labels, y=values, z=values2 if values2 else values, value=values, isomin=0.1, isomax=0.8, caps=dict(x_show=False, y_show=False)))

    elif chart_type == "scattergl":
        fig.add_trace(go.Scattergl(x=labels, y=values, mode='markers', marker=dict(color=colors[0], size=8)))

    elif chart_type == "gantt" or chart_type == "timeline":
        for i, (l, v) in enumerate(zip(labels, values)): fig.add_trace(go.Bar(x=[v], y=[l], orientation='h', marker_color=colors[i%len(colors)]))

    elif chart_type in ["bar_stacked", "bar_relative"]:
        fig.add_trace(go.Bar(x=labels, y=values, name="Group A", marker_color=colors[0]))
        if values2: fig.add_trace(go.Bar(x=labels, y=values2, name="Group B", marker_color=colors[1]))
        fig.update_layout(barmode="stack" if chart_type=="bar_stacked" else "relative")

    elif chart_type == "step":
        fig.add_trace(go.Scatter(x=labels, y=values, mode='lines', line_shape='hv', line_color=colors[0]))

    elif chart_type == "spline":
        fig.add_trace(go.Scatter(x=labels, y=values, mode='lines', line_shape='spline', line_color=colors[0]))

    elif chart_type == "filled_step":
        fig.add_trace(go.Scatter(x=labels, y=values, mode='lines', line_shape='hv', fill='tozeroy', fillcolor=colors[0], line_color=colors[0]))

    elif chart_type == "polar_line":
        fig.add_trace(go.Scatterpolar(r=values, theta=labels, mode='lines', line_color=colors[0]))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True)))

    elif chart_type == "lollipop":
        fig.add_trace(go.Scatter(x=labels, y=values, mode='markers', marker=dict(size=12, color=colors[0])))
        for i in range(len(labels)): fig.add_trace(go.Scatter(x=[labels[i], labels[i]], y=[0, values[i]], mode='lines', line=dict(color=colors[0], width=2), showlegend=False))

    elif chart_type == "slope_chart":
        if values2:
            for i in range(len(labels)): fig.add_trace(go.Scatter(x=["Start", "End"], y=[values[i], values2[i]], mode='lines+markers', line=dict(width=3), name=labels[i]))

    elif chart_type == "dumbbell":
        if values2:
            for i in range(len(labels)): fig.add_trace(go.Scatter(x=[values[i], values2[i]], y=[labels[i], labels[i]], mode='lines+markers', marker=dict(size=10), line=dict(width=3), name=labels[i], orientation='h'))

    elif chart_type == "indicator_number":
        fig.add_trace(go.Indicator(mode="number", value=values[0] if values else 0, title={'text': "Metric"}))

    elif chart_type == "indicator_delta":
        fig.add_trace(go.Indicator(mode="number+delta", value=values[0] if values else 0, delta={'reference': values2[0] if values2 else 0}, title={'text': "Delta"}))

    elif chart_type == "scatter_smith":
        fig.add_trace(go.Scattersmith(real=values, imag=values2 if values2 else values, marker=dict(color=colors[0], size=10)))

    elif chart_type == "heatmap_annotated":
        z_data = [values, values2] if values2 else [values, values]
        fig.add_trace(go.Heatmap(z=z_data, x=labels, y=["Row 1", "Row 2"], colorscale='Turbo', texttemplate="%{z}", textfont={"size": 16}))

    elif chart_type == "pointcloud":
        fig.add_trace(go.Pointcloud(x=labels, y=values, marker=dict(color=colors[0], sizemin=0.5, sizemax=100)))

    elif chart_type == "surface":
        z_mat = [values, values2] if values2 else [values, values]
        fig.add_trace(go.Surface(z=z_mat, colorscale='Magma'))

    _setup_layout(fig, theme, title, "X Axis / Categories", "Y Axis / Values")
    return fig, []

def plot_polar_graph(function_str, theta_min=0, theta_max=12.566, points=2000, theme="dark"):
    """Plot beautiful mathematical polar roses and spirals (r = f(theta))."""
    try:
        from sympy import symbols
        theta_sym = symbols('theta')
        expr, fun = _safe_lambdify(function_str, theta_sym)
        if fun is None: return None, [f"Invalid function: {expr}"]
    except Exception:
        return None, ["Math engine not imported."]
        
    theta_vals = np.linspace(theta_min, theta_max, points)
    try:
        r_vals = fun(theta_vals)
        if np.isscalar(r_vals): r_vals = np.full_like(theta_vals, r_vals)
        r_vals = np.where(np.abs(r_vals) > 1e6, np.nan, r_vals)
        
        fig = go.Figure(go.Scatterpolar(
            r=r_vals, theta=np.degrees(theta_vals), mode='lines', 
            line=dict(color='#c084fc', width=3), 
            name=f"r = {function_str}"
        ))
        _setup_layout(fig, theme, f"Polar Plot: r = {function_str}", "", "")
        fig.update_layout(polar=dict(
            radialaxis=dict(visible=True, showline=False, gridcolor="rgba(100,100,100,0.3)"), 
            angularaxis=dict(direction="counterclockwise", gridcolor="rgba(100,100,100,0.3)")
        ))
        return fig, []
    except Exception as e:
        return None, [f"Error computing polar function: {e}"]

def plot_parametric_3d(x_function, y_function, z_function, t_min=0, t_max=31.415, points=2000, theme="dark"):
    """Plot extraordinary 3D Parametric curves (x(t), y(t), z(t)) like DNA helices and orbital mechanics."""
    try:
        from sympy import symbols
        t_sym = symbols('t')
        x_ex, x_f = _safe_lambdify(x_function, t_sym)
        y_ex, y_f = _safe_lambdify(y_function, t_sym)
        z_ex, z_f = _safe_lambdify(z_function, t_sym)
    except Exception:
        return None, ["Math engine not imported."]
        
    t_vals = np.linspace(t_min, t_max, points)
    try:
        X = x_f(t_vals); Y = y_f(t_vals); Z = z_f(t_vals)
        if np.isscalar(X): X = np.full_like(t_vals, X)
        if np.isscalar(Y): Y = np.full_like(t_vals, Y)
        if np.isscalar(Z): Z = np.full_like(t_vals, Z)
        
        color_val = np.linspace(0, 1, points)
        fig = go.Figure(go.Scatter3d(
            x=X, y=Y, z=Z, mode='lines',
            line=dict(color=color_val, colorscale='Turbo', width=6)
        ))
        _setup_layout(fig, theme, "Parametric 3D Plot", "X(t)", "Y(t)", "Z(t)")
        fig.update_layout(scene_camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)))
        return fig, []
    except Exception as e:
        return None, [f"Parametric 3D Error: {e}"]
