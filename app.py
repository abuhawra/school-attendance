import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse
import io

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. هندسة التنسيق (توسيط كامل وتكبير الخطوط)
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="centered")

st.markdown("""
    <style>
    /* إخفاء القوائم والترويسات */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* تنسيق الخلفية والجسم العام */
    .stApp {
        background-color: #f4f7f9;
    }

    /* حاوية النصوص لضمان التوسيط الكامل */
    .center-text {
        text-align: center !important;
        width: 100%;
        display: block;
        direction: rtl;
    }

    /* تكبير العناوين الرئيسية */
    .main-title {
        font-size: 38px !important;
        font-weight: 800;
        color: #2c3e50;
        margin-bottom: 5px;
    }
    
    .school-name {
        font-size: 26px !important;
        color: #34495e;
        margin-bottom: 30px;
    }

    /* تكبير خط "فكرة وتنفيذ" و "مدير المدرسة" */
    .label-style {
        font-size: 24px !important;
        color: #7f8c8d !important;
        font-weight: bold;
        margin-top: 25px;
    }

    /* تكبير خط الأسماء */
    .name-style {
        font-size: 32px !important;
        color: #1f77b4 !important;
        font-weight: 900;
        margin-bottom: 20px;
    }

    /* توسيط الأزرار وتكبير الأيقونات */
    div.stButton {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
    }

    div.stButton > button {
        width: 100% !important;
        max-width: 400px !important;
        height: 75px !important;
        border-radius: 20px !important;
        font-size: 24px !important; /* حجم خط الزر */
        font-weight: bold !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin: 15px auto !important;
    }

    /* ألوان الأزرار */
    button[kind="primary"] { background-color: #4A90E2 !important; color: white !important; }
    button[kind="secondary"] { background-color: #95a5a6 !important; color: white !important; }

    /* تحسين شكل الفواصل */
    hr {
        border: 0;
        height: 2px;
        background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(31,119,180,0.75), rgba(0,0,0,0));
        margin: 30px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. إدارة الصفحات
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- الصفحة الرئيسية (التصميم المطور) ---
if st.session_state.page == "home":
    # استخدام حاوية CSS مخصصة لضمان التوسيط
    st.markdown('<div class="center-text main-title">برنامج التحضير الرقمي</div>', unsafe_allow_html=True)
    st.markdown('<div class="center-text school-name">مدرسة القطيف الثانوية</div>', unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # قسم الأسماء
    st.markdown('<div class="center-text label-style">فكرة وتنفيذ</div>', unsafe_allow_html=True)
    st.markdown('<div class="center-text name-style">أ. عارف أحمد الحداد</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="center-text label-style">مدير المدرسة</div>', unsafe_allow_html=True)
    st.markdown('<div class="center-text name-style">أ. فراس عبدالله آل عبدالمحسن</div>', unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)
    
    # الأزرار موسطة بالكامل
    if st.button("📝 ابدأ تحضير الطلاب", type="primary"):
        st.session_state.page = "attendance"; st.rerun()
    
    if st.button("⚙️ دخول لوحة التحكم", type="secondary"):
        st.session_state.page = "admin"; st.rerun()

# --- صفحة التحضير ---
elif st.session_state.page == "attendance":
    if st.button("⬅️ عودة"):
        st.session_state.page = "home"; st.rerun()
        
    if not st.session_state.logged_in:
        st.markdown('<div class="center-text school-name">تسجيل دخول المعلم</div>', unsafe_allow_html=True)
        nid = st.text_input("أدخل السجل المدني:", type="password")
        if st.button("دخول"):
            res = supabase.table("teachers").select("*").eq("national_id", nid.strip()).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                st.rerun()
            else:
                st.error("السجل المدني غير مسجل")
    else:
        st.markdown(f'<div class="center-text label-style">المعلم: {st.session_state.teacher_name}</div>', unsafe_allow_html=True)
        t_date = st.date_input("تاريخ اليوم", datetime.now())
        
        s_data = supabase.table('students').select("committee").execute()
        coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else x)
        sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
        
        if sel_c != "---":
            students = supabase.table('students').select("*").eq('committee', sel_c).execute()
            results = []
            
            for s in students.data:
                st.markdown(f'<div class="center-text label-style">👤 {s["student_name"]}</div>', unsafe_allow_html=True)
                stat = st.radio("الحالة", ["حاضر", "غائب", "متأخر"], key=f"st_{s['id']}", horizontal=True)
                results.append({"student_name": s['student_name'], "committee": sel_c, "status": stat, "date": str(t_date), "teacher_name": st.session_state.teacher_name})
            
            if st.button("💾 حفظ البيانات"):
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(t_date)).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("تم الحفظ بنجاح!")
                time.sleep(2)
                st.session_state.page = "home"; st.session_state.logged_in = False; st.rerun()

# --- صفحة الإدارة ---
elif st.session_state.page == "admin":
    if st.button("⬅️ عودة"):
        st.session_state.page = "home"; st.rerun()
    pw = st.text_input("كلمة المرور:", type="password")
    if pw == "1234":
        st.write("لوحة التحكم")
