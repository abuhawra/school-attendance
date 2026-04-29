import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# بيانات الاتصال
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

def smart_sort(x):
    try: return int(x)
    except: return str(x)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

st.set_page_config(page_title="نظام غياب الطلاب - أ. عارف الحداد", layout="wide")

# دالة جلب حالة النظام (مفتوح/مغلق)
def get_system_status():
    try:
        res = supabase.table("settings").select("is_open").eq("setting_name", "attendance_status").execute()
        if not res.data:
            supabase.table("settings").insert({"setting_name": "attendance_status", "is_open": True}).execute()
            return True
        return res.data[0]['is_open']
    except: return True

st.sidebar.title("🏫 القائمة الرئيسية")
page = st.sidebar.radio("انتقل إلى:", ["🔑 دخول المعلم", "📊 لوحة الإدارة"])

# --- 1. واجهة المعلم ---
if page == "🔑 دخول المعلم":
    is_open = get_system_status()
    if not is_open:
        st.error("🚫 نظام رصد الغياب مغلق حالياً من قبل الإدارة. يرجى مراجعة المسؤول.") # هذا سبب الاختفاء
    else:
        if not st.session_state.get('logged_in', False):
            st.header("🔑 تسجيل دخول المعلم")
            nid_input = st.text_input("أدخل رقم السجل المدني:")
            if st.button("دخول"):
                res = supabase.table("teachers").select("*").eq("national_id", nid_input.strip()).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                    st.rerun()
                else: st.error("❌ السجل غير صحيح.")
        else:
            st.success(f"✅ مرحباً أستاذ: {st.session_state.teacher_name}")
            # (هنا يظهر كود الرصد عند فتح النظام)
            st.info("النظام مفتوح وجاهز للرصد.")

# --- 2. لوحة الإدارة ---
elif page == "📊 لوحة الإدارة":
    st.header("📊 لوحة الإدارة والتقارير")
    if st.sidebar.text_input("كلمة المرور", type="password") == "1234":
        current_status = get_system_status()
        
        # التحكم في فتح وإغلاق النظام
        if current_status:
            st.success("🟢 النظام الآن: مفتوح لاستقبال الرصد")
            if st.button("🔴 إغلاق رصد الغياب الآن"):
                supabase.table("settings").update({"is_open": False}).eq("setting_name", "attendance_status").execute()
                st.rerun()
        else:
            st.error("🔴 النظام الآن: مغلق")
            if st.button("🟢 تفعيل رصد الغياب الآن"):
                supabase.table("settings").update({"is_open": True}).eq("setting_name", "attendance_status").execute()
                st.rerun()
        
        st.divider()
        # (بقية كود التقارير والواتساب هنا...)
