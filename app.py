import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse
import os
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import io

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. تنسيق الواجهة
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    
    button[kind="primary"] {
        background-color: #ADD8E6 !important;
        color: #000 !important;
        border: 2px solid #ADD8E6 !important;
        font-weight: bold;
    }
    button[kind="secondary"] {
        background-color: #FFA500 !important;
        color: #fff !important;
        border: 2px solid #FFA500 !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. الدوال المساعدة
def smart_sort(x):
    try: return int(x)
    except: return str(x)

def fix_arabic(text):
    try:
        reshaped = reshape(str(text))
        return get_display(reshaped)
    except: return str(text)

def create_pdf(df, report_date):
    pdf = FPDF()
    pdf.add_page()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, "arial.ttf")
    has_font = False
    if os.path.exists(font_path):
        try:
            pdf.add_font("ArabicFont", "", font_path)
            pdf.set_font("ArabicFont", size=12)
            has_font = True
        except: has_font = False
    
    if has_font:
        pdf.set_font("ArabicFont", size=16)
        pdf.cell(200, 10, txt=fix_arabic(f"تقرير الغياب ليوم {report_date}"), ln=True, align='C')
        pdf.ln(10)
        pdf.cell(30, 10, fix_arabic("الحالة"), 1, align='C')
        pdf.cell(30, 10, fix_arabic("الشعبة"), 1, align='C')
        pdf.cell(130, 10, fix_arabic("الاسم"), 1, align='C')
        pdf.ln()
        for _, row in df.iterrows():
            pdf.cell(30, 10, fix_arabic(row['الحالة']), 1, align='C')
            pdf.cell(30, 10, fix_arabic(row['الشعبة']), 1, align='C')
            pdf.cell(130, 10, fix_arabic(row['الاسم']), 1, align='R')
            pdf.ln()
    else:
        pdf.set_font("Arial", size=14)
        pdf.cell(200, 10, txt=f"Attendance Report - {report_date}", ln=True, align='C')
    return pdf.output()

# 4. التنقل بين الصفحات
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# الصفحة الرئيسية
if st.session_state.page == "home":
    st.write("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center; border: 2px solid #1f77b4; padding: 30px; border-radius: 15px; background-color: #f8f9fa;">
            <h1 style="color: #1f77b4;">برنامج تحضير الغياب الرقمي</h1>
            <h2>مدرسة القطيف الثانوية</h2>
            <hr style="width: 40%; margin: auto;">
            <p style="margin-top:10px;">إشراف: <b>أ. عارف أحمد الحداد</b></p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 تحضير الطلاب اليومي", use_container_width=True, type="primary"):
            st.session_state.page = "attendance"; st.rerun()
    with col2:
        if st.button("⚙️ لوحة تحكم الإدارة", use_container_width=True, type="secondary"):
            st.session_state.page = "admin"; st.rerun()

# صفحة التحضير
elif st.session_state.page == "attendance":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if not st.session_state.logged_in:
        nid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
        if st.button("تسجيل الدخول"):
            res = supabase.table("teachers").select("*").eq("national_id", nid.strip()).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                st.rerun()
            else: st.error("عذراً، السجل غير مسجل.")
    else:
        st.info(f"المعلم المسؤول: {st.session_state.teacher_name}")
        t_date = st.date_input("تاريخ اليوم", datetime.now())
        s_data = supabase.table('students').select("committee").execute()
        coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=smart_sort)
        sel_c = st.selectbox("اختر اللجنة المراد تحضيرها:", ["---"] + coms)
        
        if sel_c != "---":
            students = supabase.table('students').select("*").eq('committee', sel_c).execute()
            results = []
            for s in students.data:
                c1, c2 = st.columns([2, 1])
                c1.write(f"👤 {s['student_name']}")
                stat = c2.radio("الحالة", ["حاضر", "غائب", "متأخر"], key=f"st_{s['id']}", horizontal=True)
                results.append({"student_name": s['student_name'], "committee": sel_c, "status": stat, "date": str(t_date), "teacher_name": st.session_state.teacher_name})
            
            if st.button("💾 اعتماد وحفظ الكشف"):
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(t_date)).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("✅ تم حفظ البيانات بنجاح!"); time.sleep(1)
                st.session_state.page = "home"; st.session_state.logged_in = False; st.rerun()

