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

# 2. إعدادات الواجهة والتنسيق
st.set_page_config(page_title="نظام مدرسة القطيف", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; direction: rtl; }
    .main-title { font-size: 30px; font-weight: 800; color: #1a237e; text-align: center; }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 18px; border-radius: 12px; text-align: center; text-decoration: none; display: block; font-weight: bold; margin: 20px auto; max-width: 500px; font-size: 20px; border: 1px solid #128C7E; }
    div.stButton > button { width: 100%; max-width: 400px; height: 50px; border-radius: 12px; font-weight: bold; margin: 10px auto; display: block; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('<p class="main-title">التحضير التقني لمدرسة القطيف الثانوية</p>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;">بإشراف أ. عارف الحداد | مدير المدرسة أ. فراس آل عبدالمحسن</p><hr>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📝 دخول المعلمين للرصد", type="primary"): st.session_state.page = "att_login"; st.rerun()
        if st.button("⚙️ لوحة الإدارة والتقارير", type="secondary"): st.session_state.page = "admin_login"; st.rerun()

# --- رصد الحضور ---
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    t_id = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل غير مسجل")

elif st.session_state.page == "taking_attendance":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher_name} | التاريخ: {today}")
    s_data = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
    sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        prev = supabase.table('attendance').select("*").eq('committee', sel_c).eq('date', today).execute()
        att_dict = {p['student_name']: p['status'] for p in prev.data} if prev.data else {}
        results = []
        for s in students.data:
            p_stat = att_dict.get(s['student_name'], "حاضر")
            stat = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(p_stat), key=str(s['id']), horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
        if st.button("💾 حفظ الكشف"):
            supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
            supabase.table('attendance').insert(results).execute()
            st.success("تم الحفظ"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- لوحة الإدارة والتقرير الموحد ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز الدخول:", type="password") == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2 = st.tabs(["📊 تقرير الغياب الموحد", "🏘️ متابعة اللجان"])
    with tab1:
        d = st.date_input("تاريخ التقرير", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df_abs = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            if not df_abs.empty:
                # ترتيب اللجان
                df_abs['committee_num'] = pd.to_numeric(df_abs['committee'], errors='coerce')
                df_abs = df_abs.sort_values(by='committee_num')
                
                # جلب "الشعبة" من جدول الطلاب ودمجها لضمان ظهورها
                class_list = []
                for name in df_abs['student_name']:
                    s_info = supabase.table('students').select("class_name").eq("student_name", name).execute()
                    class_list.append(s_info.data[0]['class_name'] if s_info.data else "---")
                df_abs['الشعبة'] = class_list

                # عرض الجدول
                st.subheader(f"📋 كشف الغياب ليوم {d}")
                display_df = df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].copy()
                display_df.columns = ['اللجنة', 'اسم الطالب', 'الشعبة', 'الحالة', 'المعلم الراصد']
                st.table(display_df)
                
                # بناء رسالة الواتساب الموحدة
                msg = f"🗓️ *تقرير غياب مدرسة القطيف*%0A📅 *التاريخ:* {d}%0A"
                msg += "---------------------------------------%0A"
                for _, r in df_abs.iterrows():
                    msg += f"📦 *اللجنة:* {r['committee']} | 🏫 *الشعبة:* {r['الشعبة']}%0A👤 *الاسم:* {r['student_name']}%0A⚠️ *الحالة:* {r['status']}%0A--------------------%0A"
                
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="whatsapp-btn">إرسال التقرير الموحد عبر واتساب 📲</a>', unsafe_allow_html=True)
            else: st.success("لا يوجد غياب لهذا اليوم")
