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

# 2. تنسيق الواجهة والستايل العام
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    
    /* تنسيق الأزرار لتناسب الجوال */
    button[kind="primary"] {
        background-color: #ADD8E6 !important;
        color: #000 !important;
        border: 2px solid #ADD8E6 !important;
        font-weight: bold;
        height: 55px;
        font-size: 18px !important;
    }
    button[kind="secondary"] {
        background-color: #FFA500 !important;
        color: #fff !important;
        border: 2px solid #FFA500 !important;
        font-weight: bold;
        height: 55px;
        font-size: 18px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. الدوال المساعدة
def smart_sort(x):
    try: return int(x)
    except: return str(x)

# 4. إدارة التنقل بين الصفحات
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- الصفحة الرئيسية (الغلاف المنسق للجوال) ---
if st.session_state.page == "home":
    st.write("<br>", unsafe_allow_html=True)
    
    # تم التأكد من إضافة unsafe_allow_html=True هنا ليظهر التنسيق
    st.markdown("""
        <div style="text-align: center; border: 2px solid #1f77b4; padding: 25px; border-radius: 15px; background-color: #f8f9fa; margin-bottom: 20px;">
            <h1 style="color: #1f77b4; font-size: 28px; margin-bottom: 5px; font-weight: bold;">برنامج التحضير الرقمي</h1>
            <h2 style="color: #333; font-size: 22px; margin-top: 5px;">مدرسة القطيف الثانوية</h2>
            <hr style="width: 70%; margin: 15px auto; border: 1px solid #1f77b4;">
            
            <div style="margin-bottom: 20px;">
                <p style="font-size: 16px; margin-bottom: 2px; color: #666;">فكرة وتنفيذ</p>
                <b style="font-size: 20px; color: #1f77b4;">أ. عارف أحمد الحداد</b>
            </div>
            
            <div style="margin-bottom: 5px;">
                <p style="font-size: 16px; margin-bottom: 2px; color: #666;">مدير المدرسة</p>
                <b style="font-size: 20px; color: #1f77b4;">أ. فراس عبدالله آل عبدالمحسن</b>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)
    
    # أزرار تحضير الطلاب ولوحة التحكم
    if st.button("📝 تحضير الطلاب اليومي", use_container_width=True, type="primary"):
        st.session_state.page = "attendance"; st.rerun()
    
    st.write("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    if st.button("⚙️ لوحة تحكم الإدارة", use_container_width=True, type="secondary"):
        st.session_state.page = "admin"; st.rerun()

# --- صفحة التحضير ---
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

# --- صفحة الإدارة ---
elif st.session_state.page == "admin":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
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
                
                if 'student_name' in df_att.columns and 'student_name' in df_s.columns:
                    final = pd.merge(df_att, df_s, on='student_name', how='left')
                    final = final[final['status'].isin(['غائب', 'متأخر'])]
                    
                    display_df = final[['student_name', 'section', 'committee_y', 'status']]
                    display_df.columns = ['الاسم', 'الشعبة', 'اللجنة', 'الحالة']
                    st.table(display_df)
                    
                    msg = f"*تقرير غياب مدرسة القطيف الثانوية*\n*التاريخ:* {rep_date}\n"
                    for _, r in display_df.iterrows():
                        msg += f"--------------------------\n👤 *الاسم:* {r['الاسم']}\n🏫 *الشعبة:* {r['الشعبة']}\n📦 *اللجنة:* {r['اللجنة']}\n📍 *الحالة:* {r['الحالة']}\n"
                    
                    encoded_msg = urllib.parse.quote(msg)
                    st.markdown(f'<a href="https://wa.me/?text={encoded_msg}" target="_blank"><div style="background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; cursor: pointer;">📱 إرسال عبر الواتساب</div></a>', unsafe_allow_html=True)

        with tab2:
            st.subheader("إدارة قاعدة بيانات الطلاب")
            st.info("💾 النسخ الاحتياطي والاستعادة")
            col_bk1, col_bk2 = st.columns(2)
            
            with col_bk1:
                if st.button("📥 إنشاء نسخة احتياطية (Excel)"):
                    try:
                        all_students = supabase.table('students').select("student_name, section, committee").execute()
                        if all_students.data:
                            df_backup = pd.DataFrame(all_students.data)
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                df_backup.to_excel(writer, index=False, sheet_name='Students')
                            st.download_button(label="⬇️ تحميل النسخة الجاهزة", data=output.getvalue(), file_name=f"backup_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    except Exception as e: st.error(f"خطأ: {e}")
            
            with col_bk2:
                restore_file = st.file_uploader("📂 استرجاع النسخة", type=['xlsx'])
                if restore_file and st.button("🔄 تأكيد الاسترجاع"):
                    try:
                        df_restore = pd.read_excel(restore_file)
                        mapping = {'الاسم': 'student_name', 'اسم الطالب': 'student_name', 'الشعبة': 'section', 'اللجنة': 'committee'}
                        df_restore.rename(columns=mapping, inplace=True)
                        required = ['student_name', 'section', 'committee']
                        if all(col in df_restore.columns for col in required):
                            supabase.table('students').delete().neq('id', 0).execute() 
                            supabase.table('students').insert(df_restore[required].to_dict(orient='records')).execute()
                            st.success("تم استرجاع البيانات بنجاح.")
                    except Exception as e: st.error(f"خطأ: {e}")

        with tab3:
            st.subheader("حذف السجلات")
            del_date = st.date_input("تاريخ الحذف", datetime.now())
            if st.button("❌ حذف غياب اليوم"):
                supabase.table('attendance').delete().eq('date', str(del_date)).execute()
                st.success("تم الحذف.")
