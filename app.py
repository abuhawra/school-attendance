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

# دالة الترتيب الذكي لتجنب خطأ NameError
def smart_sort(x):
    try: return int(x)
    except: return str(x)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'teacher_name' not in st.session_state:
    st.session_state.teacher_name = ""

st.set_page_config(page_title="نظام غياب الطلاب - أ. عارف الحداد", layout="wide")

# جلب حالة النظام
def get_system_status():
    try:
        res = supabase.table("settings").select("is_open").eq("setting_name", "attendance_status").execute()
        return res.data[0]['is_open'] if res.data else True
    except: return True

st.sidebar.title("🏫 القائمة الرئيسية")
page = st.sidebar.radio("انتقل إلى:", ["🔑 دخول المعلم", "📊 لوحة الإدارة"])

# --- 1. واجهة المعلم ---
if page == "🔑 دخول المعلم":
    is_open = get_system_status()
    if not is_open:
        st.error("🚫 نظام رصد الغياب مغلق حالياً من قبل الإدارة.")
    else:
        if not st.session_state.logged_in:
            st.header("🔑 تسجيل دخول المعلم")
            nid_input = st.text_input("أدخل رقم السجل المدني:", key="login_field")
            if st.button("دخول"):
                res = supabase.table("teachers").select("*").eq("national_id", nid_input.strip()).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                    st.rerun()
                else: st.error("❌ السجل المدني غير مسجل.")
        else:
            # واجهة الرصد بعد الدخول
            st.success(f"✅ مرحباً أستاذ: **{st.session_state.teacher_name}**")
            
            if st.button("🔄 خروج / تبديل المعلم"):
                st.session_state.logged_in = False
                st.rerun()

            st.divider()
            target_date = st.date_input("📅 تاريخ الرصد", datetime.now())
            
            # جلب اللجان من قاعدة البيانات
            s_data = supabase.table('students').select("committee").execute()
            all_committees = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=smart_sort)
            
            selected_committee = st.selectbox("🎯 اختر اللجنة للبدء بالرصد:", ["--- اختر اللجنة ---"] + all_committees)
            
            if selected_committee != "--- اختر اللجنة ---":
                # عرض الطلاب للرصد
                students_query = supabase.table('students').select("*").eq('committee', selected_committee).execute()
                
                # جلب أي رصد سابق لنفس اليوم لتعديله
                old_att = supabase.table('attendance').select("student_name, status").eq('committee', selected_committee).eq('date', str(target_date)).execute()
                history = {row['student_name']: row['status'] for row in old_att.data}
                
                attendance_results = []
                st.subheader(f"📋 كشف لجنة رقم: {selected_committee}")
                
                for student in students_query.data:
                    s_name = student['student_name']
                    prev_status = history.get(s_name, "حاضر")
                    
                    col_name, col_status = st.columns([2, 1])
                    with col_name: st.write(f"👤 {s_name}")
                    with col_status:
                        status = st.radio("الحالة", ["حاضر", "غائب", "متأخر"], 
                                         index=["حاضر", "غائب", "متأخر"].index(prev_status), 
                                         key=f"st_{student['id']}", horizontal=True)
                    
                    attendance_results.append({
                        "student_name": s_name, 
                        "committee": selected_committee, 
                        "status": status, 
                        "date": str(target_date), 
                        "teacher_name": st.session_state.teacher_name
                    })
                
                if st.button("💾 حفظ وإرسال الكشف النهائي"):
                    supabase.table('attendance').delete().eq('committee', selected_committee).eq('date', str(target_date)).execute()
                    supabase.table('attendance').insert(attendance_results).execute()
                    st.balloons()
                    st.success("✅ تم حفظ الغياب بنجاح!")
                    time.sleep(1)
                    st.rerun()

# --- 2. لوحة الإدارة والتقارير ---
elif page == "📊 لوحة الإدارة":
    st.header("📊 لوحة الإدارة والتقارير")
    if st.sidebar.text_input("كلمة المرور", type="password") == "1234":
        
        # التحكم في حالة النظام
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
        report_date = st.date_input("📅 تاريخ التقرير", datetime.now())
        
        # جلب بيانات الغياب ودمجها مع الشعبة
        att_res = supabase.table('attendance').select("*").eq('date', str(report_date)).execute()
        std_res = supabase.table('students').select("student_name, section").execute()
        
        if att_res.data:
            df_att = pd.DataFrame(att_res.data)
            df_std = pd.DataFrame(std_res.data)
            merged = pd.merge(df_att, df_std, on='student_name', how='left')
            
            # تصفية الغائبين والمتأخرين فقط
            report_df = merged[merged['status'].isin(['غائب', 'متأخر'])][['student_name', 'section', 'committee', 'status']]
            report_df.columns = ['اسم الطالب', 'الشعبة', 'اللجنة', 'الحالة']
            
            # أزرار الإرسال والتصدير
            col1, col2 = st.columns(2)
            with col1:
                # واتساب تفصيلي
                msg = f"*تقرير غياب يوم {report_date}*\n"
                for _, r in report_df.iterrows():
                    msg += f"- {r['اسم الطالب']} ({r['الشعبة']}) - لجنة {r['اللجنة']}: *{r['الحالة']}*\n"
                st.link_button("📱 إرسال واتساب تفصيلي", f"https://wa.me/?text={urllib.parse.quote(msg)}")
            
            with col2:
                if st.button("📄 معاينة للطباعة (PDF)"):
                    st.table(report_df)
                    st.info("اضغط Ctrl+P للطباعة كـ PDF.")
            
            st.table(report_df)
        else: st.info("لا توجد سجلات غياب.")
