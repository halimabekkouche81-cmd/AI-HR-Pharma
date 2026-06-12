from pathlib import Path
import streamlit as st


def get_logo_path() -> str:
    logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
    return str(logo_path)


def get_theme_tokens():
    return {
        "brand_primary": "#1D4ED8",
        "brand_secondary": "#0EA5E9",
        "brand_dark": "#081120",
        "surface": "rgba(255,255,255,0.84)",
        "surface_strong": "rgba(255,255,255,0.92)",
        "surface_dark": "rgba(8,17,32,0.94)",
        "border_soft": "#DBEAFE",
        "border_strong": "#BFDBFE",
        "text_main": "#0F172A",
        "text_muted": "#64748B",
        "text_soft": "#94A3B8",
        "success": "#16A34A",
        "warning": "#D97706",
        "danger": "#DC2626",
        "violet": "#7C3AED",
        "slate": "#334155",
        "radius_xl": "28px",
        "radius_lg": "22px",
        "radius_md": "16px",
    }


def _tone_styles(tone: str):
    tones = {
        "blue": {
            "accent": "#2563EB",
            "bg": "#EFF6FF",
            "text": "#1D4ED8",
            "soft": "rgba(37,99,235,0.10)",
        },
        "cyan": {
            "accent": "#0891B2",
            "bg": "#ECFEFF",
            "text": "#0E7490",
            "soft": "rgba(8,145,178,0.10)",
        },
        "green": {
            "accent": "#16A34A",
            "bg": "#F0FDF4",
            "text": "#15803D",
            "soft": "rgba(22,163,74,0.10)",
        },
        "amber": {
            "accent": "#D97706",
            "bg": "#FFF7ED",
            "text": "#B45309",
            "soft": "rgba(217,119,6,0.10)",
        },
        "red": {
            "accent": "#DC2626",
            "bg": "#FEF2F2",
            "text": "#B91C1C",
            "soft": "rgba(220,38,38,0.10)",
        },
        "violet": {
            "accent": "#7C3AED",
            "bg": "#F5F3FF",
            "text": "#6D28D9",
            "soft": "rgba(124,58,237,0.10)",
        },
        "slate": {
            "accent": "#475569",
            "bg": "#F8FAFC",
            "text": "#334155",
            "soft": "rgba(71,85,105,0.08)",
        },
    }
    return tones.get(tone, tones["blue"])


