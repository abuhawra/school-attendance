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

# --- 🎨 التنسيق المرئي والـ CSS ---
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    
    .main-header { 
        background-color: #1a237e; padding: 30px; text-align: center; color: white; 
        border-radius: 20px; margin-bottom: 25px; border-bottom: 8px solid #ff9800; 
    }
    
    .school-name {
        margin: 0 !important; padding: 0 !important;
        line-height: 0.8 !important; color: #ff9800;
        font-size: 45px; font-weight: 800;
    }
    
    .teacher-tag { background-color: #f0f2f6; color: #1a237e; padding: 6px 12px; border-radius: 15px; font-weight: bold; font-size: 14px; border: 1px solid #d1d9e6; display: inline-block; }
    .arrow-sep { color: #ff9800; font-weight: bold; margin: 0 5px; }
    .wa-link { text-decoration: none; color: white !important; display: block; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 10px; }
    .wa-absent { background-color: #dc3545; }
    .wa-late { background-color: #fd7e14; }
    .thank-you-box { text-align: center; padding: 40px; background: #f8fdf9; border-radius: 20px; border: 2px solid #22c55e; margin-top: 20px; }
    </style>
''', unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "home"

# --- 🛠️ دالات مساعدة ---
def get_wa_link(df, status_type, d):
    if df.empty: return None
    df_sorted = df.copy()
    df_sorted['c_sort'] = pd.to_numeric(df_sorted['committee'], errors='coerce').fillna(0)
    df_sorted = df_sorted.sort_values(by='c_sort')
    header_emoji = "🚫" if "غائب" in status_type else "⏳"
    msg = f"{header_emoji} *قائمة {status_type}*%0A📅 *التاريخ:* {d}%0A-----------------%0A"
    for _, r in df_sorted.iterrows():
        msg += f"📦 *اللجنة:* {r['committee']}%0A👤 *الاسم:* {r['student_name']}%0A🏫 *الشعبة:* {r.get('الشعبة','--')}%0A⚠️ *الحالة:* {r['status']}%0A-----------------%0A"
    return f"https://wa.me/?text={msg}"

# --- 1. الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('''
        <div class="main-header">
            <h1 style="color:#ff9800; font-size: 55px; font-weight: 800; margin-bottom: 0;">بَصمَة تَميُز</h1>
            <h2 style="color:#ff9800; font-size: 22px; font-weight: 500; margin-top: 0; line-height: 0;">أول خطوة للنجاح...التحضير</h2>
                <h2 class="school-name">مدرسة</h2>
                <h2 class="school-name">القطيف الثانوية</h2>
            <div style="font-size: 20px; margin-top: 15px; border-top: 2px solid rgba(255,255,255,0.2); padding-top: 15px;">
                <p style="color:#ff9800; font-size: 24px; font-weight: 500; margin: 0;">مدير المدرسة</p>
                <p style="color:#ffffff; font-size: 24px; font-weight: 500; margin: 0;">أ. فراس آل عبدالمحسن</p>
                <p style="color:#ff9800; font-size: 22px; margin: 5px 0;">فكرة وبرمجة</p>
                <p style="color:#ffffff; font-size: 22px; margin: 5px 0;"> أ. عارف أحمد الحداد</p>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        if st.button("📝 رصد غياب الطلاب اليومي", use_container_width=True, type="primary"):
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة", use_container_width=True):
            st.session_state.page = "a_log"; st.rerun()

# --- 2. دخول المعلم ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "mark"; st.rerun()
        else: st.error("السجل المدني غير مسجل.")

# --- 3. واجهة الرصد ---
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
            
            if old_att.data:
                prev_list = []
                for entry in old_att.data:
                    for n in str(entry.get('teacher_name', '')).split(" | "):
                        if n.strip() and n.strip() not in prev_list: prev_list.append(n.strip())
                if st.session_state.teacher not in prev_list: prev_list.append(st.session_state.teacher)
                all_t = " | ".join(prev_list)
                old_map = {i['student_name']: i['status'] for i in old_att.data}
            else:
                all_t = st.session_state.teacher
                old_map = {}

            results = []
            for s in students.data:
                prev = old_map.get(s['student_name'], "حاضر")
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['student_name'], horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": all_t})
            
            if st.button("💾 حفظ الرصد النهائي", use_container_width=True):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.session_state.page = "thank_you"; st.rerun()

# --- 4. صفحة الشكر ---
elif st.session_state.page == "thank_you":
    st.snow()
    st.markdown(f'<div class="thank-you-box"><h1>✅ تم الرصد بنجاح</h1><h2>أ. {st.session_state.get("teacher", "")}</h2></div>', unsafe_allow_html=True)
    if st.button("🏠 العودة للرئيسية", use_container_width=True): st.session_state.page = "home"; st.rerun()

# --- 5. لوحة الإدارة ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 تقارير الانضباط", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1: # تقارير الانضباط
        d_rep = st.date_input("اختر تاريخ التقرير:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d_rep)).execute()
        
        if res_att.data:
            df_all = pd.DataFrame(res_att.data)
            df_all['c_sort'] = pd.to_numeric(df_all['committee'], errors='coerce').fillna(0)
            df_all = df_all.sort_values(by='c_sort')
            
            # --- زر حذف الغياب لهذا اليوم ---
            with st.expander("⚠️ خيارات الحذف"):
                if st.button(f"🗑️ حذف كافة سجلات يوم {d_rep}", use_container_width=True):
                    supabase.table("attendance").delete().eq("date", str(d_rep)).execute()
                    st.warning("تم حذف سجلات اليوم المختار."); st.rerun()
            
            res_std = supabase.table("students").select("student_name, class_name").execute()
            s_map = dict(zip([i['student_name'] for i in res_std.data], [i['class_name'] for i in res_std.data]))
            df_all['الشعبة'] = df_all['student_name'].map(s_map).fillna("---")
            report_df = df_all[df_all['status'].isin(['غائب', 'متأخر'])].copy()
            
            st.dataframe(report_df[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee':'اللجنة','student_name':'الطالب','status':'الحالة','teacher_name':'المعلمون'}), use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns(2)
            with c1:
                l1 = get_wa_link(report_df[report_df['status'] == "غائب"], "الغائبين", d_rep)
                if l1: st.markdown(f'<a href="{l1}" target="_blank" class="wa-link wa-absent">🚫 إرسال الغائبين</a>', unsafe_allow_html=True)
            with c2:
                l2 = get_wa_link(report_df[report_df['status'] == "متأخر"], "المتأخرين", d_rep)
                if l2: st.markdown(f'<a href="{l2}" target="_blank" class="wa-link wa-late">⏳ إرسال المتأخرين</a>', unsafe_allow_html=True)
        else: st.info("لا توجد بيانات لهذا التاريخ.")

    with tab2: # حالة اللجان مع السهم
        st.subheader("🏘️ حالة رصد اللجان اللحظية")
        att_now = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        
        # معالجة الأسماء لإضافة السهم
        comm_status = {}
        for r in att_now.data:
            c_id = str(r['committee'])
            t_names = str(r['teacher_name']).split(" | ")
            clean_names = []
            for name in t_names:
                if name.strip() and name.strip() not in clean_names: clean_names.append(name.strip())
            # دمج الأسماء بسهم
            comm_status[c_id] = " <span class='arrow-sep'>⬅️</span> ".join([f"<span class='teacher-tag'>{n}</span>" for n in clean_names])

        res_s = supabase.table('students').select("committee").execute()
        all_c = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
        
        col_ok, col_no = st.columns(2)
        with col_ok:
            st.success("✅ لجان تم رصدها")
            for c in all_c:
                if c in comm_status: st.markdown(f"📍 **لجنة {c}:** {comm_status[c]}", unsafe_allow_html=True)
        with col_no:
            st.error("❌ لجان لم تُرصد")
            for c in all_c:
                if c not in comm_status: st.write(f"⚠️ لجنة {c}")

    with tab3: # إدارة البيانات (طلاب ومعلمين)
        if st.text_input("رمز الأمان لإدارة البيانات:", type="password") == "4321":
            st.markdown("### 💾 النسخ الاحتياطي للبيانات")
            
            # --- قسم الطلاب ---
            st.write("👨‍🎓 **قاعدة بيانات الطلاب**")
            df_s = pd.DataFrame(supabase.table('students').select("*").execute().data)
            if not df_s.empty:
                buf_s = io.BytesIO()
                with pd.ExcelWriter(buf_s) as wr: df_s.to_excel(wr, index=False)
                st.download_button("📥 تحميل سجل الطلاب (Excel)", buf_s.getvalue(), "students_backup.xlsx", use_container_width=True)
            
            st.divider()
            
            # --- قسم المعلمين ---
            st.write("👨‍🏫 **قاعدة بيانات المعلمين**")
            df_t = pd.DataFrame(supabase.table('teachers').select("*").execute().data)
            if not df_t.empty:
                buf_t = io.BytesIO()
                with pd.ExcelWriter(buf_t) as wr: df_t.to_excel(wr, index=False)
                st.download_button("📥 تحميل سجل المعلمين (Excel)", buf_t.getvalue(), "teachers_backup.xlsx", use_container_width=True)
