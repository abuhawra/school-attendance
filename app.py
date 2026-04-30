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
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; direction: rtl; }
    .main-title { font-size: 32px; font-weight: 800; color: #1a237e; text-align: center; margin-bottom: 20px; }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 18px; border-radius: 15px; text-align: center; text-decoration: none; display: block; font-weight: bold; margin: 20px auto; max-width: 600px; font-size: 20px; border: 1px solid #128C7E; }
    div.stButton > button { width: 100%; border-radius: 12px; font-weight: bold; height: 50px; }
    .delete-section { background-color: #fff1f1; padding: 20px; border-radius: 15px; border: 1px solid #ffcccc; margin-top: 20px; }
    table { direction: rtl; text-align: right; }
    th { background-color: #1a237e !important; color: white !important; text-align: center !important; }
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

# --- 📝 2. نظام الرصد (المعلمين) ---
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    t_id = st.text_input("رقم السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل غير مسجل")

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

# --- ⚙️ 3. لوحة الإدارة (التقارير، المتابعة، البيانات) ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز دخول المسؤول:", type="password") == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ تسجيل الخروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير الموحدة", "🏘️ متابعة اللجان", "💾 إدارة بيانات الطلاب"])
    today_date = str(datetime.now().date())

    with tab1:
        d = st.date_input("اختر تاريخ التقرير", datetime.now())
        date_str = str(d)
        res = supabase.table("attendance").select("*").eq("date", date_str).execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            df_abs = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            
            if not df_abs.empty:
                df_abs['committee_num'] = pd.to_numeric(df_abs['committee'], errors='coerce')
                df_abs = df_abs.sort_values(by='committee_num')
                
                # جلب الشعبة لكل طالب غائب
                classes = []
                for n in df_abs['student_name']:
                    try:
                        si = supabase.table('students').select("class_name").eq("student_name", n).execute()
                        classes.append(si.data[0]['class_name'] if si.data else "---")
                    except: classes.append("---")
                df_abs['الشعبة'] = classes
                
                # إعداد الجدول النهائي بأسماء رؤوس عربية
                final_df = df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].copy()
                final_df.columns = ['رقم اللجنة', 'اسم الطالب', 'الشعبة', 'حالة الحضور', 'المعلم الراصد']
                
                st.subheader(f"📋 كشف الغياب ليوم {date_str}")
                st.table(final_df)
                
                # بناء رسالة واتساب
                msg = f"🗓️ *تقرير مدرسة القطيف التقني*%0A📅 *التاريخ:* {date_str}%0A---------------------------------------%0A"
                for _, r in df_abs.iterrows():
                    msg += f"📦 *لجنة:* {r['committee']} | 🏫 *شعبة:* {r['الشعبة']}%0A👤 *الاسم:* {r['student_name']} ({r['status']})%0A--------------------%0A"
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="whatsapp-btn">إرسال التقرير عبر واتساب 📲</a>', unsafe_allow_html=True)
            else:
                st.info("لا توجد حالات غياب أو تأخر مرصودة لهذا التاريخ.")

            # ميزة حذف التقرير لهذا التاريخ
            st.markdown('<div class="delete-section">', unsafe_allow_html=True)
            st.warning(f"⚠️ حذف كافة سجلات الرصد ليوم {date_str}")
            if st.button(f"🗑️ حذف تقرير {date_str}"):
                st.session_state.confirm_report_del = True
            
            if st.session_state.get('confirm_report_del'):
                st.error("هل أنت متأكد؟ سيتم مسح بيانات التحضير لهذا اليوم فقط.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("تأكيد الحذف"):
                        supabase.table('attendance').delete().eq('date', date_str).execute()
                        st.success("تم الحذف!"); st.session_state.confirm_report_del = False; time.sleep(1); st.rerun()
                with c2:
                    if st.button("إلغاء"): st.session_state.confirm_report_del = False; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else: st.write("لا توجد بيانات لهذا التاريخ.")

    with tab2:
        st.subheader(f"🏘️ حالة اللجان اليوم: {today_date}")
        all_s = supabase.table('students').select("committee").execute()
        total_coms = sorted(list(set([str(i['committee']) for i in all_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        done_res = supabase.table('attendance').select("committee, teacher_name").eq("date", today_date).execute()
        done_coms = {str(i['committee']): i['teacher_name'] for i in done_res.data}
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.success("✅ لجان تم رصدها")
            for c in total_coms:
                if c in done_coms: st.write(f"📍 لجنة {c} ({done_coms[c]})")
        with col_c2:
            st.error("❌ لجان لم ترصد بعد")
            for c in total_coms:
                if c not in done_coms: st.write(f"⚠️ لجنة {c}")

    with tab3:
        st.subheader("⚙️ إدارة النسخ الاحتياطية")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown("### 📥 تصدير البيانات")
            std_res = supabase.table('students').select("*").execute()
            if std_res.data:
                df_b = pd.DataFrame(std_res.data)
                st.download_button("تحميل CSV", data=df_b.to_csv(index=False).encode('utf-8-sig'), file_name=f"students_{today_date}.csv")
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                    df_b.to_excel(writer, index=False)
                st.download_button("تحميل Excel (XLSX)", data=out.getvalue(), file_name=f"students_{today_date}.xlsx")

        with col_b2:
            st.markdown("### 🗑️ مسح الجدول")
            if st.button("❌ حذف كافة الطلاب"):
                st.session_state.confirm_std_del = True
            if st.session_state.get('confirm_std_del'):
                if st.button("تأكيد الحذف النهائي"):
                    supabase.table('students').delete().neq('student_name', 'none').execute()
                    st.success("تم المسح"); st.session_state.confirm_std_del = False; st.rerun()

        st.divider()
        st.markdown("### 🔄 استعادة (إرجاع نسخة)")
        up = st.file_uploader("ارفع ملف (CSV أو XLSX):", type=["csv", "xlsx"])
        if up:
            df_new = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
            if st.button("🚀 استعادة الآن"):
                supabase.table('students').delete().neq('student_name', 'none').execute()
                recs = df_new.to_dict('records')
                for r in recs: r.pop('id', None)
                supabase.table('students').insert(recs).execute()
                st.success("تمت الاستعادة بنجاح!"); time.sleep(1); st.rerun()
