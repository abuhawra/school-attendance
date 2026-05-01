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

# --- 🎨 التنسيق المرئي الكامل ---
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .wa-link { text-decoration: none; color: white !important; display: block; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 10px; font-size: 18px; }
    .wa-absent { background-color: #dc3545; }
    .wa-late { background-color: #fd7e14; }
    .main-header { 
        background-color: #1a237e; 
        padding: 40px 20px; 
        text-align: center; 
        color: white; 
        border-radius: 20px; 
        margin-bottom: 30px; 
        border-bottom: 8px solid #ffd700; 
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    .header-title { font-size: 42px; font-weight: 800; margin: 0; }
    .header-subtitle { font-size: 32px; font-weight: 700; margin: 5px 0 20px 0; color: #ffffff; }
    .header-info { font-size: 22px; color: #ffd700; font-weight: bold; margin: 5px 0; }
    .header-manager { font-size: 24px; color: #ffffff; font-weight: 700; margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 15px; }
    </style>
''', unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "home"

# --- 🛠️ دالة بناء رسالة الواتساب المنسقة ---
def get_wa_link(df, status_type, d):
    if df.empty: return None
    header_emoji = "🚫" if "غائب" in status_type else "⏳"
    msg = f"{header_emoji} *قائمة {status_type}*%0A"
    msg += f"📅 *التاريخ:* {d}%0A"
    msg += "-----------------%0A"
    for _, r in df.iterrows():
        msg += f"📦 *اللجنة :* {r['committee']}%0A"
        msg += f"👤 *الاسم:* {r['student_name']}%0A"
        msg += f"🏫 *الشعبة:* {r.get('الشعبة','--')}%0A"
        msg += f"⚠️ *الحالة:* {r['status']}%0A"
        msg += "-----------------%0A" 
    return f"https://wa.me/?text={msg}"

# --- الصفحة الرئيسية (الغلاف المحدث) ---
if st.session_state.page == "home":
    st.markdown(f'''
        <div class="main-header">
            <div class="header-title">التحضير التقني</div>
            <div class="header-subtitle">مدرسة القطيف الثانوية</div>
            <div class="header-info">برمجة: أ. عارف أحمد الحداد</div>
            <div class="header-manager">
                <span style="color: #cfd8dc; font-weight: 400; font-size: 20px;">مدير المدرسة</span><br>
                أ. فراس آل عبدالمحسن
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    col_b = st.columns([1, 1.8, 1])[1]
    with col_b:
        if st.button("📝 رصد غياب الطلاب اليومي", use_container_width=True, type="primary"):
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة", use_container_width=True):
            st.session_state.page = "a_log"; st.rerun()

# --- قسم المعلم ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
    if st.button("دخول"):
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
            if st.button("💾 حفظ الرصد النهائي", use_container_width=True):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("تم الحفظ بنجاح!"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- قسم الإدارة ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": 
        st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 تقارير الواتساب", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1:
        d = st.date_input("تاريخ التقرير:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res_att.data:
            df_all = pd.DataFrame(res_att.data)
            res_std = supabase.table("students").select("student_name, class_name").execute()
            s_map = dict(zip([i['student_name'] for i in res_std.data], [i['class_name'] for i in res_std.data]))
            df_all['الشعبة'] = df_all['student_name'].map(s_map).fillna("---")
            st.dataframe(df_all[df_all['status'].isin(['غائب', 'متأخر'])][['committee', 'student_name', 'الشعبة', 'status']], use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                l_abs = get_wa_link(df_all[df_all['status'] == "غائب"], "الغائبين", d)
                if l_abs: st.markdown(f'<a href="{l_abs}" target="_blank" class="wa-link wa-absent">🚫 إرسال الغائبين</a>', unsafe_allow_html=True)
            with c2:
                l_late = get_wa_link(df_all[df_all['status'] == "متأخر"], "المتأخرين", d)
                if l_late: st.markdown(f'<a href="{l_late}" target="_blank" class="wa-link wa-late">⏳ إرسال المتأخرين</a>', unsafe_allow_html=True)

    with tab2:
        st.subheader("🏘️ حالة رصد اللجان اليوم")
        att_today = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        done_dict = {str(i['committee']): i['teacher_name'] for i in att_today.data}
        res_s = supabase.table('students').select("committee").execute()
        all_c = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ لجان تم رصدها")
            for c in all_c:
                if c in done_dict: st.write(f"📍 **لجنة {c}** - (المعلم: {done_dict[c]})")
        with c2:
            st.error("❌ لجان لم تُرصد بعد")
            for c in all_c:
                if c not in done_dict: st.write(f"⚠️ **لجنة {c}**")

    with tab3:
        pwd = st.text_input("أدخل رمز إدارة البيانات للوصول:", type="password")
        if pwd == "4321":
            st.success("تم تأكيد الرمز.")
            res_bk = supabase.table('students').select("*").execute()
            if res_bk.data:
                df_bk = pd.DataFrame(res_bk.data)
                col_csv, col_xlsx = st.columns(2)
                with col_csv:
                    st.download_button("📥 تحميل نسخة CSV", df_bk.to_csv(index=False).encode('utf-8-sig'), "students.csv", use_container_width=True)
                with col_xlsx:
                    out = io.BytesIO()
                    with pd.ExcelWriter(out, engine='openpyxl') as wr: df_bk.to_excel(wr, index=False)
                    st.download_button("📊 تحميل نسخة Excel", out.getvalue(), "students.xlsx", use_container_width=True)
            st.divider()
            up = st.file_uploader("رفع ملف تحديث بيانات الطلاب:")
            if up and st.button("🚀 تحديث قاعدة البيانات الآن"):
                df_new = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                supabase.table('students').delete().neq('committee', '0').execute()
                supabase.table('students').insert(df_new.to_dict('records')).execute()
                st.success("تم التحديث بنجاح!")
