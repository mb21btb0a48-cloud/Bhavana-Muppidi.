import streamlit as st
import base64
import time
import plotly.graph_objects as go
import pandas as pd

def hide_default_ui():
    st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def apply_global_css():
    st.markdown("""
    <style>
    /* ========================================================================= */
    /* PREMIUM UI THEME: Ultra-Clean Light Mode                                  */
    /* ========================================================================= */
    
    /* 1. Global Page Background (Soft Blue-Grey) */
    .stApp { background-color: #f8fafc !important; font-family: 'Inter', -apple-system, sans-serif !important; }
    
    /* 2. Text Colors & Aggressive Overrides */
    .stMarkdownContainer p, [data-testid="stWidgetLabel"] p, .stRadio label, .stSelectbox label, .stTextInput label, .stNumberInput label { 
        color: #1e293b !important; font-weight: 500 !important;
    }
    
    /* Force Radio Group Text Visibility */
    div[role="radiogroup"] label p, div[role="radiogroup"] label div { color: #0f172a !important; font-weight: 700 !important; }
    
    /* Force Tab Text Visibility */
    button[data-baseweb="tab"] p, button[data-baseweb="tab"] div, button[data-baseweb="tab"] span { color: #64748b !important; font-weight: 700 !important; }
    button[data-baseweb="tab"][aria-selected="true"] p, button[data-baseweb="tab"][aria-selected="true"] div, button[data-baseweb="tab"][aria-selected="true"] span { color: #2563eb !important; }
    
    /* 3. Section Headers */
    .section-header-wrapper {
        text-align: left; margin-top: 50px; margin-bottom: 25px;
    }
    .section-header {
        color: #0f172a !important; display: inline-block; border-bottom: 5px solid #2563eb;
        padding-bottom: 8px; font-weight: 900; margin: 0; font-size: 32px; text-transform: uppercase; letter-spacing: 1px;
    }
    
    /* 4. Top Hero Banner (Vibrant Gradient) */
    .hero-banner {
        padding: 60px 40px; background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 50%, #2563eb 100%);
        border-radius: 24px; box-shadow: 0 10px 25px rgba(37, 99, 235, 0.15);
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;
    }
    .hero-banner-title { margin: 0; font-size: 48px; font-weight: 900; color: #ffffff !important; letter-spacing: -1.5px; line-height: 1.1; }
    .hero-banner-sub { margin-top: 15px; font-size: 19px; color: rgba(255,255,255,0.95) !important; font-weight: 500; }
    
    /* 5. Clean White Boxes & Input Containers */
    .login-box, .analysis-box, .loading-box, .consistency-box, .daily-meal-box, .clinical-row {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        color: #1f2937 !important;
    }
    .analysis-box { padding: 40px; margin-bottom: 30px; border-top: 6px solid #3b82f6; }
    .clinical-row { padding: 25px; margin-bottom: 25px; background: #f8fafc !important; border: 1px dashed #cbd5e1; }
    
    /* 6. Professional Badge Utility */
    .gps-badge {
        transition: all 0.3s ease;
        cursor: default;
        user-select: none;
    }
    .gps-badge:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }

    /* 7. Enhanced Form Styling */
    input, select, textarea {
        border-radius: 12px !important;
        border: 1px solid #d1d5db !important;
        padding: 12px !important;
        font-weight: 500 !important;
    }
    input:focus { border-color: #3b82f6 !important; box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important; }
    
    /* 8. Section Strategy Styling */
    .strategy-container {
        background: #f1f5f9;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    
    .consistency-box { padding: 60px 40px; text-align: center; margin: 30px 0 60px; border-radius: 24px; border: none; background: linear-gradient(135deg, #10b981 0%, #059669 100%); box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3); position: relative; overflow: hidden; }
    .consistency-box h2 { color: #ffffff !important; font-weight: 900; font-size: 40px; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 2px; }
    
    /* 6. Hover Cards (Nutrients & Foods) */
    .hover-card {
        padding: 30px; border-radius: 20px; border: 1px solid #e2e8f0;
        background-color: #ffffff !important; color: #1e293b !important;
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); height: 100%;
    }
    .hover-card:hover { transform: translateY(-8px) scale(1.02); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); border-color: #cbd5e1; }
    .hover-card h4 { color: #111827 !important; margin: 0; font-weight: 800; }
    .food-title { color: #111827 !important; font-weight: 700; font-size: 18px; margin: 0; }
    .small-desc { color: #4b5563 !important; font-size: 14px; margin-top: 8px; line-height: 1.5; }
    .avoid-card { border-left: 6px solid #ef4444 !important; display: flex; align-items: center; gap: 20px; border-radius: 16px; padding: 24px; }
    
    /* Widget Label Visibility */
    label[data-testid="stWidgetLabel"] p, .stAudio label { color: #111827 !important; font-weight: 600 !important; }
    
    /* Checkbox Label Visibility */
    .stCheckbox label p, .stCheckbox span { color: #111827 !important; font-weight: 500 !important; }
    
    /* 7. Meal Plan Headers */
    .meal-header { padding: 18px; border-radius: 16px 16px 0 0; text-align: center; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-bottom: 3px solid #16a34a; }
    .meal-header h4 { color: #166534 !important; margin: 0; font-weight: 800; }
    
    /* 8. Diagnostic Table */
    .custom-table { width: 100%; border-collapse: separate; border-spacing: 0 10px; margin-top: 15px; }
    .custom-table th { padding: 12px 22px; color: #6b7280 !important; text-transform: uppercase; letter-spacing: 1px; font-size: 12px; text-align: left; font-weight: 700; }
    .custom-table tr { background-color: #ffffff; box-shadow: 0 2px 5px rgba(0,0,0,0.02); border-radius: 12px; border: 1px solid #e5e7eb; }
    .custom-table td { padding: 22px; color: #1f2937 !important; }
    .custom-table .test-name { font-weight: 700; font-size: 15px; color: #111827 !important; }
    .custom-table .patient-val { font-size: 18px; font-weight: 900; font-family: monospace; color: #111827 !important; }
    .custom-table .ref-range { font-size: 13px; color: #6b7280 !important; font-weight: 500; }
    
    /* Splash Screen */
    @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-12px); } }
    @keyframes pulse { 0%, 100% { opacity: 0.1; } 50% { opacity: 1; transform: scale(1.1); } }
    @keyframes loadBar { 0% { transform: translateX(-100%); } 100% { transform: translateX(0); } }

    /* 9. Tooltips (<details>) */
    details { margin-top: 10px; background: #f9fafb; padding: 10px 15px; border-radius: 8px; border: 1px solid #e5e7eb; cursor: pointer; transition: background 0.2s ease; }
    details:hover { background: #f3f4f6; }
    details summary { font-weight: 700; color: #4f46e5 !important; font-size: 13px; outline: none; list-style: none; display: flex; align-items: center; gap: 5px; }
    details summary::-webkit-details-marker { display: none; }
    details[open] summary { margin-bottom: 8px; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }
    details p { margin: 0; font-size: 13px; color: #4b5563 !important; line-height: 1.5; }

    /* 10. Cyclic Loading Text Animation */
    @keyframes textCycle {
        0%, 25% { opacity: 1; transform: translateY(0); }
        30%, 100% { opacity: 0; transform: translateY(-10px); }
    }
    .loading-text-container { position: relative; height: 30px; overflow: hidden; margin-top: 20px; text-align: center; }
    .loading-text { position: absolute; width: 100%; top: 0; left: 0; opacity: 0; font-weight: 700; color: #4b5563 !important; font-size: 18px; }
    .lt-1 { animation: textCycle 8s infinite 0s; }
    .lt-2 { animation: textCycle 8s infinite 2s; }
    .lt-3 { animation: textCycle 8s infinite 4s; }
    .lt-4 { animation: textCycle 8s infinite 6s; }

    /* 11. Print CSS (PDF Export) */
    @media print {
        header, footer, .stSidebar, button[kind="secondary"], button[kind="primary"], div[data-testid="stSidebar"], div[data-testid="stToolbar"] { display: none !important; }
        .stApp { background-color: white !important; }
        .hover-card, .analysis-box, .consistency-box { break-inside: avoid; box-shadow: none !important; border: 1px solid #ccc !important; }
        .custom-table tr { break-inside: avoid; }
        @page { margin: 1.5cm; }
    /* 12. Authentication / Verification Screen Styles */
    .auth-container {
        display: flex; justify-content: center; align-items: center; min-height: 80vh;
    }
    .auth-card {
        background: #ffffff; padding: 50px; border-radius: 32px; width: 100%; max-width: 500px;
        box-shadow: 0 25px 50px -12px rgba(0,0,0,0.1); border: 1px solid #f1f5f9;
        text-align: center;
    }
    .auth-title { font-size: 32px; font-weight: 900; color: #0f172a; margin-bottom: 8px; letter-spacing: -0.5px; }
    .auth-subtitle { font-size: 16px; color: #64748b; margin-bottom: 35px; line-height: 1.5; }
    .auth-icon { font-size: 60px; margin-bottom: 20px; animation: float 3s ease-in-out infinite; }
    
    .stTextInput > div > div > input {
        text-align: center; font-size: 18px !important; letter-spacing: 2px; font-weight: 700 !important;
        height: 55px !important; border-radius: 14px !important;
    }
    .otp-input > div > div > input {
        letter-spacing: 12px !important; font-size: 24px !important;
    }
    </style>
    """, unsafe_allow_html=True)

