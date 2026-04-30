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

# 2. إعدادات الواجهة والتنسيق
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; direction: rtl; }
    .main-title { font-size: 32px; font-weight: 800; color: #1a237e; text-align: center; margin-bottom: 20px; }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 18px; border-radius: 15px; text-align: center; text-decoration: none; display: block; font-weight: bold; margin: 20px auto; max-width: 600px; font-size: 20px; border: 1px solid #128C7E; }
    div.stButton > button { width: 100%; border-radius: 12px; font-weight: bold; height: 50px; }
    th { background-color: #1a237e !important; color: white !important; text-align: center !important; }
    td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- 🏠 الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('<p class="main-title">التحضير التقني لمدرسة القطيف الثانوية</p>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; font-size:18px;">مدير المدرسة: أ. فراس آل عبدالمحسن | إشراف: أ. عارف الحداد</p><hr>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📝 دخول المعلمين للرصد", type="primary"): st.session_state.page = "att_login"; st.rerun()
        if st.button("⚙️ لوحة الإدارة والتقارير"): st.session_state.page = "admin_login"; st.rerun()

# --- 📝 نظام رصد المعلمين ---
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
        results = []
        for s in students.data:
            stat = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], key=f"s_{s['id']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
        if st.button("💾 حفظ الرصد"):
            supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
            supabase.table('attendance').insert(results).execute()
            st.success("✅ تم الحفظ بنجاح"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- ⚙️ لوحة الإدارة والتقارير ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز دخول المسؤول:", type="password") == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ تسجيل الخروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير الموحدة", "🏘️ متابعة اللجان", "💾 إدارة البيانات"])
    
    with tab1:
        d = st.date_input("اختر التاريخ", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res_att.data:
            df_att = pd.DataFrame(res_att.data)
            df_abs = df_att[df_att['status'].isin(['غائب', 'متأخر'])].copy()
            
            if not df_abs.empty:
                # حل "الشعبة" - جلب أسماء الطلاب وشعبهم برمجياً لتجنب خطأ API
                res_std = supabase.table("students").select("student_name, class_name").execute()
                df_std_info = pd.DataFrame(res_std.data)
                
                # دمج الشعبة بناءً على الاسم
                df_final = pd.merge(df_abs, df_std_info, on="student_name", how="left")
                
                st.subheader(f"📋 كشف الحالات ليوم {d}")
                # عرض الجدول بالترتيب المطلوب
                view = df_final[['committee', 'student_name', 'class_name', 'status', 'teacher_name']].copy()
                view.columns = ['رقم اللجنة', 'اسم الطالب', 'الشعبة', 'الحالة', 'المعلم']
                st.table(view)
                
                # رسالة واتساب الموحدة
                msg = f"🗓️ *تقرير مدرسة القطيف*%0A📅 *التاريخ:* {d}%0A"
                for _, r in df_final.iterrows():
                    msg += f"📦 *لجنة:* {r['committee']} | 🏫 *شعبة:* {r['class_name']}%0A👤 *الاسم:* {r['student_name']} ({r['status']})%0A"
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="whatsapp-btn">إرسال عبر واتساب 📲</a>', unsafe_allow_html=True)
            else: st.success("لا توجد حالات غياب")
        else: st.info("لا توجد بيانات لهذا التاريخ")

    with tab2:
        # كود متابعة اللجان المستقر كما هو
        st.write("🏘️ متابعة حالة رصد اللجان")
        # ... (بقية كود المتابعة المستقر)

    with tab3:
        if st.text_input("الرقم السري للإدارة:", type="password") == "4321":
            st.success("تم تفعيل صلاحيات الإدارة")
            # ... (بقية أدوات المسح والاستعادة المستقرة)
