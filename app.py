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
    .stDataFrame { width: 100% !important; }
    .wa-link { text-decoration: none; color: white !important; display: block; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 10px; font-size: 18px; }
    .wa-absent { background-color: #dc3545; }
    .wa-late { background-color: #fd7e14; }
    .main-header { 
        background-color: #1a237e; padding: 30px; text-align: center; color: white; 
        border-radius: 20px; margin-bottom: 25px; border-bottom: 8px solid #ffd700; 
    }
    .teacher-tag { background-color: #f0f2f6; color: #1a237e; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 13px; border: 1px solid #d1d9e6; margin-left: 5px; margin-bottom: 5px; display: inline-block; }
    .arrow-sep { color: #1a237e; font-weight: bold; margin: 0 5px; font-size: 18px; }
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
            <h2 style="color:#ffd700; font-size: 50px; font-weight: 800;">بصمة تميز</h2>
            <h2 style="margin:15px 0; font-size: 28px;">مدرسة القطيف الثانوية</h2>
            <div style="font-size: 22px; margin-top: 22px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 22px;">
                <h3 style="margin:0; font-size: 20px;">مدير المدرسة: أ. فراس آل عبدالمحسن</h3>
                <h3 style="margin:5px 0; font-size: 18px;">برمجة: أ. عارف أحمد الحداد</h3>
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
            
            if old_att.data:
                prev_list = []
                for entry in old_att.data:
                    for n in entry.get('teacher_name', '').split(" | "):
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
    st.success("✅ تم الرصد بنجاح")
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
    
    with tab1:
        d = st.date_input("اختر التاريخ المطلوب:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        
        if res_att.data:
            df_all = pd.DataFrame(res_att.data)
            
            # --- إضافة زر الحذف هنا ---
            with st.expander("⚠️ منطقة الحذف (إجراء خطير)"):
                st.warning(f"هل أنت متأكد من رغبتك في حذف جميع بيانات الرصد لتاريخ {d}؟")
                if st.button(f"🗑️ حذف رصد يوم {d} نهائياً", use_container_width=True):
                    supabase.table("attendance").delete().eq("date", str(d)).execute()
                    st.success(f"تم حذف بيانات يوم {d} بنجاح.")
                    st.rerun()
            
            st.divider()
            
            # عرض التقارير كالمعتاد
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
        else:
            st.info("لا توجد بيانات رصد لهذا التاريخ.")

    with tab2: # حالة اللجان
        st.subheader("🏘️ حالة رصد اللجان اليوم")
        att_today = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        comm_map = {}
        for row in att_today.data:
            c = str(row['committee'])
            if c not in comm_map:
                names = [n.strip() for n in row['teacher_name'].split(" | ") if n.strip()]
                seen = set()
                comm_map[c] = [x for x in names if not (x in seen or seen.add(x))]
        
        res_s = supabase.table('students').select("committee").execute()
        all_c = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
        for c in all_c:
            if c in comm_map:
                html = "".join([f"<span class='teacher-tag'>{n}</span>" + ("<span class='arrow-sep'>⬅️</span>" if i < len(comm_map[c])-1 else "") for i, n in enumerate(comm_map[c])])
                st.markdown(f"📍 **لجنة {c}:** {html}", unsafe_allow_html=True)

    with tab3: # إدارة البيانات
        if st.text_input("رمز حماية البيانات:", type="password") == "4321":
            st.subheader("💾 النسخ الاحتياطي")
            res_std = supabase.table('students').select("*").execute()
            if res_std.data:
                df_s = pd.DataFrame(res_std.data)
                col1, col2 = st.columns(2)
                with col1: st.download_button("📥 تحميل الطلاب CSV", df_s.to_csv(index=False).encode('utf-8-sig'), "students.csv", use_container_width=True)
                with col2:
                    buf_s = io.BytesIO()
                    with pd.ExcelWriter(buf_s, engine='openpyxl') as wr: df_s.to_excel(wr, index=False)
                    st.download_button("📊 تحميل الطلاب Excel", buf_s.getvalue(), "students.xlsx", use_container_width=True)
