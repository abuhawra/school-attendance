import streamlit as st
from supabase import create_client

# --- 1. إعدادات الربط ---
URL = "https://iptsrwpxylqlnpekscuh.supabase.co"
KEY = "sb_publishable_VK9dQHxf8bT43L3Wr6oGWA_QNdoNh9L"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="نظام الغياب", layout="centered")

# --- 2. تسجيل الدخول ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.header("🔐 دخول النظام")
    user_input = st.text_input("أدخل السجل المدني").strip()
    
    if st.button("دخول"):
        # البحث في الجدول الجديد teachers_new
        res = supabase.table("teachers_new").select("*").eq("t_id", user_input).execute()
        
        if res.data:
            st.session_state.auth = True
            st.session_state.name = res.data[0]['t_name']
            st.rerun()
        else:
            st.error(f"السجل {user_input} غير مضاف في teachers_new")
else:
    st.success(f"مرحباً أ/ {st.session_state.name}")
    if st.button("تسجيل خروج"):
        st.session_state.auth = False
        st.rerun()
