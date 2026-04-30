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

# 2. إعدادات الصفحة والتنسيق (CSS)
st.set_page_config(page_title="التحضير التقني - مدرسة القطيف", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .stApp { background-color: #f8f9fa; }
    .center-div { width: 100%; text-align: center; direction: rtl; }
    .main-title { font-size: 32px; font-weight: 800; color: #1a237e; margin-bottom: 5px; }
    .sub-title { font-size: 20px; color: #455a64; margin-bottom: 20px; }
    div.stButton > button { width: 100% !important; max-width: 400px !important; height: 55px !important; border-radius: 15px !important; font-size: 20px !important; font-weight: bold !important; margin: 10px auto !important; display: block !important; transition: 0.3s; }
    div.stButton > button[kind="primary"] { background-color: #007bff !important; color: white !important; border: none; }
    div.stButton > button[kind="secondary"] { background-color: #ff9800 !important; color: white !important; border: none; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- دالة العودة للرئيسية ---
def go_home():
    st.session_state.page = "home"
    st.rerun()

# ==========================================
# 🏠 1. الصفحة الرئيسية
# ==========================================
if st.session_state.page == "home":
    st.markdown('<div class="center-div">', unsafe_allow_html=True)
    st.markdown('<p class="main-title">التحضير التقني لمدرسة القطيف الثانوية</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">إشراف الأستاذ: عارف أحمد الحداد</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:18px; color:#1565c0; font-weight:bold;">مدير المدرسة: أ. فراس عبدالله آل عبدالمحسن</p>', unsafe_allow_html=True)
    st.markdown('<hr style="width:50%; margin:auto;">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("") # مسافة
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📝 دخول المعلم للرصد", type="primary"):
            st.session_state.page = "att_login"; st.rerun()
        
        if st.button("⚙️ لوحة تحكم الإدارة", type="secondary"):
            st.session_state.page = "admin_login"; st.rerun()

# ==========================================
# 📝 2. رصد الحضور
# ==========================================
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة"): go_home()
    st.markdown('<div class="center-div"><h3>تسجيل الدخول</h3></div>', unsafe_allow_html=True)
    t_id = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول", type="primary"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل المدني غير مسجل")

elif st.session_state.page == "taking_attendance":
    today = str(datetime.now().date())
    st.markdown(f'<p style="text-align:right; font-weight:bold;">📅 التاريخ: {today}</p>', unsafe_allow_html=True)
    st.info(f"المعلم: {st.session_state.teacher_name}")
    
    # جلب اللجان
    s_data = supabase.table('students').select("committee").execute()
    raw_coms = list(set([i['committee'] for i in s_data.data if i['committee'] is not None]))
    sorted_coms = sorted(raw_coms, key=lambda x: int(x) if str(x).isdigit() else 0)

    sel_c = st.selectbox("اختر اللجنة للرصد:", ["---"] + [str(x) for x in sorted_coms])
    
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        # جلب رصد سابق إن وجد للتعديل عليه
        prev = supabase.table('attendance').select("*").eq('committee', sel_c).eq('date', today).execute()
        att_dict = {p['student_name']: p['status'] for p in prev.data} if prev.data else {}

        results = []
        for s in students.data:
            st.write(f"👤 **{s['student_name']}**")
            p_stat = att_dict.get(s['student_name'], "حاضر")
            idx = ["حاضر", "غائب", "متأخر"].index(p_stat)
            stat = st.radio(f"الحالة لـ {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=idx, key=f"s_{s['id']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
        
        if st.button("💾 حفظ وإرسال الكشف", type="primary"):
            try:
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("✅ تم الحفظ بنجاح!")
                time.sleep(1); go_home()
            except Exception as e: st.error(f"خطأ أثناء الحفظ: {e}")

# ==========================================
# ⚙️ 3. لوحة الإدارة والتقارير
# ==========================================
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): go_home()
    pw = st.text_input("رمز الدخول:", type="password")
    if pw == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ خروج"): go_home()
    tab1, tab2, tab3 = st.tabs(["📊 تقرير الغياب والواتساب", "🏘️ متابعة اللجان", "🛠️ إدارة البيانات"])
    
    with tab1:
        d_rep = st.date_input("اختر تاريخ التقرير", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d_rep)).execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            df_absent = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            
            if not df_absent.empty:
                # جلب الشعبة بأمان لتجنب الخطأ الظاهر في الصورة
                classes = []
                for n in df_absent['student_name']:
                    try:
                        si = supabase.table('students').select("class_name").eq("student_name", n).execute()
                        classes.append(si.data[0]['class_name'] if si.data else "---")
                    except: classes.append("---")
                df_absent['الشعبة'] = classes
                
                # عرض الجدول
                st.subheader(f"كشف الحالات غير الحاضرة لليوم")
                st.dataframe(df_absent[['student_name', 'الشعبة', 'committee', 'status', 'teacher_name']], use_container_width=True)
                
                st.divider()
                st.subheader("إرسال للواتساب 📲")
                for _, r in df_absent.iterrows():
                    msg = (f"🗓️ *تقرير مدرسة القطيف*%0A%0A👤 *الاسم:* {r['student_name']}%0A🏫 *الشعبة:* {r['الشعبة']}%0A📦 *اللجنة:* {r['committee']}%0A⚠️ *الحالة:* *{r['status']}*")
                    url_wa = f"https://wa.me/?text={msg}"
                    st.markdown(f'<a href="{url_wa}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:10px;border-radius:10px;text-align:center;margin-bottom:8px;font-weight:bold;">إرسال تقرير: {r["student_name"]} 📲</div></a>', unsafe_allow_html=True)
            else: st.success("لا يوجد غياب اليوم.")
            
    with tab2:
        st.write("متابعة اللجان التي لم ترصد بعد...")
        # (منطق عرض اللجان المتبقية)

    with tab3:
        if st.text_input("رمز الإدارة العليا:", type="password") == "12345":
            st.write("إدارة قاعدة البيانات...")
