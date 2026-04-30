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

# 2. تحسين مظهر الواجهة (CSS)
st.set_page_config(page_title="نظام مدرسة القطيف", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; direction: rtl; }
    .main-title { font-size: 32px; font-weight: 800; color: #1a237e; text-align: center; }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 18px; border-radius: 15px; text-align: center; text-decoration: none; display: block; font-weight: bold; margin: 20px auto; max-width: 500px; font-size: 20px; border: 1px solid #128C7E; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
    div.stButton > button { width: 100%; max-width: 400px; height: 55px; border-radius: 12px; font-weight: bold; margin: 10px auto; display: block; }
    div.stButton > button[kind="primary"] { background-color: #007bff !important; color: white !important; }
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
        if st.button("⚙️ لوحة الإدارة والتقارير"): st.session_state.page = "admin_login"; st.rerun()

# ==========================================
# 📝 2. نظام رصد الحضور (إصلاح خطأ الحفظ)
# ==========================================
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    t_id = st.text_input("رقم السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("عذراً، السجل غير مسجل")

elif st.session_state.page == "taking_attendance":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher_name} | التاريخ: {today}")
    
    # جلب اللجان
    s_data = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
    sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
    
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        # محاولة استرجاع رصد سابق للتعديل
        prev = supabase.table('attendance').select("*").eq('committee', sel_c).eq('date', today).execute()
        att_dict = {p['student_name']: p['status'] for p in prev.data} if prev.data else {}

        results = []
        for s in students.data:
            p_stat = att_dict.get(s['student_name'], "حاضر")
            stat = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], 
                            index=["حاضر", "غائب", "متأخر"].index(p_stat), key=f"std_{s['id']}", horizontal=True)
            # ملاحظة: لا نضع class_name هنا لمنع خطأ قاعدة البيانات
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
        
        if st.button("💾 حفظ وإرسال الكشف", type="primary"):
            try:
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("✅ تم الحفظ بنجاح"); time.sleep(1); st.session_state.page = "home"; st.rerun()
            except Exception as e: st.error(f"حدث خطأ أثناء الحفظ: {e}")

# ==========================================
# ⚙️ 3. لوحة الإدارة والتقرير الموحد (إصلاح الشعبة والترتيب)
# ==========================================
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
                # 1. الترتيب حسب رقم اللجنة
                df_abs['committee_num'] = pd.to_numeric(df_abs['committee'], errors='coerce')
                df_abs = df_abs.sort_values(by='committee_num')
                
                # 2. جلب "الشعبة" من جدول الطلاب لضمان ظهورها
                ch_list = []
                for name in df_abs['student_name']:
                    try:
                        si = supabase.table('students').select("class_name").eq("student_name", name).execute()
                        ch_list.append(si.data[0]['class_name'] if si.data else "---")
                    except: ch_list.append("---")
                df_abs['الشعبة'] = ch_list
                
                # 3. عرض الجدول بعناوين عربية مرتبة
                st.subheader(f"📋 كشف الحالات المرصودة ليوم {d}")
                display_df = df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].copy()
                display_df.columns = ['اللجنة', 'اسم الطالب', 'الشعبة', 'الحالة', 'المعلم الراصد']
                st.table(display_df)
                
                # 4. بناء رسالة الواتساب الموحدة
                msg = f"🗓️ *تقرير غياب مدرسة القطيف*%0A📅 *التاريخ:* {d}%0A---------------------------------------%0A"
                for _, r in df_abs.iterrows():
                    msg += f"📦 *اللجنة:* {r['committee']} | 🏫 *الشعبة:* {r['الشعبة']}%0A👤 *الاسم:* {r['student_name']}%0A⚠️ *الحالة:* {r['status']}%0A--------------------%0A"
                
                # 5. زر الواتساب الموحد الأخضر
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="whatsapp-btn">إرسال التقرير الموحد عبر واتساب 📲</a>', unsafe_allow_html=True)
            else:
                st.success("✅ لا توجد حالات غياب أو تأخر في هذا التاريخ.")
        else:
            st.warning("لم يتم رصد أي بيانات لهذا اليوم بعد.")
