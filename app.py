import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io

# 1. إعدادات الاتصال بقاعدة البيانات (Supabase)
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. إعدادات الواجهة والتنسيق (CSS)
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .main-header { background-color: #1a237e; color: white; padding: 30px; border-radius: 15px; text-align: center; border-bottom: 5px solid #ffd700; margin-bottom: 20px; }
    .wa-button { color: white !important; padding: 12px; border-radius: 10px; text-align: center; display: block; text-decoration: none; font-weight: bold; margin-top: 10px; font-size: 16px; }
    .wa-all { background-color: #28a745; }
    .wa-absent { background-color: #dc3545; }
    .wa-late { background-color: #fd7e14; }
    th { background-color: #1a237e !important; color: white !important; text-align: center !important; }
    td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown(f"""
        <div class="main-header">
            <div style="font-size:32px; font-weight:800;">التحضير التقني لـ مدرسة القطيف الثانوية</div>
            <div style="font-size:20px; color:#ffd700; margin-top:10px;">فكرة وبرمجة: أ. عارف أحمد الحداد</div>
            <div style="font-size:18px; color:#cfd8dc;">إشراف مدير المدرسة: أ. فراس آل عبد المحسن</div>
        </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 1.5, 1])
    with col_b:
        if st.button("📝 رصد غياب الطلاب", type="primary", use_container_width=True): 
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير", use_container_width=True): 
            st.session_state.page = "a_log"; st.rerun()

# --- قسم المعلم (الدخول) ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "mark"; st.rerun()
        else: st.error("السجل غير مسجل.")

# --- قسم رصد الحضور ---
elif st.session_state.page == "mark":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher} | التاريخ: {today}")
    res_s = supabase.table('students').select("committee").execute()
    if res_s.data:
        coms = sorted(list(set([str(i['committee']) for i in res_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
        if sel_c != "---":
            students = supabase.table('students').select("*").eq("committee", sel_c).execute()
            old_att = supabase.table('attendance').select("*").eq("committee", sel_c).eq("date", today).execute()
            old_map = {i['student_name']: i['status'] for i in old_att.data}
            results = []
            for s in students.data:
                prev = old_map.get(s['student_name'], "حاضر")
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['student_name'], horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": st.session_state.teacher})
            if st.button("💾 حفظ الرصد", use_container_width=True):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("تم الحفظ!"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- لوحة الإدارة ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": 
        st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير الموحدة", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1:
        d = st.date_input("تاريخ التقرير:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res_att.data:
            df_all = pd.DataFrame(res_att.data)
            df_report = df_all[df_all['status'].isin(['غائب', 'متأخر'])].copy()
            if not df_report.empty:
                res_std = supabase.table("students").select("*").execute()
                df_std = pd.DataFrame(res_std.data)
                name_col = 'student_name' if 'student_name' in df_std.columns else df_std.columns[1]
                class_col = 'class_name' if 'class_name' in df_std.columns else ('الشعبة' if 'الشعبة' in df_std.columns else df_std.columns[2])
                s_map = dict(zip(df_std[name_col], df_std[class_col]))
                df_report['الشعبة'] = df_report['student_name'].map(s_map).fillna("---")
                st.table(df_report[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee':'اللجنة','student_name':'الطالب'}))
                
                # أزرار الواتساب
                col1, col2, col3 = st.columns(3)
                def wa(df, t):
                    msg = f"🗓️ *{t}*%0A📅 *التاريخ:* {d}%0A"
                    for _, r in df.iterrows(): msg += f"-----------------------%0A📦 اللجنة: {r['committee']}%0A👤 الاسم: {r['student_name']}%0A🏫 الشعبة: {r['الشعبة']}%0A⚠️ الحالة: {r['status']}%0A"
                    return msg
                with col1: st.markdown(f'<a href="https://wa.me/?text={wa(df_report, "تقرير الغياب والتأخر")}" target="_blank" class="wa-button wa-all">📲 إرسال (الكل)</a>', unsafe_allow_html=True)
                with col2:
                    df_abs = df_report[df_report['status'] == 'غائب']
                    if not df_abs.empty: st.markdown(f'<a href="https://wa.me/?text={wa(df_abs, "تقرير الغائبين")}" target="_blank" class="wa-button wa-absent">🚫 إرسال (الغائبين)</a>', unsafe_allow_html=True)
                with col3:
                    df_late = df_report[df_report['status'] == 'متأخر']
                    if not df_late.empty: st.markdown(f'<a href="https://wa.me/?text={wa(df_late, "تقرير المتأخرين")}" target="_blank" class="wa-button wa-late">⏳ إرسال (المتأخرين)</a>', unsafe_allow_html=True)
            else: st.success("لا يوجد غياب أو تأخر.")
        else: st.info("لا توجد سجلات حضور.")

    with tab2:
        st.subheader("🏘️ حالة اللجان")
        res_s = supabase.table('students').select("committee").execute()
        if res_s.data:
            all_c = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
            done = [str(i['committee']) for i in supabase.table('attendance').select("committee").eq("date", str(datetime.now().date())).execute().data]
            c1, c2 = st.columns(2)
            with c1:
                st.success("✅ رُصدت")
                for c in all_c:
                    if c in done: st.write(f"📍 لجنة {c}")
            with c2:
                st.error("❌ لم تُرصد")
                for c in all_c:
                    if c not in done: st.write(f"⚠️ لجنة {c}")

    with tab3:
        if st.text_input("رمز البيانات:", type="password") == "4321":
            st.subheader("💾 إدارة وتحديث البيانات")
            
            # --- أزرار النسخة الاحتياطية ---
            res_backup = supabase.table('students').select("*").execute()
            if res_backup.data:
                df_backup = pd.DataFrame(res_backup.data)
                col_csv, col_xlsx = st.columns(2)
                with col_csv:
                    st.download_button("📥 تحميل نسخة CSV", df_backup.to_csv(index=False).encode('utf-8-sig'), f"students_backup_{datetime.now().date()}.csv", "text/csv", use_container_width=True)
                with col_xlsx:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer: df_backup.to_excel(writer, index=False)
                    st.download_button("📥 تحميل نسخة Excel", output.getvalue(), f"students_backup_{datetime.now().date()}.xlsx", use_container_width=True)
            
            st.divider()
            
            # --- إصلاح خطأ رفع البيانات ---
            up = st.file_uploader("تحديث قاعدة البيانات (رفع ملف Excel أو CSV):")
            if up and st.button("🚀 بدء التحديث"):
                try:
                    # قراءة الملف حسب نوعه
                    if up.name.endswith('.csv'):
                        df_new = pd.read_csv(up)
                    else:
                        df_new = pd.read_excel(up)
                    
                    # تنظيف البيانات وتغيير أسماء الأعمدة لتطابق قاعدة البيانات
                    # سنفترض أن الأعمدة المطلوبة هي: student_name, committee, class_name
                    # هذا الجزء يقوم بالبحث عن العمود المناسب حتى لو اختلف الاسم قليلاً
                    mapping = {
                        'اسم الطالب': 'student_name', 'الاسم': 'student_name', 'Name': 'student_name',
                        'اللجنة': 'committee', 'رقم اللجنة': 'committee', 'Committee': 'committee',
                        'الشعبة': 'class_name', 'الفصل': 'class_name', 'Class': 'class_name'
                    }
                    df_new.rename(columns=mapping, inplace=True)
                    
                    # اختيار الأعمدة الضرورية فقط
                    cols_to_keep = ['student_name', 'committee', 'class_name']
                    # التحقق من وجود الأعمدة
                    missing = [c for c in cols_to_keep if c not in df_new.columns]
                    if missing:
                        st.error(f"الملف يفتقد للأعمدة التالية أو مسمياتها غير واضحة: {missing}")
                        st.info("تأكد أن الملف يحتوي على: (اسم الطالب، رقم اللجنة، الشعبة)")
                    else:
                        df_final = df_new[cols_to_keep].dropna(subset=['student_name'])
                        df_final['committee'] = df_final['committee'].astype(str)
                        
                        # تنفيذ التحديث
                        with st.spinner("جاري تحديث البيانات..."):
                            # حذف البيانات القديمة (باستثناء الصفوف الخاصة إذا وجدت)
                            supabase.table('students').delete().neq('student_name', '---').execute()
                            # إدخال البيانات الجديدة
                            supabase.table('students').insert(df_final.to_dict('records')).execute()
                            st.success("✅ تم تحديث قاعدة بيانات الطلاب بنجاح!")
                            time.sleep(2)
                            st.rerun()
                except Exception as e:
                    st.error(f"حدث خطأ أثناء المعالجة: {str(e)}")
