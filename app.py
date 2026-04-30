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
st.set_page_config(page_title="نظام مدرسة القطيف - النسخة الشاملة", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; direction: rtl; }
    .main-title { font-size: 32px; font-weight: 800; color: #1a237e; text-align: center; margin-bottom: 20px; }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 18px; border-radius: 15px; text-align: center; text-decoration: none; display: block; font-weight: bold; margin: 20px auto; max-width: 600px; font-size: 20px; border: 1px solid #128C7E; }
    div.stButton > button { width: 100%; border-radius: 12px; font-weight: bold; height: 55px; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- 🏠 1. الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('<p class="main-title">التحضير التقني لمدرسة القطيف الثانوية</p>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; font-size:18px;">مدير المدرسة: أ. فراس آل عبدالمحسن | إشراف: أ. عارف الحداد</p><hr>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📝 دخول المعلمين للرصد", type="primary"): st.session_state.page = "att_login"; st.rerun()
        if st.button("⚙️ لوحة الإدارة والتقارير"): st.session_state.page = "admin_login"; st.rerun()

# --- 📝 2. نظام الرصد ---
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    t_id = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل غير موجود")

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

# --- ⚙️ 3. لوحة الإدارة (النسخة الكاملة) ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز دخول المسؤول:", type="password") == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ تسجيل الخروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير", "🏘️ متابعة اللجان", "💾 النسخ الاحتياطي والاستعادة"])
    today_date = str(datetime.now().date())

    with tab1:
        d = st.date_input("تاريخ التقرير", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df_abs = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            if not df_abs.empty:
                df_abs['committee_num'] = pd.to_numeric(df_abs['committee'], errors='coerce')
                df_abs = df_abs.sort_values(by='committee_num')
                classes = []
                for n in df_abs['student_name']:
                    try:
                        si = supabase.table('students').select("class_name").eq("student_name", n).execute()
                        classes.append(si.data[0]['class_name'] if si.data else "---")
                    except: classes.append("---")
                df_abs['الشعبة'] = classes
                st.table(df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']])
                msg = f"🗓️ *تقرير مدرسة القطيف*%0A📅 *التاريخ:* {d}%0A"
                for _, r in df_abs.iterrows():
                    msg += f"📦 *لجنة:* {r['committee']} | 🏫 *شعبة:* {r['الشعبة']}%0A👤 *الاسم:* {r['student_name']} ({r['status']})%0A"
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="whatsapp-btn">إرسال عبر واتساب 📲</a>', unsafe_allow_html=True)
            else: st.success("لا يوجد غياب")

    with tab2:
        st.subheader(f"🏘️ حالة اللجان اليوم: {today_date}")
        all_s = supabase.table('students').select("committee").execute()
        total_coms = sorted(list(set([str(i['committee']) for i in all_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        done_res = supabase.table('attendance').select("committee, teacher_name").eq("date", today_date).execute()
        done_coms = {str(i['committee']): i['teacher_name'] for i in done_res.data}
        col1, col2 = st.columns(2)
        with col1:
            st.success("✅ رصدت")
            for c in total_coms:
                if c in done_coms: st.write(f"📍 لجنة {c} ({done_coms[c]})")
        with col2:
            st.error("❌ لم ترصد")
            for c in total_coms:
                if c not in done_coms: st.write(f"⚠️ لجنة {c}")

    with tab3:
        st.subheader("💾 إدارة النسخ الاحتياطية")
        
        # --- 1. التصدير (تحميل) ---
        st.markdown("### 1. تحميل نسخة احتياطية (تصدير)")
        std_res = supabase.table('students').select("*").execute()
        if std_res.data:
            df_backup = pd.DataFrame(std_res.data)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.download_button("📥 تحميل بصيغة CSV", data=df_backup.to_csv(index=False).encode('utf-8-sig'), file_name=f"students_{today_date}.csv", mime="text/csv")
            with col_b2:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_backup.to_excel(writer, index=False, sheet_name='Students')
                st.download_button("📥 تحميل بصيغة Excel (XLSX)", data=output.getvalue(), file_name=f"students_{today_date}.xlsx")

        st.divider()

        # --- 2. الاستعادة (رفع إما CSV أو XLSX) ---
        st.markdown("### 2. إرجاع نسخة احتياطية (استعادة)")
        st.warning("⚠️ تنبيه: الاستعادة ستحذف بيانات الطلاب الحالية وتستبدلها بالملف المرفوع.")
        uploaded_file = st.file_uploader("اختر ملف النسخة الاحتياطية (CSV أو XLSX):", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                # قراءة الملف بناءً على صيغته
                if uploaded_file.name.endswith('.csv'):
                    new_data = pd.read_csv(uploaded_file)
                else:
                    new_data = pd.read_excel(uploaded_file)
                
                st.write("معاينة البيانات المراد استعادتها:")
                st.dataframe(new_data.head())
                
                if st.button("🚀 تنفيذ استعادة النسخة الآن"):
                    with st.spinner("جاري استبدال البيانات..."):
                        # حذف البيانات القديمة
                        supabase.table('students').delete().neq('student_name', 'none').execute()
                        
                        # تجهيز البيانات الجديدة للرفع
                        records = new_data.to_dict('records')
                        # إزالة عمود 'id' إن وجد لتجنب تكرار المفاتيح الأساسية
                        for r in records: r.pop('id', None)
                        
                        # رفع البيانات
                        supabase.table('students').insert(records).execute()
                        st.success("✅ تمت استعادة النسخة بنجاح!")
                        time.sleep(2)
                        st.rerun()
            except Exception as e:
                st.error(f"خطأ في معالجة الملف: {e}")
