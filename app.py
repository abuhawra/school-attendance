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

# 2. هندسة الواجهة والتوسيط
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    
    /* خلفية هادئة */
    .stApp { background-color: #f9fbff; }

    /* حاوية التوسيط للنصوص */
    .center-text {
        text-align: center !important;
        direction: rtl;
        width: 100%;
    }

    .main-title { font-size: 35px !important; font-weight: 800; color: #2c3e50; }
    .school-name { font-size: 24px !important; color: #546e7a; }
    .label-style { font-size: 22px !important; color: #78909c; font-weight: bold; }
    .name-style { font-size: 32px !important; color: #1e88e5; font-weight: 900; }

    /* --- تنسيق الأزرار وتوسيطها --- */
    .stButton {
        display: flex;
        justify-content: center;
    }

    .stButton button {
        width: 100% !important;
        max-width: 350px !important;
        height: 65px !important;
        border-radius: 15px !important;
        font-size: 22px !important;
        font-weight: bold !important;
        margin-top: 10px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
    }

    /* ألوان الأزرار */
    button[kind="primary"] { background-color: #3498db !important; color: white !important; }
    button[kind="secondary"] { background-color: #cfd8dc !important; color: #455a64 !important; }

    /* تحسين شكل الفواصل */
    hr { border: 0; height: 1px; background: #ddd; margin: 25px 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. إدارة التنقل
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

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
        st.session_state.page = "attendance"
        st.rerun()
    
    if st.button("⚙️ دخول لوحة التحكم", type="secondary"):
        st.session_state.page = "admin"
        st.rerun()

# --- صفحة التحضير ---
elif st.session_state.page == "attendance":
    if st.button("⬅️ عودة للرئيسية", type="secondary"):
        st.session_state.page = "home"
        st.rerun()
        
    if not st.session_state.logged_in:
        st.markdown('<div class="center-text label-style">تسجيل دخول المعلم</div>', unsafe_allow_html=True)
        nid = st.text_input("السجل المدني:", type="password")
        if st.button("دخول"):
            res = supabase.table("teachers").select("*").eq("national_id", nid.strip()).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                st.rerun()
            else:
                st.error("السجل غير صحيح")
    else:
        st.success(f"المعلم: {st.session_state.teacher_name}")
        t_date = st.date_input("التاريخ", datetime.now())
        s_data = supabase.table('students').select("committee").execute()
        coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else x)
        sel_c = st.selectbox("اللجنة:", ["---"] + coms)
        
        if sel_c != "---":
            students = supabase.table('students').select("*").eq('committee', sel_c).execute()
            results = []
            for s in students.data:
                st.write(f"👤 **{s['student_name']}**")
                stat = st.radio(f"الحالة", ["حاضر", "غائب", "متأخر"], key=f"s_{s['id']}", horizontal=True)
                results.append({"student_name": s['student_name'], "committee": sel_c, "status": stat, "date": str(t_date), "teacher_name": st.session_state.teacher_name})
            
            if st.button("💾 حفظ الكشف", type="primary"):
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(t_date)).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("تم الحفظ")
                time.sleep(1)
                st.session_state.page = "home"
                st.session_state.logged_in = False
                st.rerun()

# --- صفحة الإدارة ---
elif st.session_state.page == "admin":
    # زر العودة في أعلى الصفحة ومنفصل لضمان الاستجابة
    if st.button("⬅️ عودة للقائمة الرئيسية", type="secondary"):
        st.session_state.page = "home"
        st.rerun()
    
    st.divider()
    admin_pw = st.text_input("كلمة مرور الإدارة:", type="password")
    if admin_pw == "1234":
        st.success("مرحباً بك في لوحة التحكم")
        # هنا تضع تقاريرك لاحقاً
