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

# 2. إعدادات الواجهة والتنسيق (CSS)
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .main-header { background-color: #1a237e; color: white; padding: 30px; border-radius: 15px; text-align: center; border-bottom: 5px solid #ffd700; margin-bottom: 20px; }
    .thank-you-card { text-align: center; padding: 50px; background: white; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); border: 2px solid #1a237e; margin-top: 50px; }
    .teacher-log-span { background-color: #f0f2f6; padding: 2px 8px; border-radius: 5px; color: #1a237e; font-weight: bold; font-size: 14px; border: 1px solid #d1d9e6; }
    .stButton>button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- التنقل بين الصفحات ---
if st.session_state.page == "home":
    st.markdown(f"""
        <div class="main-header">
            <h1 style="margin:0; font-size: 35px;">التحضير التقني</h1>
            <h2 style="margin:0; font-size: 28px;">مدرسة القطيف الثانوية</h2>
            <p style="color:#ffd700; font-size:22px; margin-top:10px; font-weight: bold;">مدير المدرسة : أ. فراس آل عبدالمحسن</p>
            <div style="font-size: 22px; margin-top: 22px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 22px;">
                <h3 style="margin:0; font-size: 22px;">فكرة و برمجة </h3>
                <h4 style="margin:0; font-size: 22px;">أ. عارف أحمد الحداد </h4>
                <h5 style="margin:0; font-size: 22px;">2026</h5>
            </div>
        </div>
    """, unsafe_allow_html=True)
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        if st.button("📝 رصد غياب الطلاب اليومي", type="primary"): st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة"): st.session_state.page = "a_log"; st.rerun()

elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "mark"; st.rerun()
        else: st.error("عذراً، السجل المدني غير مسجل.")

elif st.session_state.page == "mark":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher} | التاريخ: {today}")
    res_s = supabase.table('students').select("committee").execute()
    if res_s.data:
        coms = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
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
            if st.button("💾 حفظ الرصد النهائي"):
                prev_t = [i['teacher_name'] for i in old_att.data if i.get('teacher_name')]
                all_t = " | ".join(list(dict.fromkeys(prev_t + [st.session_state.teacher])))
                for r in results: r['teacher_name'] = all_t
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.snow(); st.session_state.page = "thank_you"; st.rerun()

elif st.session_state.page == "thank_you":
    st.markdown(f'<div class="thank-you-card"><h1 style="color:#22c55e;">👏 شكراً لك أ. {st.session_state.teacher}</h1><p>تم حفظ الرصد بنجاح.</p></div>', unsafe_allow_html=True)
    if st.button("🏠 عودة"): st.session_state.page = "home"; st.rerun()

elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1:
        d = st.date_input("تاريخ التقرير:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res_att.data:
            df = pd.DataFrame(res_att.data)
            df = df[df['status'].isin(['غائب', 'متأخر'])][['committee', 'student_name', 'status', 'teacher_name']]
            df.columns = ['اللجنة', 'اسم الطالب', 'الحالة', 'المعلمون']
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("🏘️ متابعة اللجان")
        att_today = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        done_dict = {str(i['committee']): i['teacher_name'] for i in att_today.data}
        res_s = supabase.table('students').select("committee").execute()
        all_c = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ رصدت")
            for c in all_c:
                if c in done_dict: st.markdown(f"📍 لجنة {c}: <span class='teacher-log-span'>{done_dict[c].replace(' | ', ' ⬅️ ')}</span>", unsafe_allow_html=True)
        with c2:
            st.error("❌ لم ترصد")
            for c in all_c:
                if c not in done_dict: st.write(f"⚠️ لجنة {c}")

    with tab3: # --- قسم إدارة البيانات والتحميل المستقل ---
        if st.text_input("رمز حماية البيانات:", type="password") == "4321":
            
            # --- قسم المعلمين ---
            st.markdown("### 👨‍🏫 إدارة سجل المعلمين")
            res_t = supabase.table('teachers').select("*").execute()
            if res_t.data:
                df_t = pd.DataFrame(res_t.data)
                tc1, tc2 = st.columns(2)
                with tc1:
                    st.download_button("📥 المعلمين CSV", df_t.to_csv(index=False).encode('utf-8-sig'), "teachers_list.csv", "text/csv")
                with tc2:
                    t_buf = io.BytesIO()
                    with pd.ExcelWriter(t_buf, engine='openpyxl') as wr: df_t.to_excel(wr, index=False)
                    st.download_button("📊 المعلمين Excel", t_buf.getvalue(), "teachers_list.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                up_t = st.file_uploader("تحديث قائمة المعلمين (رفع):", key="up_t")
                if up_t and st.button("🚀 رفع وتحديث المعلمين"):
                    df_nt = pd.read_csv(up_t) if up_t.name.endswith('.csv') else pd.read_excel(up_t)
                    supabase.table('teachers').delete().neq('name_tech', '0').execute()
                    supabase.table('teachers').insert(df_nt.to_dict('records')).execute()
                    st.success("تم تحديث المعلمين!")

            st.divider()

            # --- قسم الطلاب ---
            st.markdown("### 👨‍🎓 إدارة سجل الطلاب")
            res_s = supabase.table('students').select("*").execute()
            if res_s.data:
                df_s = pd.DataFrame(res_s.data)
                sc1, sc2 = st.columns(2)
                with sc1:
                    st.download_button("📥 الطلاب CSV", df_s.to_csv(index=False).encode('utf-8-sig'), "students_list.csv", "text/csv")
                with sc2:
                    s_buf = io.BytesIO()
                    with pd.ExcelWriter(s_buf, engine='openpyxl') as wr: df_s.to_excel(wr, index=False)
                    st.download_button("📊 الطلاب Excel", s_buf.getvalue(), "students_list.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                up_s = st.file_uploader("تحديث قائمة الطلاب (رفع):", key="up_s")
                if up_s and st.button("🚀 رفع وتحديث الطلاب"):
                    df_ns = pd.read_csv(up_s) if up_s.name.endswith('.csv') else pd.read_excel(up_s)
                    supabase.table('students').delete().neq('student_name', '0').execute()
                    supabase.table('students').insert(df_ns.to_dict('records')).execute()
                    st.success("تم تحديث الطلاب!")
