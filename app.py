import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. إعدادات الواجهة والتنسيق الكلاسيكي (مع إصلاح Indentation وتوسيط الأقسام)
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; background-color: #f4f7f9; }
    .classic-card { background-color: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 20px; border: 1px solid #e0e0e0; }
    .classic-header { background-color: #1a237e; color: white; padding: 30px; border-radius: 15px; text-align: center; border-bottom: 5px solid #ffd700; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .wa-button { color: white !important; padding: 12px; border-radius: 10px; text-align: center; display: block; text-decoration: none; font-weight: bold; margin-top: 10px; font-size: 16px; transition: 0.3s; }
    .wa-all { background-color: #28a745; } .wa-all:hover { background-color: #218838; }
    .wa-absent { background-color: #dc3545; } .wa-absent:hover { background-color: #c82333; }
    th { background-color: #1a237e !important; color: white !important; text-align: center !important; font-size: 18px; }
    td { text-align: center !important; font-size: 16px; vertical-align: middle !important; }
    
    /* توسيط عناصر "إدارة البيانات" */
    .stTextInput > div > div > input { text-align: center; font-size: 18px; font-weight: bold; }
    div.stButton > button { border-radius: 12px; font-weight: bold; height: 55px; font-size: 18px !important; }
    [data-testid="stFileUploader"] { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown("""
        <div class="classic-header">
            <div style="font-size:36px; font-weight:800;">التحضير التقني</div>
            <div style="font-size:26px; font-weight:700;">مدرسة القطيف الثانوية</div>
            <div style="border-top: 2px solid white; width: 40%; margin: 15px auto;"></div>
            <div style="font-size:18px; color:#cfd8dc;">فكرة وبرمجة: أ. عارف أحمد الحداد</div>
            <div style="font-size:18px; color:#cfd8dc;">إشراف مدير المدرسة: أ. فراس عبدالله آل عبد المحسن</div>
        </div>
    """, unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 1.5, 1])
    with col_b:
        if st.button("📝 رصد غياب الطلاب اليومي", type="primary", use_container_width=True): st.session_state.page = "t_log"; st.rerun()
        st.write(" ")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة", use_container_width=True): st.session_state.page = "a_log"; st.rerun()

# --- قسم رصد المعلم ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']; st.session_state.page = "mark"; st.rerun()
        else: st.error("السجل غير موجود.")

elif st.session_state.page == "mark":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher} | التاريخ: {today}")
    res_s = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in res_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
    sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
    if sel_c != "---":
        students = supabase.table('students').select("*").eq("committee", sel_c).execute()
        results = []
        for s in students.data:
            choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], key=s['id'], horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": st.session_state.teacher})
        if st.button("💾 حفظ الرصد نهائياً"):
            supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
            supabase.table('attendance').insert(results).execute()
            st.success("تم الحفظ!"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- قسم الإدارة ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز الإدارة:", type="password") == "1234": st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2 = st.tabs(["📊 التقارير الموحدة", "💾 إدارة البيانات الطلاب"])
    with tab1:
        d = st.date_input("اختر التاريخ:", datetime.now())
        att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if att.data:
            df = pd.DataFrame(att.data)
            df_abs = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            if not df_abs.empty:
                std = supabase.table("students").select("student_name", "class_name").execute()
                s_map = {i['student_name']: i['class_name'] for i in std.data}
                df_abs['الشعبة'] = df_abs['student_name'].map(s_map).fillna("---")
                st.table(df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee':'اللجنة','student_name':'الطالب'}))
                msg = f"🗓️ *تقرير مدرسة القطيف التقني*%0A📅 *التاريخ:* {d}%0A-----------------------%0A"
                for _, r in df_abs.iterrows(): msg += f"📦 لجنة {r['committee']} | 👤 {r['student_name']} ({r['status']})%0A"
                col1, col2 = st.columns(2)
                with col1: st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="wa-button wa-all">📲 إرسال (الكل)</a>', unsafe_allow_html=True)
                with col2:
                    df_g = df_abs[df_abs['status']=='غائب']; msg_g = msg.replace("(الكل)", "(غائب فقط)")
                    if not df_g.empty: st.markdown(f'<a href="https://wa.me/?text={msg_g}" target="_blank" class="wa-button wa-absent">🚫 إرسال (غائب فقط)</a>', unsafe_allow_html=True)
        else: st.info("لا بيانات.")

    with tab2:
        # تنسيق مُوسط لقسم إدارة البيانات
        col_m1, col_m2, col_m3 = st.columns([1, 1.5, 1])
        with col_m2:
            if st.text_input("كلمة سر البيانات الموحدة:", type="password") == "4321":
                st.write(" ")
                up = st.file_uploader("ارفع ملف الطلاب الجديد (CSV/Excel):")
                if up and st.button("🚀 بدء التحديث", use_container_width=True):
                    supabase.table('students').delete().neq('student_name', 'none').execute()
                    df_up = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                    recs = df_up.to_dict('records')
                    for r in recs: r.pop('id', None) # إزالة id القديم ليتولى Supabase إنشاؤه
                    supabase.table('students').insert(recs).execute(); st.success("تم التحديث!")