def apply_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(59,130,246,0.10), transparent 28%),
                radial-gradient(circle at top left, rgba(14,165,233,0.08), transparent 24%),
                linear-gradient(180deg, #F8FBFF 0%, #F3F7FC 48%, #EEF4FF 100%);
            color: #0F172A;
        }

        #MainMenu, header, footer {visibility: hidden;}

        .main .block-container {
            max-width: 1460px;
            padding: 1.5rem 2.4rem 2.8rem;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #0F172A;
            letter-spacing: -0.02em;
        }

        p, label, .stMarkdown, .stCaption {
            color: #334155;
        }

        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(191,219,254,0.75);
            border-radius: 20px;
            padding: 16px 18px;
            box-shadow: 0 16px 40px rgba(15,23,42,0.05);
            backdrop-filter: blur(10px);
        }

        [data-testid="stMetricLabel"] {
            color: #64748B;
            font-weight: 600;
        }

        [data-testid="stMetricValue"] {
            color: #0F172A;
            font-weight: 800;
        }

        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button {
            border: 1px solid rgba(29,78,216,0.16) !important;
            border-radius: 14px !important;
            min-height: 46px !important;
            font-weight: 700 !important;
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 60%, #1E40AF 100%) !important;
            color: #FFFFFF !important;
            box-shadow: 0 14px 30px rgba(37,99,235,0.18) !important;
            transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 18px 34px rgba(37,99,235,0.24) !important;
            filter: saturate(1.02);
        }

        .stButton > button:focus,
        .stFormSubmitButton > button:focus,
        .stDownloadButton > button:focus {
            box-shadow: 0 0 0 3px rgba(59,130,246,0.14), 0 18px 34px rgba(37,99,235,0.22) !important;
        }

        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea textarea,
        .stSelectbox [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {
            border-radius: 14px !important;
            border: 1px solid #D6E4FF !important;
            background: rgba(255,255,255,0.92) !important;
            box-shadow: 0 6px 14px rgba(15,23,42,0.04);
        }

        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stTextArea textarea:focus {
            border-color: #3B82F6 !important;
            box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background: rgba(255,255,255,0.72);
            padding: 8px;
            border-radius: 18px;
            border: 1px solid #DBEAFE;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 12px !important;
            height: 44px !important;
            font-weight: 700 !important;
            color: #475569 !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #2563EB 0%, #0EA5E9 100%) !important;
            color: #FFFFFF !important;
        }

        .stAlert {
            border-radius: 16px !important;
            border: 1px solid rgba(148,163,184,0.16) !important;
        }

        [data-testid="stDataFrame"],
        .stTable {
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid #DBEAFE;
            box-shadow: 0 12px 30px rgba(15,23,42,0.05);
            background: rgba(255,255,255,0.86);
        }

        .element-container iframe {
            border-radius: 20px !important;
        }

        .ui-panel {
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(191,219,254,0.82);
            border-radius: 24px;
            padding: 22px 24px;
            box-shadow: 0 18px 40px rgba(15,23,42,0.06);
            backdrop-filter: blur(10px);
            margin-bottom: 18px;
        }

        .ui-section-title {
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 16px;
            margin: 26px 0 14px;
        }

        .ui-section-title h3 {
            margin: 0;
            font-size: 1.08rem;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.02em;
        }

        .ui-section-title p {
            margin: 6px 0 0;
            color: #64748B;
            font-size: 0.93rem;
            line-height: 1.6;
        }

        .ui-header {
            position: relative;
            overflow: hidden;
            padding: 28px 32px;
            border-radius: 28px;
            background:
                linear-gradient(135deg, rgba(8,17,32,0.98) 0%, rgba(29,78,216,0.97) 50%, rgba(14,165,233,0.93) 100%);
            color: #FFFFFF;
            box-shadow: 0 24px 60px rgba(15,23,42,0.20);
            margin-bottom: 22px;
            border: 1px solid rgba(191,219,254,0.16);
        }

        .ui-header::before,
        .ui-header::after {
            content: "";
            position: absolute;
            border-radius: 999px;
            background: rgba(255,255,255,0.08);
        }

        .ui-header::before {
            width: 260px;
            height: 260px;
            top: -140px;
            right: -90px;
        }

        .ui-header::after {
            width: 180px;
            height: 180px;
            bottom: -105px;
            left: -55px;
        }

        .ui-header-top {
            position: relative;
            z-index: 1;
            display: flex;
            justify-content: space-between;
            gap: 24px;
            align-items: flex-start;
            flex-wrap: wrap;
        }

        .ui-header-kicker {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            color: rgba(219,234,254,0.92);
            margin-bottom: 12px;
            font-weight: 700;
        }

        .ui-header h1 {
            color: #FFFFFF !important;
            margin: 0;
            font-size: 2rem;
            line-height: 1.08;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .ui-header p {
            color: #DBEAFE;
            margin: 10px 0 0;
            max-width: 760px;
            font-size: 1rem;
            line-height: 1.7;
        }

        .ui-chip-row {
            position: relative;
            z-index: 1;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 18px;
        }

        .ui-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border-radius: 999px;
            padding: 8px 14px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.16);
            color: #FFFFFF;
            font-weight: 600;
            font-size: 0.9rem;
        }

        .ui-hero-stat {
            min-width: 150px;
            padding: 16px 18px;
            border-radius: 20px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.14);
            backdrop-filter: blur(8px);
        }

        .ui-hero-stat-label {
            color: #BFDBFE;
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 6px;
            font-weight: 700;
        }

        .ui-hero-stat-value {
            color: #FFFFFF;
            font-size: 1.35rem;
            font-weight: 800;
        }

        .ui-mini-card {
            background: rgba(255,255,255,0.88);
            border: 1px solid #DBEAFE;
            border-radius: 22px;
            padding: 18px 18px 16px;
            box-shadow: 0 14px 32px rgba(15,23,42,0.05);
            height: 100%;
        }

        .ui-mini-card .label {
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #64748B;
            margin-bottom: 10px;
            font-weight: 800;
        }

        .ui-mini-card .value {
            font-size: 1.8rem;
            font-weight: 800;
            color: #0F172A;
            line-height: 1.1;
        }

        .ui-mini-card .caption {
            margin-top: 10px;
            color: #64748B;
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .ui-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 999px;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            white-space: nowrap;
        }

        .ui-empty {
            text-align: center;
            padding: 28px 24px;
            border-radius: 22px;
            background: rgba(255,255,255,0.76);
            border: 1px dashed #BFDBFE;
            color: #64748B;
        }

        .ui-empty-title {
            font-size: 1.02rem;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str, icon=None, kicker: str = "AI-HR Pharma", chips=None, stats=None):
    chips = chips or []
    stats = stats or []

    stats_html = "".join(
        f"""
        <div class='ui-hero-stat'>
            <div class='ui-hero-stat-label'>{label}</div>
            <div class='ui-hero-stat-value'>{value}</div>
        </div>
        """
        for label, value in stats
    )

    chips_html = "".join(
        f"<span class='ui-chip'>{chip}</span>" for chip in chips
    )

    title_prefix = f"{icon} " if icon else ""

    st.markdown(
        f"""
        <div class='ui-header'>
            <div class='ui-header-top'>
                <div>
                    <div class='ui-header-kicker'>{kicker}</div>
                    <h1>{title_prefix}{title}</h1>
                    <p>{subtitle}</p>
                    {f"<div class='ui-chip-row'>{chips_html}</div>" if chips_html else ''}
                </div>
                {f"<div style='display:flex; gap:12px; flex-wrap:wrap;'>{stats_html}</div>" if stats_html else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class='ui-section-title'>
            <div>
                <h3>{title}</h3>
                {f'<p>{subtitle}</p>' if subtitle else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value, caption: str = "", tone: str = "blue"):
    tone_map = _tone_styles(tone)
    accent = tone_map["accent"]
    soft = tone_map["soft"]

    st.markdown(
        f"""
        <div class='ui-mini-card' style='border-top: 4px solid {accent}; background: linear-gradient(180deg, rgba(255,255,255,0.94) 0%, {soft} 100%);'>
            <div class='label'>{label}</div>
            <div class='value'>{value}</div>
            {f"<div class='caption'>{caption}</div>" if caption else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge(text: str, tone: str = "blue") -> str:
    tone_map = _tone_styles(tone)
    accent = tone_map["accent"]
    bg = tone_map["bg"]
    text_color = tone_map["text"]

    return (
        f"<span class='ui-badge' style='background:{bg}; color:{text_color}; border:1px solid {accent}22;'>"
        f"{text}</span>"
    )


def empty_state(title: str, text: str):
    st.markdown(
        f"""
        <div class='ui-empty'>
            <div class='ui-empty-title'>{title}</div>
            <div>{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def panel_start(extra_style: str = ""):
    st.markdown(f"<div class='ui-panel' style='{extra_style}'>", unsafe_allow_html=True)


def panel_end():
    st.markdown("</div>", unsafe_allow_html=True)


def style_plotly(fig, height=None):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.0)",
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(family="Inter", color="#0F172A"),
        title_font=dict(size=18, color="#0F172A"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.0)",
        ),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(gridcolor="rgba(148,163,184,0.18)", zeroline=False),
    )
    if height:
        fig.update_layout(height=height)
    return fig