def show_splash_screen():
    if 'app_loaded' not in st.session_state:
        st.session_state.app_loaded = False
    if not st.session_state.app_loaded:
        splash = st.empty()
        clean_html = """
        <div style="position:fixed; top:0; left:0; width:100vw; height:100vh; background:#f3f4f6; z-index:9999; display:flex; flex-direction:column; align-items:center; justify-content:center; font-family:'Inter', sans-serif;">
            <div style="display:flex; align-items:center; justify-content:center; gap:20px; font-size:85px;">
                <div style="animation: float 2s ease-in-out infinite;">🩺</div>
                <div style="font-size:45px; color:#4f46e5; animation: pulse 1.5s infinite;">➔</div>
                <div style="animation: float 2s ease-in-out infinite; animation-delay:0.4s;">🥗</div>
            </div>
            <h2 style="font-family:sans-serif; color:#111827; margin-top:35px; letter-spacing:1px; font-size:26px; font-weight:900;">
                AI HEALTH TO FOOD
            </h2>
            <div style="margin-top:40px; width:220px; height:6px; background:#e5e7eb; border-radius:3px; overflow:hidden;">
                <div style="width:100%; height:100%; background:#4f46e5; animation: loadBar 2.6s cubic-bezier(0.4, 0.0, 0.2, 1) forwards;"></div>
            </div>
        </div>
        """
        splash.markdown(clean_html, unsafe_allow_html=True)
        time.sleep(2.7)
        splash.empty()
        st.session_state.app_loaded = True

