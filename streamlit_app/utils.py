"""Shared utilities for the Shows Attended app"""
import streamlit as st
from datetime import datetime


def format_date(date_str):
    """Format date string from YYYY-MM-DD to human-readable"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%b %d, %Y")


def inject_sidebar_css():
    """Rename 'app' to 'Shows' in sidebar navigation"""
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] ul li:first-child a span {
            visibility: hidden;
            position: relative;
            width: auto;
            min-width: 60px;
        }
        [data-testid="stSidebarNav"] ul li:first-child a span::before {
            content: "Shows";
            visibility: visible;
            position: absolute;
            left: 0;
            white-space: nowrap;
        }
        </style>
    """, unsafe_allow_html=True)
