import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io
import urllib.parse

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. التنسيق الجمالي والتوسيط (CSS)
st.set_page_config(page_title="التحضير التقني - مدرسة القطيف", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .stApp { background-color: #f4f7f9; }
    
    /* التوسيط الكامل */
    .block-container { display: flex; flex-direction: column; align-items: center; text-align: center; }
    .center-div { width: 100%; text-align: center; direction: rtl; }
    
    /* النصوص */
    .main-title { font-size: 32px; font-weight: 800; color: #1a237e; margin-bottom: 0px; }
    .sub-title { font-size: 22px; color: #455a64; margin-top: 5px; }
    .manager-title { font-size: 20px; color: #1565c0; font-weight: bold; margin-top: 15px; }
    
    /* الأزرار */
    .stButton button {
        width: 100% !important; max-width: 350px !important; height: 60px !important;
        border-radius: 15px !important; font-size: 20px !important; font-weight: bold !important;
        margin: 10px auto !important; display: block !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    /* زر التحضير - أزرق */
    div.stButton > button[kind="primary"] { background-color: #007bff !important; color: white !important; border: none; }
    /* زر الإدارة - برتقالي */
    div.stButton > button[kind="secondary"] { background-color: #ff9800 !important; color: white !important; border: none; }
    
    /* الجداول */
    div[data-testid="stDataFrame"] { direction: rtl !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. إدارة الحالة (State)
if 'page' not in st.session_state: st.session_state.page = "home"
if 'teacher_logged' not in st.session_state: st.session_state.teacher_logged = False

# --- الوظائف المساعدة ---
def go_home():
    st.session_state.page = "home"
    st.session_state.teacher_logged = False
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
        st.session_state.page = "attendance_login"; st.rerun()
    
    if st.button("⚙️ دخول الإدارة", type="secondary"):
        st.session_state.page = "admin_login"; st.rerun()

# ==========================================
# 2. صفحة تحضير المعلمين
# ==========================================
elif st.session_state.page == "attendance_login":
    if st.button("⬅️ عودة"): go_home()
    st.subheader("تسجيل دخول المعلم")
    t_id = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_logged = True
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل المدني غير مسجل")

elif st.session_state.page == "taking_attendance":
    st.info(f"المعلم: {st.session_state.teacher_name}")
    today_date = datetime.now().date()
    st.write(f"تاريخ اليوم: {today_date}")
    
    # اختيار اللجنة
    s_data = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in s_data.data])))
    sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
    
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        results = []
        for s in students.data:
            st.write(f"👤 **{s['student_name']}**")
            # التحضير الافتراضي هو "حاضر"
            stat = st.radio(f"الحالة لـ {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=0, key=f"s_{s['id']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": sel_c, "status": stat, "date": str(today_date), "teacher_name": st.session_state.teacher_name, "class_name": s.get('class_name', 'غير محدد')})
        
        if st.button("💾 حفظ وإرسال الكشف", type="primary"):
            with st.spinner("جاري الحفظ..."):
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(today_date)).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("تم الحفظ بنجاح!")
                time.sleep(1)
                go_home()

# ==========================================
# 3. لوحة الإدارة والتقارير
# ==========================================
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): go_home()
    pw = st.text_input("رمز دخول الإدارة:", type="password")
    if pw == "1234":
        st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ تسجيل خروج"): go_home()
    st.title("لوحة الإدارة")
    
    tab1, tab2, tab3 = st.tabs(["📊 التقارير والواتساب", "🏘️ متابعة اللجان", "🛠️ إدارة الأسماء"])
    
    # --- تبويب التقارير ---
    with tab1:
        d = st.date_input("تاريخ التقرير", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            # عرض فقط الغائب والمتأخر
            df_absent = df[df['status'].isin(['غائب', 'متأخر'])]
            st.dataframe(df_absent[['student_name', 'status', 'committee', 'class_name']], use_container_width=True)
            
            # إرسال واتساب
            if not df_absent.empty:
                st.subheader("إرسال التفاصيل عبر الواتساب")
                for _, row in df_absent.iterrows():
                    msg = f"*تقرير غياب يوم:* {d}\n\n👤 *الاسم:* {row['student_name']}\n🏫 *الشعبة:* {row['class_name']}\n📦 *اللجنة:* {row['committee']}\n⚠️ *الحالة:* {row['status']}"
                    link = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                    st.markdown(f"[{row['student_name']} - إرسال 📲]({link})")

    # --- تبويب متابعة اللجان ---
    with tab2:
        st.subheader("حالة لجان المدرسة")
        # منطق جلب اللجان التي حضرت والتي لم تحضر
        all_st = supabase.table('students').select("committee").execute()
        all_coms = set([str(i['committee']) for i in all_st.data])
        done_coms = set([str(i['committee']) for i in res.data]) if res.data else set()
        
        col1, col2 = st.columns(2)
        col1.error(f"لجان لم تحضر ({len(all_coms - done_coms)})")
        col1.write(list(all_coms - done_coms))
        col2.success(f"لجان تم تحضيرها ({len(done_coms)})")
        col2.write(list(done_coms))

    # --- تبويب إدارة الأسماء (محمي بـ 12345) ---
    with tab3:
        st.warning("هذا القسم يتطلب صلاحيات عليا")
        admin_pw = st.text_input("أدخل رمز إدارة الأسماء:", type="password", key="name_admin")
        if admin_pw == "12345":
            st.success("صلاحية الوصول مقبولة")
            # هنا تضع أزرار: (نسخة احتياطية، حذف الكل، استرجاع)
            if st.button("📥 أخذ نسخة احتياطية للطلاب"):
                all_students = supabase.table("students").select("*").execute()
                csv = pd.DataFrame(all_students.data).to_csv(index=False).encode('utf-8-sig')
                st.download_button("تحميل النسخة الاحتياطية CSV", csv, "backup_students.csv")
            
            if st.button("🗑️ حذف جميع بيانات الطلاب", type="secondary"):
                confirm = st.checkbox("أؤكد رغبتي في حذف جميع الأسماء")
                if confirm:
                    supabase.table("students").delete().neq("id", 0).execute()
                    st.error("تم مسح قاعدة البيانات")

            st.divider()
            uploaded_file = st.file_uploader("استرجاع بيانات من ملف Excel/CSV", type=["csv", "xlsx"])
            if uploaded_file and st.button("📤 إرجاع البيانات"):
                # منطق الرفع للسوبابيس
                st.info("جاري المعالجة والرفع...")