def styled_header(text):
    st.markdown(f"""
    <div class="section-header-wrapper">
        <h2 class="section-header">{text}</h2>
    </div>
    """, unsafe_allow_html=True)

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

def render_top_banner(lottie_anim=None):
    logo_b64 = get_base64_of_bin_file('logo.png')
    if logo_b64:
        visual_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 130px; animation: float 4s ease-in-out infinite; filter: drop-shadow(0 0 10px rgba(255,255,255,0.05));">'
    else:
        visual_html = '<div style="font-size: 60px; animation: float 4s ease-in-out infinite;">🧬</div>'

    st.markdown(f"""
    <div class="hero-banner">
        <div>
            <h1 class="hero-banner-title">AI Health Dashboard ✨</h1>
            <p class="hero-banner-sub">Smart, real-time food and health recommendations powered by AI Vision.</p>
        </div>
        <div>
            {visual_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_diagnostic_table(diagnostics, is_manual=False):
    html_parts = [
        '<table class="custom-table">',
        '<thead><tr>',
        '<th>Test Name</th>'
    ]
    if not is_manual:
        html_parts.extend(['<th>Your Value</th>', '<th>Trend</th>', '<th>Visual Status</th>'])
    html_parts.extend(['<th>Reference Range</th>', '<th>Interpretation</th>', '</tr></thead><tbody>'])
    
    for test in diagnostics:
        status_norm = str(getattr(test, "status", "")).lower()
        severity = getattr(test, "severity_score", 50)
        
        # Clinical zone mapping (Defensive Calibration)
        is_high = any(k in status_norm for k in ["high", "elevated", "attention", "warning", "critical", "borderline"])
        is_low = any(k in status_norm for k in ["low", "deficient", "anaemic", "insufficient"])
        
        if is_high:
            if severity < 67: severity = 85
            marker_color = "#ff4b4b" # Red
            gauge_color = "#ff4b4b"
        elif is_low:
            if severity > 33 or severity < 1: severity = 15
            marker_color = "#ffcc00" # Yellow
            gauge_color = "#ffcc00"
        else: # Normal or Stable
            if severity < 34 or severity > 66: severity = 50
            marker_color = "#4CAF50" # Green
            gauge_color = "#4CAF50"

        row_html = f'<tr><td class="test-name">{test.test_name}</td>'
        if not is_manual:
            trend = getattr(test, "trend", "")
            trend_html = ""
            if "improv" in trend.lower(): trend_html = f'<td style="color: #10b981; font-weight: bold; font-size: 13px;">⬆️ {trend}</td>'
            elif "degrad" in trend.lower() or "worsen" in trend.lower(): trend_html = f'<td style="color: #ef4444; font-weight: bold; font-size: 13px;">⬇️ {trend}</td>'
            else: trend_html = f'<td style="color: #6b7280; font-size: 13px;">{trend}</td>'
            
            row_html += f"""<td class="patient-val">{test.patient_value}</td>
{trend_html}
<td>
<div style="position: relative; height: 25px; width: 100%; display: flex; align-items: center; margin-bottom: 5px;">
    <div style="position: absolute; width: 100%; height: 8px; background: linear-gradient(90deg, #ffcc00 0%, #ffcc00 33%, #4CAF50 34%, #4CAF50 66%, #ff4b4b 67%, #ff4b4b 100%); border-radius: 4px; opacity: 0.25;"></div>
    <div style="position: absolute; left: calc({severity}% - 4px); width: 8px; height: 20px; background: {marker_color}; border: 2px solid white; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); z-index: 2;"></div>
</div>
<div style="display: flex; justify-content: space-between; font-size: 10px; font-weight: 800; color: #9ca3af; text-transform: uppercase;">
<span>Low</span><span>Normal</span><span>High</span>
</div>
</td>"""
        row_html += f"""<td class="ref-range">{test.value_range}</td>
<td style="color: {gauge_color if not is_manual else '#111827'}; font-weight: 800; font-size: 14px;">{test.interpretation}</td></tr>"""
        html_parts.append(row_html)
        
    html_parts.append("</tbody></table>")
    st.write("".join(html_parts), unsafe_allow_html=True)

def render_medical_disclaimer():
    st.markdown("""
    <div style="background: #f9fafb; color: #4b5563; padding: 40px; text-align: center; border-radius: 16px 16px 0 0; margin-top: 50px; border-top: 1px solid #e5e7eb; border-left: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb; box-shadow: 0 -4px 6px -1px rgba(0,0,0,0.02);">
        <h4 style="color: #111827 !important; margin-top: 0; font-weight: 800; font-size: 18px;">⚠️ Medical Disclaimer</h4>
        <p style="font-size: 14px; opacity: 0.9; max-width: 800px; margin: 0 auto; line-height: 1.6;">
            This AI Health Dashboard provides nutritional and lifestyle suggestions based on standard guidelines.
            <strong>This is NOT a substitute for professional medical advice, diagnosis, or treatment.</strong>
            Always seek the advice of your physician or qualified health provider.
        </p>
    </div>
    """, unsafe_allow_html=True)
def render_nutrient_pie_chart(item, key=None):
    """Render a premium pie chart for a single food item."""
    import plotly.graph_objects as go
    labels = ['Protein (g)', 'Carbs (g)', 'Fats (g)']
    values = [item.protein, item.carbs, item.fats]
    colors = ['#6366f1', '#10b981', '#f59e0b']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.5,
        textinfo='label+percent',
        marker=dict(colors=colors, line=dict(color='#ffffff', width=3)),
        hoverinfo='label+value+percent'
    )])
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(text=f'<b>{item.calories}</b><br>kcal', x=0.5, y=0.5, font=dict(size=16, color="#1e293b"), showarrow=False)],
        title=dict(text=f"📊 Breakdown: {item.name}", font=dict(size=14, color="#0f172a"), x=0.5, xanchor='center', yanchor='top'),
        transition=dict(duration=800, easing='cubic-in-out')
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=key)

def render_chart_placeholder():
    """Render a premium pulse placeholder when no data is logged."""
    st.markdown("""
    <div style="height: 320px; display: flex; align-items: center; justify-content: center; background: #f8fafc; border: 2px dashed #e2e8f0; border-radius: 50%; margin: 10px auto; width: 220px; position: relative; overflow: hidden;">
        <style>
            @keyframes pulse-ring {
                0% { transform: scale(.33); }
                80%, 100% { opacity: 0; }
            }
            @keyframes pulse-dot {
                0% { transform: scale(.8); }
                50% { transform: scale(1); }
                100% { transform: scale(.8); }
            }
            .pulse-container { position: relative; width: 80px; height: 80px; }
            .pulse-ring { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 50%; background-color: #3b82f6; animation: pulse-ring 2s cubic-bezier(0.455, 0.03, 0.515, 0.955) infinite; }
            .pulse-dot { position: absolute; left: 20px; top: 20px; width: 40px; height: 40px; background-color: #3b82f6; border-radius: 50%; animation: pulse-dot 2s cubic-bezier(0.455, 0.03, 0.515, 0.955) -0.4s infinite; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 10px rgba(59, 130, 246, 0.5); }
        </style>
        <div class="pulse-container">
            <div class="pulse-ring"></div>
            <div class="pulse-dot">
                <span style="color: white; font-size: 20px;">🩺</span>
            </div>
        </div>
        <div style="position: absolute; bottom: 40px; width: 100%; text-align: center; color: #94a3b8; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Ready to Track</div>
    </div>
    """, unsafe_allow_html=True)

def render_body_progress_chart(consumed_total, targets, key=None):
    """Render a comparison of Current Intake vs Daily Targets."""
    import plotly.graph_objects as go
    metrics = ['Calories', 'Protein (g)', 'Carbs (g)', 'Fats (g)']
    consumed_vals = [consumed_total['calories'], consumed_total['protein'], consumed_total['carbs'], consumed_total['fats']]
    target_vals = [targets.calories, targets.protein, targets.carbs, targets.fats]
    
    # Calculate % progress for each
    labels = []
    for c, t, m in zip(consumed_vals, target_vals, metrics):
        pct = round((c/t)*100, 1) if t > 0 else 0
        labels.append(f"<b>{c}</b> / {t} ({pct}%)")

    fig = go.Figure()
    
    # Target bars (Gray background)
    fig.add_trace(go.Bar(
        name='Daily Target',
        y=metrics, x=target_vals,
        orientation='h',
        marker=dict(color='#e2e8f0', line=dict(color='#cbd5e1', width=1)),
        hoverinfo='skip',
        showlegend=False
    ))
    
    # Consumption bars (Colored)
    fig.add_trace(go.Bar(
        name='Current Intake',
        y=metrics, x=consumed_vals,
        orientation='h',
        marker=dict(
            color='#6366f1',
            line=dict(color='#4f46e5', width=1)
        ),
        text=labels,
        textposition='auto',
        insidetextanchor='start',
        textfont=dict(size=13)
    ))
    
    fig.update_layout(
        barmode='overlay',
        title=dict(text="🧬 Body Recovery & Intake Progress", font=dict(size=18, color="#0f172a", weight="bold")),
        height=350,
        margin=dict(l=10, r=30, t=60, b=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(autorange="reversed", tickfont=dict(size=13, color="#334155")),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=key)

def render_auth_screen():
    """Render the premium authentication gate."""
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    
    if not st.session_state.get('otp_sent'):
        st.markdown('<div class="auth-icon">🛡️</div>', unsafe_allow_html=True)
        st.markdown('<h1 class="auth-title">Verify Identity</h1>', unsafe_allow_html=True)
        st.markdown('<p class="auth-subtitle">Please provide your Aadhar & Mobile number to access the clinical dashboard.</p>', unsafe_allow_html=True)
        
        aadhar = st.text_input("Aadhar Number (12 Digits)", placeholder="XXXX XXXX XXXX", max_chars=12, key="auth_aadhar")
        mobile = st.text_input("Mobile Number", placeholder="+91 XXXXX XXXXX", key="auth_mobile")
        
        st.markdown("<br>", unsafe_allow_html=True)
        return aadhar, mobile, None
    else:
        st.markdown('<div class="auth-icon">📲</div>', unsafe_allow_html=True)
        st.markdown('<h1 class="auth-title">Enter OTP</h1>', unsafe_allow_html=True)
        st.markdown(f'<p class="auth-subtitle">A 6-digit verification code has been sent to <b>{st.session_state.verified_mobile}</b>.</p>', unsafe_allow_html=True)
        
        otp = st.text_input("Verification Code", placeholder="● ● ● ● ● ●", max_chars=6, key="auth_otp", help="Enter the 6-digit code sent via Twilio")
        
        st.markdown("<br>", unsafe_allow_html=True)
        return None, None, otp

def close_auth_card():
    st.markdown('</div></div>', unsafe_allow_html=True)
