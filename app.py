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

# 2. تحسين مظهر الواجهة
st.set_page_config(page_title="نظام مدرسة القطيف", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; direction: rtl; }
    .main-title { font-size: 30px; font-weight: 800; color: #1a237e; text-align: center; }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-align: center; text-decoration: none; display: block; font-weight: bold; margin: 10px auto; }
    div.stButton > button { width: 100%; border-radius: 12px; font-weight: bold; height: 50px; }
    .status-card { padding: 20px; border-radius: 15px; margin-bottom: 10px; border: 1px solid #ddd; }
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
        if st.button("⚙️ لوحة الإدارة والتقارير"): st.session_state.page = "admin_login"; st.rerun()

# --- دخول المعلمين ---
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
    
    # جلب اللجان المتاحة
    s_data = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
    
    sel_c = st.selectbox("اختر اللجنة لرصدها:", ["---"] + coms)
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        results = []
        for s in students.data:
            stat = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], key=f"s_{s['id']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
        
        if st.button("💾 حفظ الكشف"):
            try:
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("تم الحفظ بنجاح"); time.sleep(1); st.session_state.page = "home"; st.rerun()
            except Exception as e: st.error(f"خطأ في قاعدة البيانات: {e}")

# --- لوحة الإدارة والمتابعة ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز الدخول:", type="password") == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2 = st.tabs(["📊 تقرير الغياب الموحد", "🏘️ متابعة حالة اللجان"])
    
    today_date = str(datetime.now().date())

    with tab1:
        d = st.date_input("اختر تاريخ التقرير", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df_abs = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            if not df_abs.empty:
                # ترتيب حسب اللجنة
                df_abs['committee_num'] = pd.to_numeric(df_abs['committee'], errors='coerce')
                df_abs = df_abs.sort_values(by='committee_num')
                
                # جلب "الشعبة" بحذر لتجنب APIError
                classes = []
                for name in df_abs['student_name']:
                    try:
                        si = supabase.table('students').select("class_name").eq("student_name", name).execute()
                        classes.append(si.data[0]['class_name'] if si.data else "---")
                    except: classes.append("---")
                df_abs['الشعبة'] = classes

                st.subheader(f"📋 كشف الحالات ليوم {d}")
                disp = df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].copy()
                disp.columns = ['اللجنة', 'اسم الطالب', 'الشعبة', 'الحالة', 'المعلم الراصد']
                st.table(disp)
                
                # رسالة الواتساب
                msg = f"🗓️ *تقرير مدرسة القطيف*%0A📅 *التاريخ:* {d}%0A"
                for _, r in df_abs.iterrows():
                    msg += f"📦 *لجنة:* {r['committee']} | 🏫 *شعبة:* {r['الشعبة']}%0A👤 *الاسم:* {r['student_name']} ({r['status']})%0A--------------------%0A"
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="whatsapp-btn">إرسال التقرير الموحد عبر واتساب 📲</a>', unsafe_allow_html=True)
            else: st.success("لا توجد حالات غياب")

    with tab2:
        st.subheader(f"🏘️ متابعة اللجان اليوم: {today_date}")
        # جلب قائمة اللجان الكلية
        all_s = supabase.table('students').select("committee").execute()
        total_coms = sorted(list(set([str(i['committee']) for i in all_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        
        # جلب اللجان التي رصدت اليوم
        done_res = supabase.table('attendance').select("committee, teacher_name").eq("date", today_date).execute()
        done_coms = {str(i['committee']): i['teacher_name'] for i in done_res.data}
        
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ لجان تم رصدها")
            for c in total_coms:
                if c in done_coms:
                    st.write(f"📍 **اللجنة {c}** - رصدها: {done_coms[c]}")
        with c2:
            st.error("❌ لجان لم ترصد بعد")
            for c in total_coms:
                if c not in done_coms:
                    st.write(f"⚠️ **اللجنة {c}** - بانتظار الرصد")
