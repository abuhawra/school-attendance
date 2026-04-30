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

# 2. التنسيق الجمالي (توسيط كامل وألوان محددة)
st.set_page_config(page_title="التحضير التقني - مدرسة القطيف", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .stApp { background-color: #f8f9fa; }
    .center-div { width: 100%; text-align: center; direction: rtl; }
    .main-title { font-size: 30px; font-weight: 800; color: #1a237e; margin-bottom: 0px; }
    .sub-title { font-size: 20px; color: #455a64; margin-top: 5px; }
    .manager-title { font-size: 18px; color: #1565c0; font-weight: bold; margin-top: 10px; }
    
    /* تنسيق الأزرار حسب الطلب */
    div.stButton > button { width: 100% !important; max-width: 350px !important; height: 55px !important; border-radius: 12px !important; font-size: 18px !important; font-weight: bold !important; margin: 10px auto !important; display: block !important; }
    /* زر التحضير - أزرق */
    div.stButton > button[kind="primary"] { background-color: #007bff !important; color: white !important; border: none; }
    /* زر الإدارة - برتقالي */
    div.stButton > button[kind="secondary"] { background-color: #ff9800 !important; color: white !important; border: none; }
    
    div[data-testid="stDataFrame"] { direction: rtl !important; }
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
    st.markdown('<div class="center-div">', unsafe_allow_html=True)
    st.markdown('<p class="main-title">التحضير التقني لمدرسة القطيف الثانوية</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">تصميم وتنفيذ أستاذ عارف أحمد الحداد</p>', unsafe_allow_html=True)
    st.markdown('<p class="manager-title">مدير المدرسة أ. فراس عبدالله آل عبدالمحسن</p>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("📝 الدخول للتحضير", type="primary"):
        st.session_state.page = "att_login"; st.rerun()
    
    if st.button("⚙️ دخول الإدارة", type="secondary"):
        st.session_state.page = "admin_login"; st.rerun()

# ==========================================
# 2. صفحة التحضير (دخول بالسجل المدني)
# ==========================================
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة"): go_home()
    st.markdown('<div class="center-div"><h3>تسجيل دخول المعلم</h3></div>', unsafe_allow_html=True)
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
    st.write(f"تاريخ اليوم: {today}")
    
    # اختيار اللجنة
    s_data = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in s_data.data])))
    sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
    
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        results = []
        for s in students.data:
            st.write(f"👤 **{s['student_name']}**")
            # التحضير الافتراضي "حاضر"
            stat = st.radio(f"الحالة لـ {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=0, key=f"s_{s['id']}", horizontal=True)
            results.append({
                "student_name": s['student_name'],
                "committee": str(sel_c),
                "status": stat,
                "date": today,
                "teacher_name": st.session_state.teacher_name
                # تم حذف class_name لأنه غير موجود في قاعدة البيانات لديك
            })
        
        if st.button("💾 حفظ وإرسال الكشف", type="primary"):
            try:
                # حذف القديم وحفظ الجديد
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("✅ تم الحفظ والإرسال بنجاح!")
                time.sleep(1.5)
                go_home() # إغلاق والعودة للرئيسية
            except Exception as e:
                st.error(f"خطأ في الحفظ: {e}")

# ==========================================
# 3. لوحة الإدارة (تقارير + واتساب + إدارة الأسماء)
# ==========================================
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): go_home()
    pw = st.text_input("رمز دخول الإدارة:", type="password")
    if pw == "1234":
        st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ تسجيل خروج"): go_home()
    
    tab1, tab2, tab3 = st.tabs(["📊 تقارير الغياب", "🏘️ متابعة اللجان", "🛠️ إدارة الأسماء"])
    
    with tab1:
        d = st.date_input("اختر التاريخ", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            # إظهار فقط غير الحاضر (غائب ومتأخر)
            df_view = df[df['status'].isin(['غائب', 'متأخر'])]
            
            if not df_view.empty:
                st.dataframe(df_view[['student_name', 'status', 'committee']], use_container_width=True)
                
                st.subheader("إرسال تقارير الواتساب 📲")
                for _, row in df_view.iterrows():
                    # رسالة منسقة بالبولد ورموز تعبيرية
                    msg = f"📌 *تقرير حالة طالب*\n\n" \
                          f"👤 *الاسم:* {row['student_name']}\n" \
                          f"📦 *اللجنة:* {row['committee']}\n" \
                          f"⚠️ *الحالة:* **{row['status']}**\n" \
                          f"📅 *التاريخ:* {d}"
                    link = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                    st.markdown(f"[{row['student_name']} - إرسال التفاصيل]({link})")
            else:
                st.success("لا يوجد غياب أو تأخر لهذا اليوم.")

    with tab2:
        # منطق اللجان المحضرة وغير المحضرة
        all_st = supabase.table('students').select("committee").execute()
        all_coms = set([str(i['committee']) for i in all_st.data])
        done_coms = set([str(i['committee']) for i in res.data]) if res.data else set()
        
        c1, c2 = st.columns(2)
        c1.error(f"لجان لم تحضر ({len(all_coms - done_coms)})")
        c1.write(list(all_coms - done_coms))
        c2.success(f"لجان حضرت ({len(done_coms)})")
        c2.write(list(done_coms))

    with tab3:
        st.markdown("### إدارة البيانات الحساسة")
        adm_pw = st.text_input("أدخل رمز إدارة الأسماء (للوصول للنسخ والحذف):", type="password")
        if adm_pw == "12345":
            col1, col2 = st.columns(2)
            if col1.button("📥 نسخة احتياطية (CSV)"):
                data = supabase.table("students").select("*").execute()
                csv = pd.DataFrame(data.data).to_csv(index=False).encode('utf-8-sig')
                st.download_button("تحميل الملف", csv, "students_backup.csv")
            
            if col2.button("🗑️ حذف جميع الأسماء"):
                st.warning("سيتم مسح كل الطلاب!")
                # supabase.table("students").delete().neq("id", 0).execute()
