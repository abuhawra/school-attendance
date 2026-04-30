import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse
import os
import io

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. تنسيق الواجهة والستايل (توسيط كامل للنصوص والأزرار)
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="wide")

st.markdown("""
    <style>
    /* إخفاء القوائم الافتراضية */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    
    /* تنسيق الحاوية الرئيسية لتوسيط كل شيء */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    /* تنسيق النصوص */
    .main-title {
        color: #1f77b4;
        font-size: 35px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .school-name {
        color: #333;
        font-size: 24px;
        margin-bottom: 20px;
    }
    .label-text {
        color: #666;
        font-size: 16px;
        margin-top: 15px;
        margin-bottom: 2px;
    }
    .name-text {
        color: #1f77b4;
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    /* تنسيق الأزرار */
    div.stButton > button {
        width: 100%;
        max-width: 400px;
        height: 55px;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        margin: 10px auto;
        display: block;
    }
    
    button[kind="primary"] {
        background-color: #ADD8E6 !important;
        color: #000 !important;
        border: 2px solid #ADD8E6 !important;
    }
    button[kind="secondary"] {
        background-color: #FFA500 !important;
        color: #fff !important;
        border: 2px solid #FFA500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. إدارة التنقل
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- الصفحة الرئيسية (توسيط احترافي للجوال) ---
if st.session_state.page == "home":
    # عرض النصوص باستخدام HTML بسيط ومضمون
    st.markdown(f'<p class="main-title">برنامج التحضير الرقمي</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="school-name">مدرسة القطيف الثانوية</p>', unsafe_allow_html=True)
    
    st.markdown('<hr style="width: 60%; border: 1px solid #1f77b4;">', unsafe_allow_html=True)
    
    st.markdown('<p class="label-text">فكرة وتنفيذ</p>', unsafe_allow_html=True)
    st.markdown('<p class="name-text">أ. عارف أحمد الحداد</p>', unsafe_allow_html=True)
    
    st.markdown('<p class="label-text">مدير المدرسة</p>', unsafe_allow_html=True)
    st.markdown('<p class="name-text">أ. فراس عبدالله آل عبدالمحسن</p>', unsafe_allow_html=True)
    
    st.markdown('<hr style="width: 60%; border: 1px solid #1f77b4;">', unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)
    
    # الأزرار (ستظهر موسطة وتلقائية العرض)
    if st.button("📝 تحضير الطلاب اليومي", type="primary"):
        st.session_state.page = "attendance"; st.rerun()
    
    if st.button("⚙️ لوحة تحكم الإدارة", type="secondary"):
        st.session_state.page = "admin"; st.rerun()

# --- صفحة التحضير ---
elif st.session_state.page == "attendance":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if not st.session_state.logged_in:
        nid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
        if st.button("تسجيل الدخول"):
            res = supabase.table("teachers").select("*").eq("national_id", nid.strip()).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                st.rerun()
            else: st.error("عذراً، السجل غير مسجل.")
    else:
        st.info(f"المعلم المسؤول: {st.session_state.teacher_name}")
        t_date = st.date_input("تاريخ اليوم", datetime.now())
        s_data = supabase.table('students').select("committee").execute()
        coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else x)
        sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
        
        if sel_c != "---":
            students = supabase.table('students').select("*").eq('committee', sel_c).execute()
            results = []
            for s in students.data:
                st.write(f"👤 {s['student_name']}")
                stat = st.radio("الحالة", ["حاضر", "غائب", "متأخر"], key=f"st_{s['id']}", horizontal=True)
                results.append({"student_name": s['student_name'], "committee": sel_c, "status": stat, "date": str(t_date), "teacher_name": st.session_state.teacher_name})
            
            if st.button("💾 اعتماد وحفظ الكشف"):
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(t_date)).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("✅ تم الحفظ!"); time.sleep(1)
                st.session_state.page = "home"; st.session_state.logged_in = False; st.rerun()

# --- صفحة الإدارة ---
elif st.session_state.page == "admin":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    pw = st.text_input("كلمة مرور الإدارة:", type="password")
    if pw == "1234":
        tab1, tab2, tab3 = st.tabs(["📊 التقارير", "🗂️ الطلاب", "🧹 الإعدادات"])
        
        with tab1:
            rep_date = st.date_input("اختر التاريخ", datetime.now())
            att = supabase.table('attendance').select("*").eq('date', str(rep_date)).execute()
            if att.data:
                df = pd.DataFrame(att.data)
                st.table(df[['student_name', 'status']])
                msg = f"*تقرير غياب {rep_date}*\n"
                encoded_msg = urllib.parse.quote(msg)
                st.markdown(f'<a href="https://wa.me/?text={encoded_msg}" target="_blank">📱 إرسال واتساب</a>', unsafe_allow_html=True)

        with tab2:
            col_bk1, col_bk2 = st.columns(2)
            with col_bk1:
                if st.button("📥 نسخة احتياطية"):
                    res = supabase.table('students').select("*").execute()
                    df = pd.DataFrame(res.data)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    st.download_button("تحميل الملف", output.getvalue(), "backup.xlsx")
            with col_bk2:
                restore = st.file_uploader("📂 استرجاع", type=['xlsx'])
                if restore and st.button("تأكيد الاسترجاع"):
                    df = pd.read_excel(restore)
                    supabase.table('students').delete().neq('id', 0).execute() 
                    supabase.table('students').insert(df.to_dict(orient='records')).execute()
                    st.success("تم!")

        with tab3:
            if st.button("❌ حذف غياب اليوم"):
                supabase.table('attendance').delete().eq('date', str(datetime.now().date())).execute()
                st.success("تم الحذف.")
