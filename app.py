import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# بيانات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# دالة الترتيب الذكي للجان
def smart_sort(x):
    try: return int(x)
    except: return str(x)

st.set_page_config(page_title="نظام غياب الطلاب - أ. عارف الحداد", layout="wide")

# دالة توليد تقرير PDF احترافي
def show_pdf_report(df, report_date):
    html_table = df.to_html(index=False, classes='report-table')
    report_html = f"""
    <div dir="rtl" style="font-family: 'Arial'; padding: 30px; border: 5px double #2c3e50; background: white; border-radius: 10px;">
        <div style="text-align: center;">
            <h1 style="color: #2c3e50; margin-bottom: 5px;">كشف الغياب والتأخر اليومي</h1>
            <h3 style="color: #7f8c8d;">التاريخ: {report_date}</h3>
        </div>
        <hr style="border: 1px solid #eee;">
        <style>
            .report-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 18px; }}
            .report-table th {{ background-color: #34495e; color: white; padding: 15px; border: 1px solid #2c3e50; }}
            .report-table td {{ padding: 12px; border: 1px solid #bdc3c7; text-align: center; }}
            .report-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
        {html_table}
        <div style="margin-top: 40px; display: flex; justify-content: space-between;">
            <p><b>توقيع مراقب الدور:</b> ........................</p>
            <p><b>ختم الإدارة:</b> ........................</p>
        </div>
    </div>
    """
    st.markdown(report_html, unsafe_allow_html=True)

# دالة التحكم في حالة النظام
def get_system_status():
    try:
        res = supabase.table("settings").select("is_open").eq("setting_name", "attendance_status").execute()
        return res.data[0]['is_open'] if res.data else True
    except: return True

st.sidebar.title("🏫 القائمة الرئيسية")
page = st.sidebar.radio("انتقل إلى:", ["🔑 دخول المعلم", "📊 لوحة الإدارة"])

# --- 1. واجهة المعلم ---
if page == "🔑 دخول المعلم":
    if not get_system_status():
        st.error("🚫 نظام رصد الغياب مغلق حالياً.")
    else:
        # (كود الدخول والرصد المعتاد هنا...)
        st.info("قم بتسجيل الدخول لرصد غياب اللجنة.")

# --- 2. لوحة الإدارة ---
elif page == "📊 لوحة الإدارة":
    st.header("📊 لوحة الإدارة والتقارير")
    if st.sidebar.text_input("كلمة المرور", type="password") == "1234":
        
        # التحكم في التشغيل/الإيقاف (أخضر/أحمر)
        current_status = get_system_status()
        if current_status:
            st.success("🟢 النظام الآن: مفتوح لاستقبال الرصد")
            if st.button("🔴 إيقاف رصد الغياب"):
                supabase.table("settings").update({"is_open": False}).eq("setting_name", "attendance_status").execute()
                st.rerun()
        else:
            st.error("🔴 النظام الآن: مغلق")
            if st.button("🟢 تفعيل رصد الغياب"):
                supabase.table("settings").update({"is_open": True}).eq("setting_name", "attendance_status").execute()
                st.rerun()

        st.divider()
        report_date = st.date_input("📅 تاريخ التقرير", datetime.now())
        
        # زر المسح الفوري
        if st.button("⚠️ مسح بيانات هذا اليوم"):
            supabase.table('attendance').delete().eq('date', str(report_date)).execute()
            st.warning("تم المسح. جاري تحديث الصفحة..."); time.sleep(1); st.rerun()

        att_res = supabase.table('attendance').select("*").eq('date', str(report_date)).execute()
        
        if att_res.data:
            df = pd.DataFrame(att_res.data)
            report_df = df[df['status'].isin(['غائب','متأخر'])][['student_name','committee','status','teacher_name']]
            report_df.columns = ['الاسم', 'اللجنة', 'الحالة', 'المعلم']

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📤 إرسال الكشف (فتح نافذة الطباعة)"):
                    st.balloons()
                    show_pdf_report(report_df, report_date)
                    st.info("💡 نصيحة أستاذ عارف: اضغط (Ctrl + P) من جهازك لحفظه كـ PDF فوراً.")
            
            with col2:
                # ميزة إرسال رسالة واتساب سريعة بالإحصائيات
                absent_count = len(report_df[report_df['الحالة'] == 'غائب'])
                late_count = len(report_df[report_df['الحالة'] == 'متأخر'])
                msg = f"تقرير غياب يوم {report_date}: غياب ({absent_count})، تأخر ({late_count}). راجع النظام للمزيد."
                wa_url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                st.link_button("📱 إرسال ملخص عبر واتساب", wa_url)
            
            st.table(report_df)
        else:
            st.info("لا توجد بيانات غياب مسجلة لهذا التاريخ.")
