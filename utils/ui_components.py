import streamlit as st

def module_header(number, title, subtitle):
    """Creates a professional accented header for each module."""
    st.markdown(f"""
        <div style="border-left: 5px solid #007BFF; padding-left: 15px; margin-bottom: 25px;">
            <h1 style="color: #212529; margin-bottom: 0px; font-weight: 800;">{number} | {title}</h1>
            <p style="color: #6c757d; font-size: 1.1rem; margin-top: 5px; font-style: italic;">{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)

def main_content_text(text):
    """Renders standard body text with optimized line height and focus-friendly width."""
    st.markdown(f"""
        <div style="line-height: 1.6; color: #343a40; font-size: 1.05rem; margin-bottom: 15px;">
            {text}
        </div>
    """, unsafe_allow_html=True)

def sub_section_header(title, emoji=""):
    """Creates a consistent style for sub-headers within a module."""
    st.markdown(f"### {emoji} {title}")
    st.divider()

def highlight_box(content, type="info"):
    """A styled container for key takeaways or formulas."""
    colors = {
        "info": {"bg": "#f0f7ff", "border": "#007BFF"},
        "warning": {"bg": "#fff9e6", "border": "#ffcc00"},
        "success": {"bg": "#f2fff5", "border": "#28a745"}
    }
    c = colors.get(type, colors["info"])
    
    st.markdown(f"""
        <div style="background-color: {c['bg']}; padding: 15px; border-radius: 8px; 
                    border-left: 4px solid {c['border']}; margin: 15px 0;">
            {content}
        </div>
    """, unsafe_allow_html=True)

def learning_objectives(objectives_list):
    """Renders a styled list of goals for the module."""
    items = "".join([f"<li>{item}</li>" for item in objectives_list])
    st.markdown(f"""
        <div style="background-color: #f8f9fa; border-radius: 10px; padding: 20px; border: 1px solid #dee2e6;">
            <h4 style="margin-top:0;">🎯 What you will learn in this module:</h4>
            <ul style="margin-bottom:0;">{items}</ul>
        </div>
    """, unsafe_allow_html=True)