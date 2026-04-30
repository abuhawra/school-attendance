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

# 2. هندسة التوسيط الكامل وتنسيق الواجهة
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="centered")

st.markdown("""
    <style>
    /* إخفاء القوائم غير الضرورية */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    
    /* خلفية هادئة مريحة للعين */
    .stApp {
        background-color: #f9fbff;
    }

    /* تنسيق النصوص وتوسيطها */
    .center-container {
        text-align: center !important;
        direction: rtl;
        width: 100%;
    }

    /* تكبير الخطوط بشكل متناسق */
    .main-title { font-size: 38px !important; font-weight: 800; color: #2c3e50; margin-bottom: 5px; }
    .school-name { font-size: 26px !important; color: #546e7a; margin-bottom: 25px; }
    .label-style { font-size: 24px !important; color: #78909c; font-weight: bold; margin-top: 25px; }
    .name-style { font-size: 34px !important; color: #1e88e5; font-weight: 900; margin-bottom: 10px; }

    /* --- توسيط الأزرار تماماً في منتصف الشاشة --- */
    div.stButton {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
    }

    .stButton button {
        width: 100% !important;
        max-width: 380px !important; /* عرض مثالي للجوال */
        height: 75px !important;
        border-radius: 20px !important;
        font-size: 24px !important;
        font-weight: bold !important;
        margin: 15px auto !important;
        display: block !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.1) !important;
        border: none !important;
        transition: transform 0.2s ease;
    }
    
    .stButton button:active {
        transform: scale(0.98);
    }

    /* ألوان هادئة واحترافية */
    button[kind="primary"] { background-color: #3498db !important; color: white !important; }
    button[kind="secondary"] { background-color: #90a4ae !important; color: white !important; }

    /* تحسين شكل الفواصل */
    hr { border: 0; height: 2px; background-image: linear-gradient(to right, transparent, #3498db, transparent); margin: 30px 0; }
    
    /* تنسيق الراديو بوتون ليكون واضحاً */
    div[data-testid="stMarkdownContainer"] p { font-size: 20px !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. إدارة التنقل بين الصفحات
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('<div class="center-container">', unsafe_allow_html=True)
    st.markdown('<div class="main-title">برنامج التحضير الرقمي</div>', unsafe_allow_html=True)
    st.markdown('<div class="school-name">مدرسة القطيف الثانوية</div>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    
    st.markdown('<div class="label-style">فكرة وتنفيذ</div>', unsafe_allow_html=True)
    st.markdown('<div class="name-style">أ. عارف أحمد الحداد</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="label-style">مدير المدرسة</div>', unsafe_allow_html=True)
    st.markdown('<div class="name-style">أ. فراس عبدالله آل عبدالمحسن</div>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)

    # الأزرار ستظهر الآن في المنتصف تماماً
    if st.button("📝 ابدأ تحضير الطلاب", type="primary"):
        st.session_state.page = "attendance"
        st.rerun()
    
    if st.button("⚙️ دخول لوحة التحكم", type="secondary"):
        st.session_state.page = "admin"
        st.rerun()

# --- صفحة التحضير ---
elif st.session_state.page == "attendance":
    if st.button("⬅️ عودة للرئيسية"):
        st.session_state.page = "home"; st.rerun()
        
    if not st.session_state.logged_in:
        st.markdown('<div class="center-container main-title" style="font-size:24px !important;">تسجيل الدخول</div>', unsafe_allow_html=True)
        nid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
        if st.button("تسجيل الدخول"):
            res = supabase.table("teachers").select("*").eq("national_id", nid.strip()).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                st.rerun()
            else:
                st.error("عذراً، السجل المدني غير موجود")
    else:
        st.info(f"المعلم المسؤول: {st.session_state.teacher_name}")
        t_date = st.date_input("تاريخ التحضير", datetime.now())
        
        # جلب قائمة اللجان
        s_data = supabase.table('students').select("committee").execute()
        coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else x)
        sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
        
        if sel_c != "---":
            students = supabase.table('students').select("*").eq('committee', sel_c).execute()
            results = []
            
            for s in students.data:
                st.markdown(f"👤 **{s['student_name']}**")
                stat = st.radio(f"الحالة لـ {s['student_name']}", ["حاضر", "غائب", "متأخر"], key=f"st_{s['id']}", horizontal=True, label_visibility="collapsed")
                results.append({
                    "student_name": s['student_name'], 
                    "committee": sel_c, 
                    "status": stat, 
                    "date": str(t_date), 
                    "teacher_name": st.session_state.teacher_name
                })
            
            st.divider()
            if st.button("💾 حفظ وإرسال الكشف", type="primary"):
                with st.spinner('جاري الحفظ...'):
                    supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(t_date)).execute()
                    supabase.table('attendance').insert(results).execute()
                    st.success("✅ تم حفظ الغياب بنجاح!")
                    time.sleep(1.5)
                    st.session_state.page = "home"
                    st.session_state.logged_in = False
                    st.rerun()

# --- صفحة الإدارة ---
elif st.session_state.page == "admin":
    if st.button("⬅️ عودة"):
        st.session_state.page = "home"; st.rerun()
    
    admin_pw = st.text_input("كلمة مرور الإدارة:", type="password")
    if admin_pw == "1234":
        st.success("مرحباً بك في لوحة التحكم")
        # يمكن إضافة تقارير أو أدوات إدارة البيانات هنا
