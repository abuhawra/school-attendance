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
    .wa-link { text-decoration: none; color: white !important; display: block; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 10px; font-size: 18px; }
    .wa-absent { background-color: #dc3545; }
    .wa-late { background-color: #fd7e14; }
    .teacher-log-span { background-color: #f0f2f6; padding: 2px 8px; border-radius: 5px; color: #1a237e; font-weight: bold; font-size: 14px; border: 1px solid #d1d9e6; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- دالة بناء رسالة الواتساب ---
def get_wa_link(df, status_type, d):
    if df.empty: return None
    header_emoji = "🚫" if "غائب" in status_type else "⏳"
    msg = f"{header_emoji} *قائمة {status_type}*%0A📅 *التاريخ:* {d}%0A-----------------%0A"
    df_sorted = df.copy()
    df_sorted['committee_int'] = pd.to_numeric(df_sorted['committee'], errors='coerce').fillna(0)
    df_sorted = df_sorted.sort_values(by='committee_int')
    for _, r in df_sorted.iterrows():
        shoba = r.get('الشعبة', '---')
        msg += f"📦 *اللجنة:* {r['committee']}%0A👤 *الاسم:* {r['student_name']}%0A🏫 *الشعبة:* {shoba}%0A⚠️ *الحالة:* {r['status']}%0A-----------------%0A"
    return f"https://wa.me/?text={msg}"

# --- الصفحة الرئيسية ---
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
        if st.button("📝 رصد غياب الطلاب اليومي", type="primary", use_container_width=True): st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة", use_container_width=True): st.session_state.page = "a_log"; st.rerun()

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
            if st.button("💾 حفظ الرصد النهائي", use_container_width=True):
                prev_t = [i['teacher_name'] for i in old_att.data if i.get('teacher_name')]
                all_t = " | ".join(list(dict.fromkeys(prev_t + [st.session_state.teacher])))
                for r in results: r['teacher_name'] = all_t
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.snow(); st.session_state.page = "thank_you"; st.rerun()

elif st.session_state.page == "thank_you":
    st.markdown(f'<div class="thank-you-card"><h1 style="color:#22c55e;">👏 شكراً لك أ. {st.session_state.teacher}</h1><p>تم حفظ الرصد بنجاح.</p></div>', unsafe_allow_html=True)
    if st.button("🏠 عودة", use_container_width=True): st.session_state.page = "home"; st.rerun()

elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1: # التقارير والواتساب
        d = st.date_input("تاريخ التقرير:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res_att.data:
            df_all = pd.DataFrame(res_att.data)
            res_std = supabase.table("students").select("student_name, class_name").execute()
            if res_std.data:
                std_map = {i['student_name']: i['class_name'] for i in res_std.data}
                df_all['الشعبة'] = df_all['student_name'].map(std_map).fillna("---")
            df_report = df_all[df_all['status'].isin(['غائب', 'متأخر'])].copy()
            if not df_report.empty:
                df_report['committee_sort'] = pd.to_numeric(df_report['committee'], errors='coerce').fillna(0)
                df_report = df_report.sort_values(by='committee_sort')
                st.dataframe(df_report[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee':'اللجنة','student_name':'الطالب','status':'الحالة','teacher_name':'المعلمون'}), use_container_width=True, hide_index=True)
                st.markdown("### 📲 إرسال التقارير")
                c1, c2 = st.columns(2)
                with c1:
                    link_abs = get_wa_link(df_all[df_all['status'] == "غائب"], "الغائبين", d)
                    if link_abs: st.markdown(f'<a href="{link_abs}" target="_blank" class="wa-link wa-absent">🚫 إرسال الغائبين</a>', unsafe_allow_html=True)
                with c2:
                    link_late = get_wa_link(df_all[df_all['status'] == "متأخر"], "المتأخرين", d)
                    if link_late: st.markdown(f'<a href="{link_late}" target="_blank" class="wa-link wa-late">⏳ إرسال المتأخرين</a>', unsafe_allow_html=True)
            else: st.success("لا يوجد غياب لهذا اليوم.")
        else: st.info("لا توجد سجلات لهذا التاريخ.")

    with tab2: # حالة اللجان
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

    with tab3: # إدارة البيانات (إعادة زر المسح)
        if st.text_input("رمز حماية البيانات:", type="password") == "4321":
            # --- 1. قسم مسح البيانات التاريخية ---
            st.markdown("### 🗑️ تنظيف بيانات الغياب")
            del_date = st.date_input("اختر التاريخ المراد حذفه:", datetime.now())
            if st.button("❌ حذف سجلات هذا التاريخ نهائياً"):
                supabase.table('attendance').delete().eq("date", str(del_date)).execute()
                st.warning(f"تم مسح كافة سجلات تاريخ {del_date}")
            st.divider()

            # --- 2. إدارة المعلمين ---
            st.markdown("### 👨‍🏫 المعلمين (تحميل وتحديث)")
            res_t = supabase.table('teachers').select("*").execute()
            if res_t.data:
                df_t = pd.DataFrame(res_t.data)
                tc1, tc2 = st.columns(2)
                with tc1: st.download_button("📥 المعلمين CSV", df_t.to_csv(index=False).encode('utf-8-sig'), "teachers.csv", use_container_width=True)
                with tc2:
                    t_buf = io.BytesIO()
                    with pd.ExcelWriter(t_buf, engine='openpyxl') as wr: df_t.to_excel(wr, index=False)
                    st.download_button("📊 المعلمين Excel", t_buf.getvalue(), "teachers.xlsx", use_container_width=True)
            
            st.divider()
            # --- 3. إدارة الطلاب ---
            st.markdown("### 👨‍🎓 الطلاب (تحميل وتحديث)")
            res_s = supabase.table('students').select("*").execute()
            if res_s.data:
                df_s = pd.DataFrame(res_s.data)
                sc1, sc2 = st.columns(2)
                with sc1: st.download_button("📥 الطلاب CSV", df_s.to_csv(index=False).encode('utf-8-sig'), "students.csv", use_container_width=True)
                with sc2:
                    s_buf = io.BytesIO()
                    with pd.ExcelWriter(s_buf, engine='openpyxl') as wr: df_s.to_excel(wr, index=False)
                    st.download_button("📊 الطلاب Excel", s_buf.getvalue(), "students.xlsx", use_container_width=True)
