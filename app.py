import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# بيانات الاتصال
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

def smart_sort(x):
    try: return int(x)
    except: return str(x)

st.set_page_config(page_title="نظام غياب الطلاب - أ. عارف الحداد", layout="wide")

# دالة توليد التقرير التفصيلي (الاسم، اللجنة، الشعبة)
def show_detailed_report(df, report_date):
    html_table = df.to_html(index=False, classes='report-table')
    report_html = f"""
    <div dir="rtl" style="font-family: 'Arial'; padding: 30px; border: 4px solid #2c3e50; background: white;">
        <div style="text-align: center;">
            <h2 style="margin-bottom: 5px;">كشف غياب الطلاب التفصيلي</h2>
            <h4 style="color: #555;">تاريخ الرصد: {report_date}</h4>
        </div>
        <style>
            .report-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .report-table th {{ background-color: #f2f2f2; padding: 12px; border: 1px solid #333; }}
            .report-table td {{ padding: 10px; border: 1px solid #333; text-align: center; }}
        </style>
        {html_table}
        <div style="margin-top: 30px; text-align: left;">
            <p>يعتمد مدير المدرسة: ........................</p>
        </div>
    </div>
    """
    st.markdown(report_html, unsafe_allow_html=True)

def get_system_status():
    try:
        res = supabase.table("settings").select("is_open").eq("setting_name", "attendance_status").execute()
        return res.data[0]['is_open'] if res.data else True
    except: return True

st.sidebar.title("🏫 القائمة الرئيسية")
page = st.sidebar.radio("انتقل إلى:", ["🔑 دخول المعلم", "📊 لوحة الإدارة"])

# --- واجهة المعلم ---
if page == "🔑 دخول المعلم":
    if not get_system_status():
        st.error("🚫 النظام مغلق حالياً.")
    else:
        # كود الرصد المعتاد...
        st.info("الرجاء تسجيل الدخول للبدء بالرصد.")

# --- لوحة الإدارة ---
elif page == "📊 لوحة الإدارة":
    st.header("📊 لوحة الإدارة والتقارير")
    if st.sidebar.text_input("كلمة المرور", type="password") == "1234":
        
        # أزرار الحالة (أخضر/أحمر)
        status = get_system_status()
        if status:
            st.success("🟢 النظام الآن: مفتوح")
            if st.button("🔴 إيقاف الرصد"):
                supabase.table("settings").update({"is_open": False}).eq("setting_name", "attendance_status").execute()
                st.rerun()
        else:
            st.error("🔴 النظام الآن: مغلق")
            if st.button("🟢 تفعيل الرصد"):
                supabase.table("settings").update({"is_open": True}).eq("setting_name", "attendance_status").execute()
                st.rerun()

        st.divider()
        report_date = st.date_input("📅 اختر تاريخ التقرير", datetime.now())
        
        # جلب البيانات مع دمج معلومات "الشعبة" من جدول الطلاب
        att_res = supabase.table('attendance').select("student_name, status, committee, date").eq('date', str(report_date)).execute()
        std_res = supabase.table('students').select("student_name, section").execute() # نفترض وجود عمود section للشعبة
        
        if att_res.data:
            att_df = pd.DataFrame(att_res.data)
            std_df = pd.DataFrame(std_res.data)
            
            # دمج الجداول للحصول على الشعبة
            merged_df = pd.merge(att_df, std_df, on='student_name', how='left')
            
            # تصفية الغائبين والمتأخرين فقط
            final_df = merged_df[merged_df['status'].isin(['غائب', 'متأخر'])]
            display_df = final_df[['student_name', 'committee', 'section', 'status']]
            display_df.columns = ['اسم الطالب', 'اللجنة', 'الشعبة', 'الحالة']

            # أزرار الإرسال الجديدة
            col_send1, col_send2 = st.columns(2)
            
            with col_send1:
                if st.button("📤 إرسال التقرير بالتفصيل"):
                    st.balloons()
                    show_detailed_report(display_df, report_date)
                    st.info("💡 جاهز للطباعة: اضغط (Ctrl + P) لحفظ التقرير كـ PDF.")

            with col_send2:
                # رابط واتساب للملخص السريع
                summary_msg = f"تقرير غياب يوم {report_date}: تم رصد {len(display_df)} حالات."
                wa_url = f"https://wa.me/?text={urllib.parse.quote(summary_msg)}"
                st.link_button("📱 ملخص سريع عبر واتساب", wa_url)

            st.table(display_df)
        else:
            st.info("لا توجد سجلات لهذا التاريخ.")
    else: st.sidebar.warning("كلمة المرور مطلوبة.")
