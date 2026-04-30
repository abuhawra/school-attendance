import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io
import urllib.parse

# 1. إعدادات الاتصال
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. التنسيق (توسيط كامل)
st.set_page_config(page_title="التحضير التقني - مدرسة القطيف", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .center-div { width: 100%; text-align: center; direction: rtl; }
    .main-title { font-size: 32px; font-weight: 800; color: #1a237e; }
    .stButton button { width: 100% !important; max-width: 350px !important; border-radius: 15px !important; font-weight: bold !important; height: 55px; }
    div.stButton > button[kind="primary"] { background-color: #007bff !important; color: white !important; }
    div.stButton > button[kind="secondary"] { background-color: #ff9800 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- دالة العودة للرئيسية ---
def go_home():
    st.session_state.page = "home"
    st.rerun()

# --- الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('<div class="center-div"><p class="main-title">التحضير التقني لمدرسة القطيف الثانوية</p><p>تصميم وتنفيذ أستاذ عارف أحمد الحداد</p><p>مدير المدرسة أ. فراس عبدالله آل عبدالمحسن</p></div>', unsafe_allow_html=True)
    if st.button("📝 الدخول للتحضير", type="primary"): st.session_state.page = "att_login"; st.rerun()
    if st.button("⚙️ دخول الإدارة", type="secondary"): st.session_state.page = "admin_login"; st.rerun()

# --- صفحة التحضير ---
elif st.session_state.page == "att_login":
    t_id = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل المدني غير مسجل")

elif st.session_state.page == "taking_attendance":
    st.info(f"المعلم: {st.session_state.teacher_name}")
    today = str(datetime.now().date())
    
    # جلب اللجان
    s_data = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in s_data.data])))
    sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
    
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        results = []
        for s in students.data:
            st.write(f"👤 **{s['student_name']}**")
            stat = st.radio(f"الحالة", ["حاضر", "غائب", "متأخر"], index=0, key=f"s_{s['id']}", horizontal=True)
            results.append({
                "student_name": s['student_name'],
                "committee": str(sel_c),
                "status": stat,
                "date": today,
                "teacher_name": st.session_state.teacher_name,
                "class_name": s.get('class_name', 'عام')
            })
        
        if st.button("💾 حفظ وإرسال الكشف", type="primary"):
            try:
                # حذف التحضير القديم لنفس اللجنة واليوم لتجنب التكرار
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
                # إدخال البيانات الجديدة
                response = supabase.table('attendance').insert(results).execute()
                st.success("تم الحفظ بنجاح!")
                time.sleep(1)
                go_home()
            except Exception as e:
                st.error(f"حدث خطأ أثناء الحفظ: {e}")
                st.info("تأكد أن جدول attendance يحتوي على الأعمدة: student_name, committee, status, date, teacher_name, class_name")

# --- الإدارة ---
elif st.session_state.page == "admin_login":
    pw = st.text_input("رمز دخول الإدارة:", type="password")
    if pw == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ خروج"): go_home()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير", "🏘️ اللجان", "🛠️ الأسماء"])
    
    with tab1:
        d = st.date_input("التاريخ", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df_view = df[df['status'].isin(['غائب', 'متأخر'])]
            st.table(df_view[['student_name', 'status', 'committee']])
            
            for _, row in df_view.iterrows():
                msg = f"*تقرير غياب*\n👤 *الاسم:* {row['student_name']}\n📦 *اللجنة:* {row['committee']}\n⚠️ *الحالة:* {row['status']}"
                link = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                st.markdown(f"[إرسال واتساب لـ {row['student_name']} 📲]({link})")

    with tab3:
        adm_pw = st.text_input("رمز الإدارة العليا:", type="password")
        if adm_pw == "12345":
            st.success("مرحباً بك في إدارة البيانات")
            if st.button("🗑️ حذف جميع الطلاب"):
                supabase.table("students").delete().neq("id", 0).execute()
                st.warning("تم الحذف")
