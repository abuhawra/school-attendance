import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. التنسيق الجمالي وتوسيط الواجهة
st.set_page_config(page_title="نظام مدرسة القطيف", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .stApp { background-color: #f8f9fa; direction: rtl; }
    .main-title { font-size: 32px; font-weight: 800; color: #1a237e; text-align: center; }
    div.stButton > button { width: 100%; max-width: 400px; height: 55px; border-radius: 12px; font-weight: bold; margin: 10px auto; display: block; }
    div.stButton > button[kind="primary"] { background-color: #007bff !important; color: white !important; }
    div.stButton > button[kind="secondary"] { background-color: #ff9800 !important; color: white !important; }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 18px; border-radius: 15px; text-align: center; text-decoration: none; display: block; font-weight: bold; margin: 20px auto; max-width: 500px; border: 1px solid #128C7E; font-size: 20px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# ==========================================
# 🏠 1. الصفحة الرئيسية
# ==========================================
if st.session_state.page == "home":
    st.markdown('<p class="main-title">التحضير التقني لمدرسة القطيف الثانوية</p>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; font-size:18px;">بإشراف أ. عارف الحداد | مدير المدرسة أ. فراس آل عبدالمحسن</p><hr>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📝 دخول المعلمين للرصد", type="primary"): st.session_state.page = "att_login"; st.rerun()
        if st.button("⚙️ لوحة الإدارة والتقارير", type="secondary"): st.session_state.page = "admin_login"; st.rerun()

# ==========================================
# 📝 2. رصد الحضور (مع ميزة التعديل)
# ==========================================
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة للرئيسية"): st.session_state.page = "home"; st.rerun()
    t_id = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل غير مسجل في النظام")

elif st.session_state.page == "taking_attendance":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher_name} | التاريخ: {today}")
    
    # جلب اللجان مرتبة رقمياً
    s_data = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
    sel_c = st.selectbox("اختر اللجنة المراد رصدها:", ["---"] + coms)
    
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        # جلب رصد سابق لهذا اليوم إن وجد للسماح بالتعديل
        prev = supabase.table('attendance').select("*").eq('committee', sel_c).eq('date', today).execute()
        att_dict = {p['student_name']: p['status'] for p in prev.data} if prev.data else {}

        results = []
        st.write("---")
        for s in students.data:
            p_stat = att_dict.get(s['student_name'], "حاضر") # الافتراضي حاضر
            stat = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], 
                            index=["حاضر", "غائب", "متأخر"].index(p_stat), key=f"std_{s['id']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
        
        if st.button("💾 حفظ وإرسال الكشف", type="primary"):
            try:
                # حذف القديم وحفظ الجديد
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("✅ تم الحفظ بنجاح!"); time.sleep(1); st.session_state.page = "home"; st.rerun()
            except Exception as e: st.error(f"خطأ أثناء الحفظ: {e}")

# ==========================================
# ⚙️ 3. لوحة الإدارة والتقرير الموحد (مرتب)
# ==========================================
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز دخول الإدارة:", type="password") == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2 = st.tabs(["📊 تقرير الغياب الموحد", "🏘️ متابعة اللجان"])
    
    with tab1:
        d = st.date_input("اختر تاريخ التقرير", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df_abs = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            if not df_abs.empty:
                # 1. الترتيب حسب رقم اللجنة
                df_abs['committee_num'] = pd.to_numeric(df_abs['committee'], errors='coerce')
                df_abs = df_abs.sort_values(by='committee_num')
                
                # 2. جلب الشعبة من جدول الطلاب بأمان
                classes = []
                for n in df_abs['student_name']:
                    try:
                        si = supabase.table('students').select("class_name").eq("student_name", n).execute()
                        classes.append(si.data[0]['class_name'] if si.data else "---")
                    except: classes.append("---")
                df_abs['الشعبة'] = classes
                
                # 3. عرض الجدول
                st.subheader(f"📋 كشف الغياب والتأخر (مرتب باللجان)")
                st.table(df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee': 'اللجنة', 'student_name': 'الاسم'}))
                
                # 4. إنشاء الرسالة الموحدة
                msg_header = f"🗓️ *تقرير مدرسة القطيف (مرتب لجان)*%0A📅 *التاريخ:* {d}%0A"
                msg_header += "---------------------------------------%0A"
                msg_
