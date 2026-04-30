import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# 1. إعدادات الاتصال
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. التنسيق الجمالي
st.set_page_config(page_title="التحضير التقني - مدرسة القطيف", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .stApp { background-color: #f8f9fa; }
    .center-div { width: 100%; text-align: center; direction: rtl; }
    .main-title { font-size: 30px; font-weight: 800; color: #1a237e; }
    div.stButton > button { width: 100% !important; max-width: 350px !important; height: 50px !important; border-radius: 12px !important; font-size: 18px !important; font-weight: bold !important; margin: 10px auto !important; display: block !important; }
    div.stButton > button[kind="primary"] { background-color: #007bff !important; color: white !important; }
    div.stButton > button[kind="secondary"] { background-color: #ff9800 !important; color: white !important; }
    .report-table { direction: rtl; text-align: right; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('<div class="center-div"><p class="main-title">التحضير التقني لمدرسة القطيف الثانوية</p><p>تصميم وتنفيذ أستاذ عارف أحمد الحداد</p><p>مدير المدرسة أ. فراس عبدالله آل عبدالمحسن</p></div><hr>', unsafe_allow_html=True)
    if st.button("📝 الدخول للتحضير", type="primary"): st.session_state.page = "att_login"; st.rerun()
    if st.button("⚙️ دخول الإدارة", type="secondary"): st.session_state.page = "admin_login"; st.rerun()

# --- تسجيل دخول المعلم ---
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    t_id = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول", type="primary"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل المدني غير مسجل")

# --- صفحة رصد الحضور ---
elif st.session_state.page == "taking_attendance":
    today = str(datetime.now().date())
    st.markdown(f'<div style="text-align:right; font-weight:bold; color:#1a237e;">📅 تاريخ اليوم: {today}</div>', unsafe_allow_html=True)
    st.info(f"المعلم: {st.session_state.teacher_name}")
    
    s_data = supabase.table('students').select("committee").execute()
    raw_coms = list(set([i['committee'] for i in s_data.data if i['committee'] is not None]))
    try: sorted_coms = sorted(raw_coms, key=lambda x: int(x))
    except: sorted_coms = sorted([str(x) for x in raw_coms])

    sel_c = st.selectbox("اختر اللجنة:", ["---"] + [str(x) for x in sorted_coms])
    
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        existing_att = supabase.table('attendance').select("*").eq('committee', sel_c).eq('date', today).execute()
        att_dict = {a['student_name']: a['status'] for a in existing_att.data} if existing_att.data else {}

        results = []
        for s in students.data:
            st.write(f"👤 **{s['student_name']}**")
            prev_status = att_dict.get(s['student_name'], "حاضر")
            idx = ["حاضر", "غائب", "متأخر"].index(prev_status)
            stat = st.radio(f"الحالة", ["حاضر", "غائب", "متأخر"], index=idx, key=f"s_{s['id']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
        
        if st.button("💾 حفظ وإرسال الكشف", type="primary"):
            try:
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("✅ تم تحديث الرصد بنجاح!")
                time.sleep(1)
                st.session_state.page = "home"; st.rerun()
            except Exception as e: st.error(f"خطأ: {e}")

# --- لوحة الإدارة ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    pw = st.text_input("رمز الإدارة:", type="password")
    if pw == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 تقارير الغياب", "🏘️ متابعة اللجان", "🛠️ إدارة البيانات"])
    
    with tab1:
        d_rep = st.date_input("اختر التاريخ", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d_rep)).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            # استخراج الشعبة من جدول الطلاب
            df_absent = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            
            if not df_absent.empty:
                # محاولة إضافة عمود الشعبة
                classes = []
                for name in df_absent['student_name']:
                    try:
                        s_info = supabase.table('students').select("class_name").eq("student_name", name).execute()
                        classes.append(s_info.data[0]['class_name'] if s_info.data else "غير محدد")
                    except: classes.append("غير محدد")
                df_absent['الشعبة'] = classes
                
                # ترتيب وتنظيم الجدول للعرض
                df_show = df_absent[['student_name', 'الشعبة', 'committee', 'status', 'teacher_name']]
                df_show.columns = ['اسم الطالب', 'الشعبة', 'اللجنة', 'الحالة', 'المعلم']
                
                st.subheader(f"📋 كشف الغياب والتأخر لتاريخ {d_rep}")
                st.table(df_show)
                
                st.divider()
                st.subheader("📲 إرسال تقارير الواتساب")
                for _, row in df_show.iterrows():
                    msg = (f"🗓️ *تقرير غياب - مدرسة القطيف*%0A%0A"
                           f"👤 *الاسم:* {row['اسم الطالب']}%0A"
                           f"🏫 *الشعبة:* {row['الشعبة']}%0A"
                           f"📦 *اللجنة:* {row['اللجنة']}%0A"
                           f"⚠️ *الحالة:* *{row['الحالة']}*%0A"
                           f"📅 *التاريخ:* {d_rep}")
                    
                    wa_url = f"https://wa.me/?text={msg}"
                    st.markdown(f'''<a href="{wa_url}" target="_blank" style="text-decoration:none;">
                        <div style="background-color:#25D366; color:white; padding:10px; border-radius:10px; text-align:center; margin-bottom:8px; font-weight:bold;">
                        إرسال تقرير الطالب: {row['اسم الطالب']} 📲
                        </div></a>''', unsafe_allow_html=True)
            else: st.success("لا يوجد حالات غياب أو تأخر مسجلة.")

    with tab2:
        # منطق متابعة اللجان
        all_st = supabase.table('students').select("committee").execute()
        all_c = set([str(i['committee']) for i in all_st.data if i['committee']])
        done_c = set([str(i['committee']) for i in res.data]) if res.data else set()
        c1, c2 = st.columns(2)
        c1.error(f"لجان لم تُرصد ({len(all_c - done_c)})")
        c1.write(sorted(list(all_c - done_c), key=lambda x: int(x) if x.isdigit() else 0))
        c2.success(f"لجان تـم رصدها ({len(done_c)})")
        c2.write(sorted(list(done_c), key=lambda x: int(x) if x.isdigit() else 0))

    with tab3:
        # إدارة البيانات
        adm_pw = st.text_input("رمز الإدارة العليا (12345):", type="password")
        if adm_pw == "12345":
