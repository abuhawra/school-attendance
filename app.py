import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. هندسة الواجهة والتنسيق
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    
    .stApp { background-color: #f9fbff; }

    .center-text {
        text-align: center !important;
        direction: rtl;
        width: 100%;
    }

    .main-title { font-size: 35px !important; font-weight: 800; color: #2c3e50; }
    .school-name { font-size: 24px !important; color: #546e7a; }
    .label-style { font-size: 22px !important; color: #78909c; font-weight: bold; }
    .name-style { font-size: 32px !important; color: #1e88e5; font-weight: 900; }

    .stButton { display: flex; justify-content: center; }

    .stButton button {
        width: 100% !important;
        max-width: 350px !important;
        height: 65px !important;
        border-radius: 15px !important;
        font-size: 22px !important;
        font-weight: bold !important;
        margin-top: 10px !important;
    }

    button[kind="primary"] { background-color: #3498db !important; color: white !important; }
    button[kind="secondary"] { background-color: #cfd8dc !important; color: #455a64 !important; }

    hr { border: 0; height: 1px; background: #ddd; margin: 25px 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. إدارة التنقل
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'admin_logged_in' not in st.session_state: st.session_state.admin_logged_in = False

# --- الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('<div class="center-text">', unsafe_allow_html=True)
    st.markdown('<div class="main-title">برنامج التحضير الرقمي</div>', unsafe_allow_html=True)
    st.markdown('<div class="school-name">مدرسة القطيف الثانوية</div>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('<div class="label-style">فكرة وتنفيذ</div>', unsafe_allow_html=True)
    st.markdown('<div class="name-style">أ. عارف أحمد الحداد</div>', unsafe_allow_html=True)
    st.markdown('<div class="label-style">مدير المدرسة</div>', unsafe_allow_html=True)
    st.markdown('<div class="name-style">أ. فراس عبدالله آل عبدالمحسن</div>', unsafe_allow_html=True)
    st.markdown('<hr></div>', unsafe_allow_html=True)

    if st.button("📝 ابدأ تحضير الطلاب", type="primary"):
        st.session_state.page = "attendance"; st.rerun()
    
    if st.button("⚙️ دخول لوحة التحكم", type="secondary"):
        st.session_state.page = "admin_login"; st.rerun()

# --- صفحة التحضير ---
elif st.session_state.page == "attendance":
    if st.button("⬅️ عودة للقائمة الرئيسية"):
        st.session_state.page = "home"; st.session_state.logged_in = False; st.rerun()
    # (كود التحضير يبقى كما هو)
    st.write("صفحة التحضير جاهزة...")

# --- صفحة تسجيل دخول الإدارة ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"):
        st.session_state.page = "home"; st.rerun()
    
    st.markdown('<div class="center-text label-style">كلمة مرور الإدارة</div>', unsafe_allow_html=True)
    pw = st.text_input("أدخل الرمز:", type="password")
    
    if pw == "1234":
        st.session_state.admin_logged_in = True
        st.session_state.page = "admin_panel"
        st.rerun()
    elif pw != "":
        st.error("الرمز غير صحيح")

# --- لوحة التحكم الفعلية (بعد تسجيل الدخول) ---
elif st.session_state.page == "admin_panel":
    if st.button("⬅️ خروج من الإدارة"):
        st.session_state.admin_logged_in = False
        st.session_state.page = "home"
        st.rerun()
    
    st.markdown('<div class="center-text main-title">لوحة التحكم</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 التقارير", "🗂️ قاعدة البيانات", "🛠️ الإعدادات"])
    
    with tab1:
        st.write("عرض تقارير الغياب...")
        rep_date = st.date_input("اختر التاريخ", datetime.now())
        # هنا تضع كود جلب بيانات الغياب من السوبابيس كما في النسخ السابقة

    with tab2:
        st.write("إدارة الطلاب والمعلمين")
        # هنا تضع كود الرفع (Upload) والتحميل (Download)

    with tab3:
        st.write("إعدادات النظام")