# صفحة الإدارة
elif st.session_state.page == "admin":
    if st.button("⬅️ عودة للمؤشر الرئيسي"): st.session_state.page = "home"; st.rerun()
    pw = st.text_input("كلمة مرور الإدارة:", type="password")
    if pw == "1234":
        tab1, tab2, tab3 = st.tabs(["📊 التقارير والواتساب", "🗂️ إدارة بيانات الطلاب", "🧹 إدارة سجلات الغياب"])
        
        with tab1:
            st.subheader("إصدار التقارير اليومية")
            rep_date = st.date_input("اختر التاريخ", datetime.now(), key="rep_date")
            att = supabase.table('attendance').select("*").eq('date', str(rep_date)).execute()
            
            if att.data:
                df_att = pd.DataFrame(att.data)
                std = supabase.table('students').select("student_name, section, committee").execute()
                df_s = pd.DataFrame(std.data)
                final = pd.merge(df_att, df_s, on='student_name', how='left')
                final = final[final['status'].isin(['غائب', 'متأخر'])]
                
                display_df = final[['student_name', 'section', 'committee_y', 'status']]
                display_df.columns = ['الاسم', 'الشعبة', 'اللجنة', 'الحالة']
                st.table(display_df)
                
                msg = f"*تقرير غياب مدرسة القطيف الثانوية*\n*التاريخ:* {rep_date}\n"
                for _, r in display_df.iterrows():
                    msg += f"--------------------------\n👤 *الاسم:* {r['الاسم']}\n🏫 *الشعبة:* {r['الشعبة']}\n📦 *اللجنة:* {r['اللجنة']}\n📍 *الحالة:* {r['الحالة']}\n"
                
                encoded_msg = urllib.parse.quote(msg)
                st.markdown(f'<a href="https://wa.me/?text={encoded_msg}" target="_blank"><div style="background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; cursor: pointer;">📱 إرسال التقرير عبر الواتساب</div></a>', unsafe_allow_html=True)
            else: st.warning("لا توجد سجلات لهذا التاريخ.")

        with tab2:
            st.subheader("إدارة قاعدة بيانات الطلاب")
            
            # --- ميزة النسخة الاحتياطية ---
            st.info("💾 النسخ الاحتياطي والاستعادة")
            col_bk1, col_bk2 = st.columns(2)
            
            with col_bk1:
                if st.button("📥 إنشاء نسخة احتياطية (Excel)"):
                    all_students = supabase.table('students').select("student_name, section, committee").execute()
                    if all_students.data:
                        df_backup = pd.DataFrame(all_students.data)
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df_backup.to_excel(writer, index=False, sheet_name='Students')
                        st.download_button(
                            label="⬇️ تحميل النسخة الاحتياطية",
                            data=output.getvalue(),
                            file_name=f"backup_students_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            
            with col_bk2:
                restore_file = st.file_uploader("📂 اختيار ملف لاسترجاع النسخة", type=['xlsx'], key="restore")
                if restore_file:
                    if st.button("🔄 تأكيد استرجاع البيانات"):
                        df_restore = pd.read_excel(restore_file)
                        supabase.table('students').delete().neq('id', 0).execute() # مسح القديم
                        supabase.table('students').insert(df_restore.to_dict(orient='records')).execute()
                        st.success("تم استرجاع النسخة الاحتياطية بنجاح.")

            st.divider()
            
            if st.button("🗑️ حذف جميع أسماء الطلاب من النظام", type="secondary"):
                supabase.table('students').delete().neq('id', 0).execute()
                st.success("تم حذف جميع الأسماء بنجاح.")
            
            st.divider()
            
            st.subheader("📤 رفع بيانات الطلاب (ملف جديد)")
            up_file = st.file_uploader("اختر ملف Excel", type=['xlsx'], key="file_up")
            if up_file:
                df_up = pd.read_excel(up_file)
                if st.button("✅ تأكيد الرفع"):
                    supabase.table('students').insert(df_up.to_dict(orient='records')).execute()
                    st.success("تم الرفع بنجاح.")
            
            st.divider()
            
            st.subheader("🔍 تعديل بيانات طالب")
            s_name = st.text_input("ابحث عن اسم الطالب:")
            if s_name:
                search_res = supabase.table('students').select("*").ilike('student_name', f'%{s_name}%').execute()
                if search_res.data:
                    selected_st = st.selectbox("اختر الطالب:", [s['student_name'] for s in search_res.data])
                    st_data = [s for s in search_res.data if s['student_name'] == selected_st][0]
                    with st.form("edit_form"):
                        n_name = st.text_input("الاسم:", value=st_data['student_name'])
                        n_sec = st.text_input("الشعبة:", value=st_data['section'])
                        n_com = st.text_input("اللجنة:", value=st_data['committee'])
                        if st.form_submit_button("حفظ التغييرات"):
                            supabase.table('students').update({"student_name": n_name, "section": n_sec, "committee": n_com}).eq('id', st_data['id']).execute()
                            st.success("تم التحديث.")

        with tab3:
            st.subheader("تنظيف سجلات الغياب")
            del_date = st.date_input("اختر التاريخ المراد حذف سجلاته:", datetime.now(), key="del_date")
            if st.button("❌ حذف غياب هذا اليوم نهائياً"):
                supabase.table('attendance').delete().eq('date', str(del_date)).execute()
                st.success(f"تم حذف سجلات {del_date}")
