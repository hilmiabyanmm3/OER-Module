import streamlit as st

# --- 1. UI COMPONENT DEFINITIONS ---

def inject_global_css():
    """Injects modern typography, button styles, and Font Awesome icons."""
    st.markdown("""
        <style>
            /* Import Inter Font & Font Awesome */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
            @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
            }

            .stApp {
                background-color: #fcfcfc;
            }

            /* Modernizing all Streamlit buttons */
            .stButton > button {
                border-radius: 8px;
                border: 1px solid #007BFF;
                font-weight: 600;
                padding: 0.5rem 1rem;
                transition: all 0.3s ease;
            }
            .stButton > button:hover {
                background-color: #007BFF;
                color: white;
                box-shadow: 0 4px 12px rgba(0, 123, 255, 0.2);
                border: 1px solid #007BFF;
            }
        </style>
    """, unsafe_allow_html=True)

def module_header(number, title, subtitle):
    """Refined header with a gradient badge and modern hierarchy."""
    st.markdown(f"""
        <div style="margin-bottom: 35px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="background: linear-gradient(135deg, #007BFF, #0056b3); 
                             color: white; padding: 6px 16px; border-radius: 8px; 
                             font-weight: 800; font-size: 0.85rem; letter-spacing: 0.5px;">{number}</span>
                <h1 style="color: #1a1c1e; margin: 0; font-weight: 800; font-size: 2.2rem; letter-spacing: -0.5px;">{title}</h1>
            </div>
            <p style="color: #6c757d; font-size: 1.1rem; margin-top: 10px; font-weight: 400; font-style: normal;">{subtitle}</p>
            <hr style="margin-top: 20px; border: 0; border-top: 2px solid #f0f2f6;">
        </div>
    """, unsafe_allow_html=True)

def main_content_text(text):
    """Renders body text with optimized line-height for long-form research reading."""
    st.markdown(f"""
        <div style="line-height: 1.8; color: #3e444b; font-size: 1.05rem; margin-bottom: 20px;">
            {text}
        </div>
    """, unsafe_allow_html=True)

def sub_section_header(title, icon_class="fa-solid fa-circle-chevron-right"):
    """Creates a consistent, software-grade sub-header with precise alignment."""
    st.markdown(f"""
        <div style="margin-top: 30px; margin-bottom: 15px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <i class="{icon_class}" style="color: #007BFF; font-size: 1.1rem; display: flex; align-items: center;"></i>
                <span style="font-weight: 700; color: #1a1c1e; font-size: 1.3rem; letter-spacing: -0.02em;">
                    {title}
                </span>
            </div>
            <hr style="margin-top: 12px; margin-bottom: 0; border: 0; border-top: 1px solid #f0f2f6;">
        </div>
    """, unsafe_allow_html=True)

def highlight_box(content, type="info"):
    """Modern 'Card' style box with Font Awesome icons and soft depth shadows."""
    # Mapping icons to Font Awesome classes
    configs = {
        "info": {"border": "#007BFF", "icon": "fa-solid fa-circle-info"},
        "warning": {"border": "#FFC107", "icon": "fa-solid fa-triangle-exclamation"},
        "success": {"border": "#28A745", "icon": "fa-solid fa-circle-check"}
    }
    c = configs.get(type, configs["info"])
    
    st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 12px; 
                    border-left: 6px solid {c['border']}; margin: 25px 0;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.05); display: flex; gap: 15px; align-items: flex-start;">
            <div style="color: {c['border']}; font-size: 1.2rem;">
                <i class="{c['icon']}"></i>
            </div>
            <div style="color: #3e444b; font-size: 1rem; line-height: 1.6;">{content}</div>
        </div>
    """, unsafe_allow_html=True)

def style_sidebar():
    """Sleek sidebar styling with compact navigation."""
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                background-color: #ffffff;
                border-right: 1px solid #f0f2f6;
            }
            [data-testid="stSidebarNav"] {
                padding-top: 1rem !important;
            }
            [data-testid="stSidebarNavItems"] li {
                margin: 2px 12px !important;
                border-radius: 6px;
                transition: all 0.3s ease;
            }
            [data-testid="stSidebarNavItems"] li a {
                padding: 6px 15px !important;
                color: #4a4a4a !important;
                text-decoration: none !important;
                font-weight: 500;
            }
            [data-testid="stSidebarNavItems"] li:hover {
                background-color: #f0f7ff;
            }
            [data-testid="stSidebarNavItems"] li [aria-current="page"] {
                background-color: #eef6ff !important;
                color: #007BFF !important;
                font-weight: 700 !important;
                border-left: 4px solid #007BFF;
                border-radius: 4px 6px 6px 4px;
            }
            .stProgress > div > div > div > div {
                background-image: linear-gradient(to right, #007BFF, #00c6ff);
                border-radius: 10px;
                height: 6px;
            }
            section[data-testid="stSidebar"] .stAlert {
                border: none;
                box-shadow: 0 2px 10px rgba(0,0,0,0.04);
                border-radius: 10px;
                padding: 0.75rem;
            }
        </style>
    """, unsafe_allow_html=True)

def render_sidebar_progress(progress_value):
    """Renders progress with Font Awesome lightbulb icon."""
    with st.sidebar:
        st.markdown("<h2 style='font-size: 1.1rem; margin-top: 0;'>Portal Journey</h2>", unsafe_allow_html=True)
        st.progress(progress_value)
        st.caption(f"Course Completion: **{progress_value}%**")
        st.divider()
        st.markdown(f"""
            <div style="background-color: white; padding: 12px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); display: flex; gap: 10px;">
                <i class="fa-solid fa-lightbulb" style="color: #FFC107; margin-top: 3px;"></i>
                <div style="font-size: 0.85rem; color: #3e444b;">
                    Complete modules in order to ensure DFT convergence.
                </div>
            </div>
        """, unsafe_allow_html=True)

def learning_objectives(objectives_list):
    """
    Renders a styled card for learning objectives with bullseye and checkmark icons.
    """
    # Rapatkan HTML untuk list item
    items_html = "".join([
        f'<div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 10px;">'
        f'<i class="fa-solid fa-check" style="color: #28a745; margin-top: 4px; font-size: 0.9rem;"></i>'
        f'<span style="color: #495057; font-size: 1rem; line-height: 1.5;">{obj}</span>'
        f'</div>' for obj in objectives_list
    ])

    # Rapatkan HTML utama ke margin kiri agar terhindar dari Markdown parser error
    html_string = f"""
<div style="background-color: #f8fbff; padding: 24px; border-radius: 12px; border: 1px solid #e1e8f0; border-left: 6px solid #007BFF; margin: 20px 0 30px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 18px;">
        <i class="fa-solid fa-bullseye" style="color: #007BFF; font-size: 1.4rem;"></i>
        <h3 style="margin: 0; color: #1a1c1e; font-size: 1.2rem; font-weight: 700; letter-spacing: -0.02em;">
            Learning Objectives
        </h3>
    </div>
    <div style="padding-left: 4px;">
        {items_html}
    </div>
</div>
"""
    st.markdown(html_string, unsafe_allow_html=True)