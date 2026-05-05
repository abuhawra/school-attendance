import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
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
        border-radius: 20px; margin-bottom: 25px; border-bottom: 8px solid #ffd700; 
    }
    .teacher-tag { background-color: #f0f2f6; color: #1a237e; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px; border: 1px solid #d1d9e6; margin: 4px; display: inline-block; }
    .wa-link { text-decoration: none; color: white !important; display: block; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 10px; font-size: 18px; }
    .wa-absent { background-color: #dc3545; }
    .wa-late { background-color: #fd7e14; }
    .arrow-sep { color: #1a237e; font-weight: bold; margin: 0 8px; font-size: 18px; }
    .thank-you-box { text-align: center; padding: 40px; background: #f8fdf9; border-radius: 20px; border: 2px solid #22c55e; margin-top: 20px; }
    </style>
''', unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "home"

# --- 🛠️ دالة بناء رسالة الواتساب ---
def get_wa_link(df, status_type, d):
    if df.empty: return None
    header_emoji = "🚫" if "غائب" in status_type else "⏳"
    msg = f"{header_emoji} *قائمة {status_type}*%0A📅 *التاريخ:* {d}%0A-----------------%0A"
    df_sorted = df.copy()
    df_sorted['committee_int'] = pd.to_numeric(df_sorted['committee'], errors='coerce').fillna(0)
    df_sorted = df_sorted.sort_values(by='committee_int')
    for _, r in df_sorted.iterrows():
        msg += f"📦 *اللجنة:* {r['committee']}%0A👤 *الاسم:* {r['student_name']}%0A🏫 *الشعبة:* {r.get('الشعبة','--')}%0A⚠️ *الحالة:* {r['status']}%0A-----------------%0A"
    return f"https://wa.me/?text={msg}"

# --- 1. الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('''
        <div class="main-header">
            <h2 style="color:#ff9800; font-size: 50px; font-weight: 800;">بصمة تميز</h2>
            <h2 style="color:#ffd700; font-size: 20px; font-weight: 500; margin-top: 0.8; line-height: 0.8;">النجاح يبدأ بالتحضير اليومي</h2>
            <h2 style="margin:10px 0; font-size: 35px;">مدرسة</h2>
            <h2 style="margin:10px 0; font-size: 35px;">القطيف الثانوية</h2>
            <div style="font-size: 18px; margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 20px;">
            </div>
            <h2 style="color:#ffd700; font-size: 24px; font-weight: 500;">مدير المدرسة</h2>
            <h2 style="color:#ffffff; font-size: 24px; font-weight: 500;">أ. فراس آل عبدالمحسن</h2>
            <h2 style="color:#ffd700; font-size: 24px;">فكرة و برمجة</h2>
            <h2 style="color:#ffffff; font-size: 24px;">أ. عارف أحمد الحداد</h2>
        </div>
    ''', unsafe_allow_html=True)
    
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        if st.button("📝 رصد غياب الطلاب اليومي", use_container_width=True, type="primary"):
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة", use_container_width=True):
            st.session_state.page = "a_log"; st.rerun()

# --- 2. تسجيل دخول المعلم ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "mark"; st.rerun()
        else: st.error("عذراً، السجل المدني غير مسجل.")

# --- 3. واجهة الرصد ---
elif st.session_state.page == "mark":
    today = str(datetime.now().date())
    st.info(f"المعلم الحالي: {st.session_state.teacher} | التاريخ: {today}")
    res_s = supabase.table('students').select("committee").execute()
    if res_s.data:
        coms = sorted(list(set([str(i['committee']) for i in res_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
        if sel_c != "---":
            students = supabase.table('students').select("*").eq("committee", sel_c).execute()
            old_att = supabase.table('attendance').select("*").eq("committee", sel_c).eq("date", today).execute()
            
            # معالجة أسماء المعلمين الراصدين
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
    teacher_name = st.session_state.get('teacher', 'المعلم')
    st.markdown(f'''
        <div class="thank-you-box">
            <h1 style="color: #22c55e; font-size: 40px;">✅ تم الرصد بنجاح</h1>
            <h2 style="color: #1a237e; margin-top: 20px;">شكراً لك: أ. {teacher_name}</h2>
        </div>
    ''', unsafe_allow_html=True)
    if st.button("🏠 العودة للرئيسية", use_container_width=True):
        st.session_state.page = "home"; st.rerun()

# --- 5. لوحة الإدارة ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": 
        st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير والحذف", "🏘️ حالة اللجان", "💾 النسخ الاحتياطي"])
    
    with tab1:
        d = st.date_input("اختر التاريخ المطلوب:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        
        if res_att.data:
            df_all = pd.DataFrame(res_att.data)
            with st.expander("🗑️ منطقة الحذف (ليوم محدد)"):
                if st.button(f"حذف رصد يوم {d} نهائياً", use_container_width=True):
                    supabase.table("attendance").delete().eq("date", str(d)).execute()
                    st.success("تم حذف البيانات."); st.rerun()
            
            st.divider()
            res_std = supabase.table("students").select("student_name, class_name").execute()
            s_map = dict(zip([i['student_name'] for i in res_std.data], [i['class_name'] for i in res_std.data]))
            df_all['الشعبة'] = df_all['student_name'].map(s_map).fillna("---")
            report_df = df_all[df_all['status'].isin(['غائب', 'متأخر'])].copy()
            st.dataframe(report_df[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee':'اللجنة','student_name':'الطالب','status':'الحالة','teacher_name':'المعلمون'}), use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns(2)
            with c1:
                link_abs = get_wa_link(df_all[df_all['status'] == "غائب"], "الغائبين", d)
                if link_abs: st.markdown(f'<a href="{link_abs}" target="_blank" class="wa-link wa-absent">🚫 إرسال الغائبين</a>', unsafe_allow_html=True)
            with c2:
                link_late = get_wa_link(df_all[df_all['status'] == "متأخر"], "المتأخرين", d)
                if link_late: st.markdown(f'<a href="{link_late}" target="_blank" class="wa-link wa-late">⏳ إرسال المتأخرين</a>', unsafe_allow_html=True)
        else:
            st.info("لا توجد بيانات رصد لهذا التاريخ.")

    with tab2: # حالة اللجان - تصحيح البيانات غير المقروءة
        st.subheader("🏘️ متابعة رصد اللجان اللحظي")
        # جلب البيانات لليوم الحالي
        att_today = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        
        # تجميع المعلمين حسب اللجنة بشكل نظيف
        comm_map = {}
        for row in att_today.data:
            c_id = str(row['committee'])
            t_names = str(row['teacher_name']).split(" | ")
            clean_names = []
            for name in t_names:
                name = name.strip()
                if name and name not in clean_names: clean_names.append(name)
            comm_map[c_id] = clean_names

        res_s = supabase.table('students').select("committee").execute()
        all_c_list = sorted(list(set([str(i['committee']) for i in res_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        
        col_done, col_not = st.columns(2)
        with col_done:
            st.success("✅ لجان تم رصدها")
            for c in all_c_list:
                if c in comm_map:
                    names_html = "".join([f"<span class='teacher-tag'>{n}</span>" + ("<span class='arrow-sep'>⬅️</span>" if i < len(comm_map[c])-1 else "") for i, n in enumerate(comm_map[c])])
                    st.markdown(f"📍 **لجنة {c}:** {names_html}", unsafe_allow_html=True)
        with col_not:
            st.error("❌ لجان لم تُرصد")
            for c in all_c_list:
                if c not in comm_map:
                    st.markdown(f"⚠️ **اللجنة رقم {c}** لم يتم رصدها")

    with tab3: # النسخ الاحتياطي
        if st.text_input("رمز حماية النسخ:", type="password") == "4321":
            # الطلاب
            st.markdown("#### 👨‍🎓 بيانات الطلاب")
            df_s = pd.DataFrame(supabase.table('students').select("*").execute().data)
            if not df_s.empty:
                col1, col2 = st.columns(2)
                with col1: st.download_button("📥 الطلاب CSV", df_s.to_csv(index=False).encode('utf-8-sig'), "students_backup.csv", use_container_width=True)
                with col2:
                    buf_s = io.BytesIO()
                    with pd.ExcelWriter(buf_s) as wr: df_s.to_excel(wr, index=False)
                    st.download_button("📊 الطلاب Excel", buf_s.getvalue(), "students_backup.xlsx", use_container_width=True)
            st.divider()
            # المعلمين
            st.markdown("#### 👨‍🏫 بيانات المعلمين")
            df_t = pd.DataFrame(supabase.table('teachers').select("*").execute().data)
            if not df_t.empty:
                col3, col4 = st.columns(2)
                with col3: st.download_button("📥 المعلمين CSV", df_t.to_csv(index=False).encode('utf-8-sig'), "teachers_backup.csv", use_container_width=True)
                with col4:
                    buf_t = io.BytesIO()
                    with pd.ExcelWriter(buf_t) as wr: df_t.to_excel(wr, index=False)
                    st.download_button("📊 المعلمين Excel", buf_t.getvalue(), "teachers_backup.xlsx", use_container_width=True)
