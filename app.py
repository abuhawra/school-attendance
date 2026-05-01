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

# 2. إعدادات الواجهة الكلاسيكية (CSS)
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; background-color: #f4f7f9; }
    .stApp { background-color: #f4f7f9; }
    
    /* تصميم الواجهة الكلاسيكية */
    .classic-header {
        background-color: #1a237e;
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        border-bottom: 5px solid #ffd700;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .line-1 { font-size: 32px; font-weight: 800; margin-bottom: 5px; color: #ffffff; }
    .line-2 { font-size: 26px; font-weight: 700; margin-bottom: 20px; color: #e0e0e0; }
    .line-3 { font-size: 18px; margin-bottom: 2px; color: #ffd700; }
    .line-4 { font-size: 22px; font-weight: bold; margin-bottom: 15px; }
    .line-5 { font-size: 18px; margin-bottom: 2px; color: #cfd8dc; }
    .line-6 { font-size: 20px; font-weight: bold; }

    /* تنسيق الحقول والأزرار */
    .stTextInput > div > div > input { background-color: white !important; border: 1px solid #1a237e !important; }
    div.stButton > button { border-radius: 10px; font-weight: bold; height: 55px; font-size: 18px !important; }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-align: center; text-decoration: none; display: block; font-weight: bold; margin: 10px auto; max-width: 500px; }
    th { background-color: #1a237e !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- 🏠 1. الصفحة الرئيسية (الواجهة الكلاسيكية المرتبة) ---
if st.session_state.page == "home":
    st.markdown("""
        <div class="classic-header">
            <div class="line-1">التحضير التقني</div>
            <div class="line-2">مدرسة القطيف الثانوية</div>
            <hr style="border: 0.5px solid rgba(255,255,255,0.2); width: 60%;">
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
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    t_id = st.text_input("أدخل رقم السجل المدني للمعلم:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل غير مسجل في النظام")

elif st.session_state.page == "taking_attendance":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher_name} | التاريخ: {today}")
    
    # جلب اللجان المتاحة
    s_data = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
    
    sel_c = st.selectbox("اختر اللجنة المراد رصدها:", ["---"] + coms)
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        
        # جلب التحضير السابق لهذا اليوم لتثبيت الحالة
        old_att = supabase.table('attendance').select("student_name, status").eq('committee', sel_c).eq('date', today).execute()
        old_map = {item['student_name']: item['status'] for item in old_att.data}
        
        results = []
        for s in students.data:
            # التحقق من الحالة السابقة أو وضع "حاضر" كافتراضي
            prev_status = old_map.get(s['student_name'], "حاضر")
            default_idx = ["حاضر", "غائب", "متأخر"].index(prev_status)
            
            stat = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=default_idx, key=f"s_{s['id']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
            
        if st.button("💾 حفظ الرصد نهائياً"):
            supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
            supabase.table('attendance').insert(results).execute()
            st.success("✅ تم حفظ البيانات بنجاح"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- ⚙️ 3. لوحة الإدارة والتقارير (التنقل وحذف اليوم) ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز دخول المسؤول:", type="password") == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ تسجيل الخروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير الموحدة", "🏘️ متابعة حالة اللجان", "💾 إدارة بيانات الطلاب"])
    
    with tab1:
        report_date = st.date_input("اختر تاريخ عرض التقرير", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(report_date)).execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            df_abs = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            
            # زر حذف غياب اليوم المختار
            if st.button(f"🗑️ حذف كافة سجلات يوم {report_date}"):
                supabase.table('attendance').delete().eq('date', str(report_date)).execute()
                st.warning("تم حذف السجلات"); st.rerun()

            if not df_abs.empty:
                # معالجة بيانات العرض
                classes = []
                for name in df_abs['student_name']:
                    try:
                        s_info = supabase.table('students').select("class_name").eq("student_name", name).execute()
                        classes.append(s_info.data[0]['class_name'] if s_info.data else "---")
                    except: classes.append("---")
                df_abs['الشعبة'] = classes
                df_abs['committee_num'] = pd.to_numeric(df_abs['committee'], errors='coerce')
                df_abs = df_abs.sort_values(by='committee_num')
                
                st.subheader(f"📋 كشف الغياب ليوم {report_date}")
                final_view = df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].copy()
                final_view.columns = ['اللجنة', 'الاسم', 'الشعبة', 'الحالة', 'المعلم']
                st.table(final_view)
                
                msg = f"🗓️ *تقرير مدرسة القطيف التقني*%0A📅 *التاريخ:* {report_date}%0A---------------------------------------%0A"
                for _, r in df_abs.iterrows():
                    msg += f"📦 *لجنة:* {r['committee']}%0A👤 *الاسم:* {r['student_name']} ({r['status']})%0A%0A"
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="whatsapp-btn">إرسال عبر واتساب 📲</a>', unsafe_allow_html=True)
            else: st.success("لا يوجد غياب في هذا اليوم")
        else: st.info("لا توجد بيانات لهذا التاريخ")

    with tab3:
        if st.text_input("الرقم السري للإدارة (4321):", type="password") == "4321":
            col_a, col_b = st.columns(2)
            with col_a:
                std_data = supabase.table('students').select("*").execute()
                if std_data.data:
                    df_std = pd.DataFrame(std_data.data)
                    st.download_button("📥 تحميل نسخة CSV", data=df_std.to_csv(index=False).encode('utf-8-sig'), file_name="backup.csv")
            with col_b:
                up = st.file_uploader("رفع نسخة احتياطية (CSV/XLSX):")
                if up and st.button("🚀 استعادة"):
                    df_new = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                    supabase.table('students').delete().neq('student_name', 'none').execute()
                    recs = df_new.to_dict('records')
                    for r in recs: r.pop('id', None)
                    supabase.table('students').insert(recs).execute()
                    st.success("تمت الاستعادة بنجاح")
