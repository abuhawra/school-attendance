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

# 2. إعدادات الواجهة (CSS) - النسخة الكلاسيكية المستقرة
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; background-color: #f4f7f9; }
    .stApp { background-color: #f4f7f9; }
    
    /* تصميم الواجهة الكلاسيكية المعدل */
    .classic-header {
        background-color: #1a237e;
        padding: 35px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        border-bottom: 5px solid #ffd700;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .line-1 { font-size: 34px; font-weight: 800; margin-bottom: 5px; color: #ffffff; }
    .line-2 { font-size: 28px; font-weight: 700; margin-bottom: 15px; color: #e0e0e0; }
    
    /* تنسيق الخط الفاصل الموسط */
    .centered-hr {
        border: 0;
        height: 1px;
        background: rgba(255, 255, 255, 0.3);
        width: 40%;
        margin: 20px auto; /* التوسيط في المنتصف */
    }
    
    .line-3 { font-size: 18px; margin-bottom: 2px; color: #ffd700; letter-spacing: 1px; }
    .line-4 { font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    .line-5 { font-size: 18px; margin-bottom: 2px; color: #cfd8dc; }
    .line-6 { font-size: 22px; font-weight: bold; }

    /* تنسيق العناصر التقنية */
    .stTextInput > div > div > input { background-color: white !important; border: 1px solid #1a237e !important; border-radius: 8px !important; }
    div.stButton > button { border-radius: 12px; font-weight: bold; height: 55px; font-size: 18px !important; transition: 0.3s; }
    div.stButton > button:hover { transform: scale(1.02); }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-align: center; text-decoration: none; display: block; font-weight: bold; margin: 15px auto; max-width: 500px; }
    th { background-color: #1a237e !important; color: white !important; text-align: center !important; }
    td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- 🏠 1. الصفحة الرئيسية (الواجهة المحدثة بالتوسيط) ---
if st.session_state.page == "home":
    st.markdown("""
        <div class="classic-header">
            <div class="line-1">التحضير التقني</div>
            <div class="line-2">مدرسة القطيف الثانوية</div>
            <div class="centered-hr"></div>
            <div class="line-3">فكرة وبرمجة</div>
            <div class="line-4">أ. عارف أحمد الحداد</div>
            <div class="line-5">مدير المدرسة</div>
            <div class="line-6">أ. فراس عبدالله آل عبد المحسن</div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.button("📝 دخول المعلمين للرصد", type="primary"): 
            st.session_state.page = "att_login"
            st.rerun()
        st.write(" ")
        if st.button("⚙️ لوحة الإدارة والتقارير"): 
            st.session_state.page = "admin_login"
            st.rerun()

# --- 📝 2. نظام رصد المعلمين (تثبيت حالة التحضير) ---
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة للرئيسية"): st.session_state.page = "home"; st.rerun()
    st.markdown("### 🔐 تسجيل دخول المعلم")
    t_id = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("عذراً، الرقم غير مسجل")

elif st.session_state.page == "taking_attendance":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher_name} | التاريخ: {today}")
    
    s_data = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
    
    sel_c = st.selectbox("اختر اللجنة المراد رصدها:", ["---"] + coms)
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        
        # جلب التحضير السابق لهذا اليوم (تثبيت الحالة)
        old_att = supabase.table('attendance').select("student_name, status").eq('committee', sel_c).eq('date', today).execute()
        old_map = {item['student_name']: item['status'] for item in old_att.data}
        
        results = []
        for s in students.data:
            prev_status = old_map.get(s['student_name'], "حاضر")
            default_idx = ["حاضر", "غائب", "متأخر"].index(prev_status)
            
            stat = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=default_idx, key=f"s_{s['id']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
            
        if st.button("💾 حفظ الرصد نهائياً"):
            supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
            supabase.table('attendance').insert(results).execute()
            st.success("✅ تم حفظ رصد اللجنة بنجاح"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- ⚙️ 3. لوحة الإدارة والتقارير ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز دخول المسؤول:", type="password") == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ تسجيل الخروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير الموحدة", "🏘️ متابعة اللجان", "💾 إدارة البيانات"])
    
    with tab1:
        report_date = st.date_input("🗓️ اختر التاريخ:", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(report_date)).execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            df_abs = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            
            col_act1, col_act2 = st.columns([3, 1])
            with col_act2:
                if st.button(f"🗑️ حذف سجلات {report_date}", type="secondary"):
                    supabase.table('attendance').delete().eq('date', str(report_date)).execute()
                    st.warning("تم حذف سجلات اليوم المختار"); st.rerun()

            if not df_abs.empty:
                # عرض الشعبة في الجدول
                classes = []
                for name in df_abs['student_name']:
                    try:
                        s_info = supabase.table('students').select("class_name").eq("student_name", name).execute()
                        classes.append(s_info.data[0]['class_name'] if s_info.data else "---")
                    except: classes.append("---")
                df_abs['الشعبة'] = classes
                df_abs['committee_num'] = pd.to_numeric(df_abs['committee'], errors='coerce')
                df_abs = df_abs.sort_values(by='committee_num')
                
                st.table(df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee':'اللجنة','student_name':'الطالب','status':'الحالة','teacher_name':'المعلم'}))
                
                # رسالة الواتساب بدون شعبة وبمسافات
                msg = f"🗓️ *تقرير مدرسة القطيف التقني*%0A📅 *التاريخ:* {report_date}%0A---------------------------------------%0A"
                for _, r in df_abs.iterrows():
                    msg += f"📦 *لجنة:* {r['committee']}%0A👤 *الاسم:* {r['student_name']} ({r['status']})%0A%0A"
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="whatsapp-btn">إرسال عبر واتساب 📲</a>', unsafe_allow_html=True)
            else: st.success("لا يوجد غياب أو تأخر مسجل لهذا اليوم")
        else: st.info("لا توجد بيانات لهذا التاريخ")

    with tab3:
        if st.text_input("كلمة مرور إدارة البيانات:", type="password") == "4321":
            col_a, col_b = st.columns(2)
            with col_a:
                std_data = supabase.table('students').select("*").execute()
                if std_data.data:
                    df_std = pd.DataFrame(std_data.data)
                    st.download_button("📥 نسخة احتياطية CSV", data=df_std.to_csv(index=False).encode('utf-8-sig'), file_name="backup.csv")
            with col_b:
                up = st.file_uploader("استعادة من ملف CSV/XLSX:")
                if up and st.button("🚀 استعادة الآن"):
                    df_new = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                    supabase.table('students').delete().neq('student_name', 'none').execute()
                    recs = df_new.to_dict('records')
                    for r in recs: r.pop('id', None)
                    supabase.table('students').insert(recs).execute()
                    st.success("تم استيراد البيانات بنجاح")
