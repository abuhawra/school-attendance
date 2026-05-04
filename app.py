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

# --- ⚙️ نظام التحكم في حالة النظام (فتح/إغلاق الرصد) ---
if 'system_open' not in st.session_state:
    st.session_state.system_open = True

# --- 🎨 التنسيق المرئي والـ CSS ---
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stDataFrame { width: 100% !important; }
    .wa-link { text-decoration: none; color: white !important; display: block; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 10px; font-size: 18px; }
    .wa-absent { background-color: #dc3545; }
    .wa-late { background-color: #fd7e14; }
    .main-header { 
        background-color: #1a237e; padding: 30px; text-align: center; color: white; 
        border-radius: 20px; margin-bottom: 25px; border-bottom: 8px solid #ffd700; 
    }
    .teacher-tag { background-color: #f0f2f6; color: #1a237e; padding: 4px 10px; border-radius: 8px; font-weight: bold; font-size: 14px; border: 1px solid #d1d9e6; margin-left: 5px; margin-bottom: 5px; display: inline-block; }
    .thank-you-card { text-align: center; padding: 40px; background: white; border-radius: 15px; border: 2px solid #22c55e; margin-top: 20px; }
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
    c_img1, c_img2, c_img3 = st.columns([1, 0.8, 1])
    with c_img2:
        try: st.image("logo.png", use_container_width=True)
        except: pass

    st.markdown(f'''
        <div class="main-header">
            <h2 style="color:#ffd700; font-size: 50px; font-weight: 800;">بصمة تميز</h2>
            <h2 style="margin:0; font-size: 18px; opacity: 0.9;">التحضير أولى خطوات النجاح</h2>
            <h2 style="margin:15px 0; font-size: 28px;">مدرسة القطيف الثانوية</h2>
            <div style="font-size: 22px; margin-top: 22px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 22px;">
                <h3 style="margin:0; font-size: 20px;">مدير المدرسة</h3>
                <h2 style="color:#ffd700; font-size: 24px;">أ. فراس آل عبدالمحسن</h2>
            </div>
            <div style="font-size: 22px; margin-top: 15px;">
                <h3 style="margin:0; font-size: 18px;">فكرة وبرمجة</h3>
                <h2 style="color:#ffd700; font-size: 24px;">أ. عارف أحمد الحداد</h2>
                <h5 style="margin:5px 0; font-size: 16px; opacity: 0.7;">2026</h5>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        # زر الرصد المتغير بناءً على حالة النظام
        if st.session_state.system_open:
            if st.button("📝 رصد غياب الطلاب اليومي", use_container_width=True, type="primary"):
                st.session_state.page = "t_log"; st.rerun()
        else:
            st.button("🔒 النظام مغلق: يفتح الرصد 7:10 ص", use_container_width=True, disabled=True)
            st.caption("<center>عذراً، الرصد متاح فقط خلال الفترة الصباحية المحددة.</center>", unsafe_allow_html=True)
        
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
            old_map = {i['student_name']: i['status'] for i in old_att.data}
            
            prev_t = list(set([i['teacher_name'] for i in old_att.data if i.get('teacher_name')]))
            all_t = " | ".join(prev_t + [st.session_state.teacher]) if st.session_state.teacher not in prev_t else " | ".join(prev_t)

            results = []
            for s in students.data:
                prev = old_map.get(s['student_name'], "حاضر")
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['student_name'], horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": all_t})
            
            if st.button("💾 حفظ الرصد النهائي", use_container_width=True):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.session_state.page = "thank_you"; st.rerun()

# --- 4. صفحة الشكر (لحل مشكلة الاختفاء) ---
elif st.session_state.page == "thank_you":
    st.snow()
    st.markdown(f'''
        <div class="thank-you-card">
            <h1 style="color: #22c55e;">✅ تم الرصد بنجاح</h1>
            <p style="font-size: 20px;">شكراً لك أستاذ <b>{st.session_state.get('teacher', '')}</b></p>
            <p>تم تحديث بيانات اللجنة في النظام المركزي للمدرسة.</p>
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
    tab1, tab2, tab3 = st.tabs(["📊 تقارير الواتساب", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1: # التقارير
        d = st.date_input("تاريخ التقرير:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res_att.data:
            df_all = pd.DataFrame(res_att.data)
            res_std = supabase.table("students").select("student_name, class_name").execute()
            s_map = dict(zip([i['student_name'] for i in res_std.data], [i['class_name'] for i in res_std.data]))
            df_all['الشعبة'] = df_all['student_name'].map(s_map).fillna("---")
            report_df = df_all[df_all['status'].isin(['غائب', 'متأخر'])].copy()
            report_df['committee_sort'] = pd.to_numeric(report_df['committee'], errors='coerce').fillna(0)
            report_df = report_df.sort_values(by='committee_sort')
            st.dataframe(report_df[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee':'اللجنة','student_name':'الطالب','status':'الحالة','teacher_name':'المعلمون'}), use_container_width=True, hide_index=True)
            c1, c2 = st.columns(2)
            with c1:
                link_abs = get_wa_link(df_all[df_all['status'] == "غائب"], "الغائبين", d)
                if link_abs: st.markdown(f'<a href="{link_abs}" target="_blank" class="wa-link wa-absent">🚫 إرسال الغائبين</a>', unsafe_allow_html=True)
            with c2:
                link_late = get_wa_link(df_all[df_all['status'] == "متأخر"], "المتأخرين", d)
                if link_late: st.markdown(f'<a href="{link_late}" target="_blank" class="wa-link wa-late">⏳ إرسال المتأخرين</a>', unsafe_allow_html=True)

    with tab2: # حالة اللجان
        st.subheader("🏘️ حالة رصد اللجان اليوم")
        att_today = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        comm_map = {}
        for row in att_today.data:
            c = str(row['committee'])
            for name in row['teacher_name'].split(" | "):
                if c not in comm_map: comm_map[c] = set()
                comm_map[c].add(name.strip())
        res_s = supabase.table('students').select("committee").execute()
        all_c = sorted(list(set([str(i['committee']) for i in res_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ تم الرصد")
            for c in all_c:
                if c in comm_map:
                    names_html = "".join([f"<span class='teacher-tag'>{n}</span>" for n in comm_map[c]])
                    st.markdown(f"📍 **لجنة {c}:** {names_html}", unsafe_allow_html=True)
        with c2:
            st.error("❌ لم تُرصد")
            for c in all_c:
                if c not in comm_map: st.write(f"⚠️ لجنة {c}")

    with tab3: # إدارة البيانات والتحكم في النظام
        if st.text_input("رمز حماية البيانات:", type="password") == "4321":
            
            # --- 🔑 زر التحكم في حالة الرصد ---
            st.subheader("🔒 التحكم في صلاحية الرصد")
            if st.session_state.system_open:
                if st.button("إغلاق نظام الرصد الآن", use_container_width=True, type="secondary"):
                    st.session_state.system_open = False
                    st.rerun()
            else:
                if st.button("فتح نظام الرصد الآن", use_container_width=True, type="primary"):
                    st.session_state.system_open = True
                    st.rerun()
            st.caption("عند الإغلاق، سيظهر زر 'النظام مغلق' في الواجهة الرئيسية ولن يتمكن المعلمون من الدخول.")
            st.divider()

            # إدارة المعلمين والطلاب
            st.subheader("👨‍🏫 المعلمين")
            res_t = supabase.table('teachers').select("*").execute()
            if res_t.data:
                df_t = pd.DataFrame(res_t.data)
                col1, col2 = st.columns(2)
                with col1: st.download_button("📥 CSV المعلمين", df_t.to_csv(index=False).encode('utf-8-sig'), "teachers.csv", use_container_width=True)
                with col2:
                    buf_t = io.BytesIO()
                    with pd.ExcelWriter(buf_t, engine='openpyxl') as wr: df_t.to_excel(wr, index=False)
                    st.download_button("📊 Excel المعلمين", buf_t.getvalue(), "teachers.xlsx", use_container_width=True)
            
            st.divider()
            st.subheader("👨‍🎓 الطلاب")
            res_s = supabase.table('students').select("*").execute()
            if res_s.data:
                df_s = pd.DataFrame(res_s.data)
                col1, col2 = st.columns(2)
                with col1: st.download_button("📥 CSV الطلاب", df_s.to_csv(index=False).encode('utf-8-sig'), "students.csv", use_container_width=True)
                with col2:
                    buf_s = io.BytesIO()
                    with pd.ExcelWriter(buf_s, engine='openpyxl') as wr: df_s.to_excel(wr, index=False)
                    st.download_button("📊 Excel الطلاب", buf_s.getvalue(), "students.xlsx", use_container_width=True)

            st.divider()
            st.subheader("🗑️ تنظيف السجلات")
            del_date = st.date_input("اختر تاريخاً لحذفه:", datetime.now())
            if st.button("❌ تأكيد حذف سجلات اليوم"):
                supabase.table('attendance').delete().eq("date", str(del_date)).execute()
                st.warning(f"تم حذف سجلات يوم {del_date}")
