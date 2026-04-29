import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# 1. بيانات الاتصال (مستخرجة من صورك)
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
# تم استخدام مفتاح anon الظاهر في إعداداتك
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

# إنشاء الاتصال
if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

st.set_page_config(page_title="نظام غياب الطلاب - أ. عارف الحداد", layout="wide")

# القائمة الجانبية
st.sidebar.title("🏫 القائمة الرئيسية")
page = st.sidebar.radio("انتقل إلى:", ["🔑 دخول المعلم", "📊 لوحة الإدارة"])

# --- واجهة دخول المعلم ---
if page == "🔑 دخول المعلم":
    st.header("🔑 تسجيل دخول المعلم")
    
    # حقل إدخال رقم السجل المدني
    nid_input = st.text_input("أدخل رقم السجل المدني الخاص بك:", type="default")
    
    if st.button("دخول"):
        if nid_input:
            try:
                # الإصلاح الجوهري: البحث باستخدام national_id بدلاً من teacher_id
                res = supabase.table("teachers").select("*").eq("national_id", nid_input.strip()).execute()
                
                if res.data:
                    teacher_data = res.data[0]
                    teacher_name = teacher_data.get('name_tech', 'المعلم')
                    st.success(f"✅ مرحباً بك أستاذ: **{teacher_name}**")
                    st.divider()
                    
                    # --- واجهة التحضير ---
                    target_date = st.date_input("📅 تاريخ اليوم", datetime.now())
                    
                    # جلب اللجان المتوفرة
                    s_data = supabase.table('students').select("committee").execute()
                    committees = sorted(list(set([item['committee'] for item in s_data.data if item['committee']])))
                    selected_committee = st.selectbox("🎯 اختر اللجنة المراد تحضيرها", committees)
                    
                    if selected_committee:
                        students_query = supabase.table('students').select("*").eq('committee', selected_committee).execute()
                        
                        if students_query.data:
                            attendance_results = []
                            st.write(f"### قائمة طلاب لجنة: {selected_committee}")
                            
                            for student in students_query.data:
                                col1, col2 = st.columns([2, 1])
                                with col1:
                                    st.write(f"👤 {student['student_name']}")
                                with col2:
                                    status = st.radio("الحالة", ["حاضر", "غائب", "متأخر"], key=f"s_{student['id']}", horizontal=True)
                                
                                attendance_results.append({
                                    "student_name": student['student_name'],
                                    "committee": selected_committee,
                                    "status": status,
                                    "date": str(target_date),
                                    "teacher_name": teacher_name
                                })
                            
                            if st.button("💾 إرسال كشف الغياب"):
                                supabase.table('attendance').insert(attendance_results).execute()
                                st.balloons()
                                st.success("تم تسجيل الغياب بنجاح في قاعدة البيانات.")
                else:
                    st.error("❌ رقم السجل المدني غير موجود. يرجى التأكد من البيانات المرفوعة.")
            except Exception as e:
                st.error(f"⚠️ خطأ في الاتصال: تأكد من تعطيل RLS في Supabase.")
        else:
            st.warning("الرجاء كتابة رقم السجل المدني.")

# --- واجهة الإدارة ---
elif page == "📊 لوحة الإدارة":
    st.header("⚙️ إدارة النظام والتقارير")
    password = st.sidebar.text_input("كلمة مرور الإدارة", type="password")
    if password == "1234":
        st.write("إحصائيات وتقارير الغياب تظهر هنا.")
        # يمكن إضافة جداول التقارير لاحقاً
    else:
        st.info("أدخل كلمة المرور في القائمة الجانبية.")

st.sidebar.divider()
st.sidebar.caption("تصميم وتطوير: أ. عارف أحمد الحداد")
