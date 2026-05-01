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
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    
    /* تنسيق الحاويات والأزرار */
    .stButton>button { border-radius: 10px; font-weight: bold; height: 50px; width: 100%; font-size: 18px; }
    .wa-button { color: white !important; padding: 12px; border-radius: 10px; text-align: center; display: block; text-decoration: none; font-weight: bold; margin-top: 10px; font-size: 16px; }
    .wa-all { background-color: #28a745; }
    .wa-absent { background-color: #dc3545; }
    .wa-late { background-color: #fd7e14; }
    
    th { background-color: #1a237e !important; color: white !important; text-align: center !important; font-size: 18px; }
    td { text-align: center !important; font-size: 16px; }
    </style>
    ''', unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- 🏠 الصفحة الرئيسية (الغلاف المنسق حسب طلبك الأخير) ---
if st.session_state.page == "home":
    st.markdown('''
        <div style="background-color: #1a237e; padding: 40px 20px; text-align: center; color: white; border-bottom: 8px solid #ffd700; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 30px;">
            <div style="font-size: 38px; font-weight: 800; margin-bottom: 5px;">التحضير التقني</div>
            <div style="font-size: 34px; font-weight: 700; margin-bottom: 20px;">مدرسة القطيف الثانوية</div>
            
            <div style="margin: 25px 0;"></div> <div style="font-size: 24px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px;">فكرة وبرمجة</div>
            <div style="font-size: 30px; font-weight: 700; color: #ffd700; margin-bottom: 25px;">أ. عارف أحمد الحداد</div>
            
            <div style="margin: 25px 0;"></div> <div style="font-size: 22px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px;">مدير المدرسة</div>
            <div style="font-size: 28px; font-weight: 600; color: #ffffff;">أ. فراس آل عبدالمحسن</div>
        </div>
    ''', unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 1.5, 1])
    with col_b:
        st.write("")
        if st.button("📝 رصد غياب الطلاب اليومي", type="primary", use_container_width=True): 
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة", use_container_width=True): 
            st.session_state.page = "a_log"; st.rerun()

# --- 📝 قسم رصد المعلم ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة للرئيسية"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "mark"; st.rerun()
        else: st.error("عذراً، السجل غير مسجل.")

elif st.session_state.page == "mark":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher} | التاريخ: {today}")
    res_s = supabase.table('students').select("committee").execute()
    if res_s.data:
        coms = sorted(list(set([str(i['committee']) for i in res_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        sel_c = st.selectbox("اختر رقم اللجنة:", ["---"] + coms)
        if sel_c != "---":
            students = supabase.table('students').select("*").eq("committee", sel_c).execute()
            old_att = supabase.table('attendance').select("*").eq("committee", sel_c).eq("date", today).execute()
            old_map = {i['student_name']: i['status'] for i in old_att.data}
            results = []
            for s in students.data:
                prev = old_map.get(s['student_name'], "حاضر")
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['student_name'], horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": st.session_state.teacher})
            if st.button("💾 حفظ بيانات الرصد", use_container_width=True):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("تم حفظ البيانات بنجاح!"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- ⚙️ لوحة الإدارة ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": 
        st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير الموحدة", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1:
        d = st.date_input("اختر تاريخ التقرير:", datetime.now())
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
                
                col1, col2, col3 = st.columns(3)
                def build_wa(df, title, emoji):
                    msg = f"🗓️ *{title}*%0A📅 *التاريخ:* {d}%0A-----------------------%0A"
                    for _, r in df.iterrows():
                        msg += f"📦 اللجنة: {r['committee']}%0A👤 الطالب: {r['student_name']}%0A🏫 الشعبة: {r['الشعبة']}%0A{emoji} الحالة: {r['status']}%0A-----------------------%0A"
                    return msg
                
                with col1: st.markdown(f'<a href="https://wa.me/?text={build_wa(df_report, "تقرير الغياب والتأخر", "⚠️")}" target="_blank" class="wa-button wa-all">📲 إرسال (الكل)</a>', unsafe_allow_html=True)
                with col2:
                    df_abs = df_report[df_report['status'] == 'غائب']
                    if not df_abs.empty: st.markdown(f'<a href="https://wa.me/?text={build_wa(df_abs, "تقرير الغائبين فقط", "🔴")}" target="_blank" class="wa-button wa-absent">🚫 إرسال (الغائبين)</a>', unsafe_allow_html=True)
                with col3:
                    df_late = df_report[df_report['status'] == 'متأخر']
                    if not df_late.empty: st.markdown(f'<a href="https://wa.me/?text={build_wa(df_late, "تقرير المتأخرين فقط", "⏳")}" target="_blank" class="wa-button wa-late">⏳ إرسال (المتأخرين)</a>', unsafe_allow_html=True)
            else: st.success("لا يوجد حالات غياب أو تأخر لهذا اليوم.")
        else: st.info("لا توجد سجلات رصد لهذا التاريخ.")

    with tab2:
        st.subheader("🏘️ متابعة رصد لجان اليوم")
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
        if st.text_input("رمز إدارة البيانات:", type="password") == "4321":
            # --- أزرار النسخة الاحتياطية ---
            st.subheader("💾 النسخة الاحتياطية")
            res_backup = supabase.table('students').select("*").execute()
            if res_backup.data:
                df_bk = pd.DataFrame(res_backup.data)
                col_csv, col_xlsx = st.columns(2)
                with col_csv:
                    st.download_button("📥 تحميل نسخة CSV", df_bk.to_csv(index=False).encode('utf-8-sig'), f"backup_{datetime.now().date()}.csv", "text/csv", use_container_width=True)
                with col_xlsx:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as wr: df_bk.to_excel(wr, index=False)
                    st.download_button("📊 تحميل نسخة XLSX (Excel)", output.getvalue(), f"backup_{datetime.now().date()}.xlsx", use_container_width=True)
            
            st.divider()
            # --- حذف سجلات تاريخ محدد ---
            st.subheader("🗑️ حذف سجلات رصد قديمة")
            del_d = st.date_input("اختر التاريخ المراد مسح سجلاته نهائياً:", datetime.now())
            if st.button("⚠️ تنفيذ الحذف النهائي لهذا التاريخ"):
                supabase.table('attendance').delete().eq("date", str(del_d)).execute()
                st.warning(f"تم حذف سجلات يوم {del_d} بنجاح.")

            st.divider()
            # --- استيراد بيانات جديدة ---
            st.subheader("🚀 استيراد بيانات طلاب جديدة")
            up = st.file_uploader("ارفع ملف الطلاب الجديد:")
            if up and st.button("بدء التحديث"):
                df_new = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                supabase.table('students').delete().neq('committee', '0').execute()
                supabase.table('students').insert(df_new.to_dict('records')).execute()
                st.success("تم تحديث قاعدة البيانات!")
