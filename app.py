import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse
import io

# 1. إعدادات الاتصال
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. التنسيق الجمالي وتوسيط الواجهة
st.set_page_config(page_title="التحضير التقني - مدرسة القطيف", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .stApp { background-color: #f8f9fa; }
    .center-div { width: 100%; text-align: center; direction: rtl; }
    .main-title { font-size: 30px; font-weight: 800; color: #1a237e; }
    div.stButton > button { width: 100% !important; max-width: 350px !important; height: 55px !important; border-radius: 12px !important; font-size: 18px !important; font-weight: bold !important; margin: 10px auto !important; display: block !important; }
    div.stButton > button[kind="primary"] { background-color: #007bff !important; color: white !important; }
    div.stButton > button[kind="secondary"] { background-color: #ff9800 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

def go_home():
    st.session_state.page = "home"
    st.rerun()

# ==========================================
# 1. الواجهة الرئيسية
# ==========================================
if st.session_state.page == "home":
    st.markdown('<div class="center-div"><p class="main-title">التحضير التقني لمدرسة القطيف الثانوية</p><p>تصميم وتنفيذ أستاذ عارف أحمد الحداد</p><p>مدير المدرسة أ. فراس عبدالله آل عبدالمحسن</p></div><hr>', unsafe_allow_html=True)
    if st.button("📝 الدخول للتحضير", type="primary"): st.session_state.page = "att_login"; st.rerun()
    if st.button("⚙️ دخول الإدارة", type="secondary"): st.session_state.page = "admin_login"; st.rerun()

# ==========================================
# 2. صفحة التحضير (بناءً على السجل المدني)
# ==========================================
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة"): go_home()
    t_id = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول", type="primary"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل المدني غير مسجل")

elif st.session_state.page == "taking_attendance":
    st.info(f"المعلم: {st.session_state.teacher_name}")
    today = str(datetime.now().date())
    
    s_data = supabase.table('students').select("committee").execute()
    raw_coms = list(set([i['committee'] for i in s_data.data if i['committee'] is not None]))
    try: sorted_coms = sorted(raw_coms, key=lambda x: int(x))
    except: sorted_coms = sorted([str(x) for x in raw_coms])

    sel_c = st.selectbox("اختر اللجنة:", ["---"] + [str(x) for x in sorted_coms])
    
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        results = []
        for s in students.data:
            st.write(f"👤 **{s['student_name']}**")
            stat = st.radio(f"الحالة لـ {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=0, key=f"s_{s['id']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
        
        if st.button("💾 حفظ وإرسال الكشف", type="primary"):
            try:
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("✅ تم الحفظ بنجاح!")
                time.sleep(1)
                go_home()
            except Exception as e: st.error(f"خطأ في الحفظ: {e}")

# ==========================================
# 3. لوحة الإدارة (تقارير - متابعة - إدارة بيانات)
# ==========================================
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): go_home()
    pw = st.text_input("رمز دخول الإدارة:", type="password")
    if pw == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ خروج"): go_home()
    tab1, tab2, tab3 = st.tabs(["📊 تقارير الواتساب", "🏘️ متابعة اللجان", "🛠️ إدارة البيانات"])
    
    # --- نافذة الواتساب ---
    with tab1:
        d = st.date_input("تاريخ التقرير", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df_view = df[df['status'].isin(['غائب', 'متأخر'])]
            if not df_view.empty:
                for _, row in df_view.iterrows():
                    # محاولة جلب الشعبة بأمان
                    try:
                        s_info = supabase.table('students').select("class_name").eq("student_name", row['student_name']).execute()
                        c_name = s_info.data[0]['class_name'] if s_info.data else "غير محدد"
                    except: c_name = "غير محدد"

                    msg = (f"🗓️ *التاريخ:* {d}%0A%0A👤 *الاسم:* {row['student_name']}%0A🏫 *الشعبة:* {c_name}%0A📦 *اللجنة:* {row['committee']}%0A⚠️ *الحالة:* *{row['status']}*%0A%0Aمدرسة القطيف الثانوية")
                    wa_link = f"https://wa.me/?text={msg}"
                    st.markdown(f'<a href="{wa_link}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:10px;border-radius:10px;text-align:center;margin-bottom:5px;">إرسال تقرير: {row['student_name']} 📲</div></a>', unsafe_allow_html=True)
            else: st.success("لا يوجد غياب اليوم")

    # --- نافذة متابعة اللجان ---
    with tab2:
        st.subheader("رصد اللجان")
        all_st = supabase.table('students').select("committee").execute()
        all_coms = set([str(i['committee']) for i in all_st.data if i['committee']])
        done_coms = set([str(i['committee']) for i in res.data]) if res.data else set()
        
        c1, c2 = st.columns(2)
        c1.error(f"لجان لم تُرصد ({len(all_coms - done_coms)})")
        c1.write(list(all_coms - done_coms))
        c2.success(f"لجان تـم رصدها ({len(done_coms)})")
        c2.write(list(done_coms))

    # --- نافذة إدارة البيانات (نسخة احتياطية وإرجاع) ---
    with tab3:
        adm_pw = st.text_input("رمز الإدارة العليا (12345):", type="password")
        if adm_pw == "12345":
            st.write("### العمليات على البيانات")
            if st.button("📥 أخذ نسخة احتياطية للطلاب"):
                data = supabase.table("students").select("*").execute()
                df_backup = pd.DataFrame(data.data)
                csv = df_backup.to_csv(index=False).encode('utf-8-sig')
                st.download_button("تحميل ملف النسخة الاحتياطية CSV", csv, "students_backup.csv", "text/csv")

            st.divider()
            uploaded_file = st.file_uploader("اختر ملف CSV لإرجاع البيانات", type="csv")
            if uploaded_file is not None:
                if st.button("📤 تأكيد إرجاع البيانات"):
                    df_upload = pd.read_csv(uploaded_file)
                    # تحويل البيانات لقائمة قواميس للرفع
                    data_to_insert = df_upload.to_dict(orient='records')
                    # مسح القديم ورفع الجديد
                    supabase.table("students").delete().neq("id", 0).execute()
                    supabase.table("students").insert(data_to_insert).execute()
                    st.success("تم إرجاع البيانات بنجاح!")
