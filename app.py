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

# --- 🎨 التنسيق المرئي المطور ---
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
    .thank-you-card {
        text-align: center; padding: 50px; background: white; border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1); border: 2px solid #1a237e; margin-top: 50px;
    }
    .teacher-badge {
        background-color: #f1f3f9; padding: 2px 8px; border-radius: 5px; color: #1a237e; font-size: 14px; font-weight: bold; border: 1px solid #d1d9e6;
    }
    </style>
''', unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "home"

# --- 🛠️ دالة بناء رسالة الواتساب ---
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

# --- 1. الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown(f'''
        <div class="main-header">
            <h1 style="margin:0; font-size: 35px;">التحضير التقني</h1>
            <h2 style="margin:0; font-size: 28px;">مدرسة القطيف الثانوية</h2>
            <p style="color:#ffd700; font-size:22px; margin-top:10px; font-weight: bold;">برمجة: أ. عارف أحمد الحداد</p>
            <div style="font-size: 20px; margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 10px;">
                مدير المدرسة: أ. فراس آل عبدالمحسن
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
                # الحذف والإضافة يضمنان تسجيل الاسم الجديد في السجل
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.balloons()
                st.session_state.page = "thank_you"; st.rerun()

# --- 4. صفحة الشكر ---
elif st.session_state.page == "thank_you":
    st.markdown(f'''
        <div class="thank-you-card">
            <h1 style="color: #22c55e; font-size: 50px;">👏 شكراً لك</h1>
            <h2 style="color: #1a237e;">الأستاذ: {st.session_state.get('teacher', 'المعلم')}</h2>
            <p style="font-size: 20px;">تم حفظ رصد الطلاب بنجاح في قاعدة البيانات السحابية.</p>
        </div>
    ''', unsafe_allow_html=True)
    if st.button("🏠 العودة لصفحة البداية", use_container_width=True, type="primary"):
        st.session_state.page = "home"; st.rerun()

# --- 5. قسم الإدارة ---
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
            
            report_df = df_all[df_all['status'].isin(['غائب', 'متأخر'])][['committee', 'student_name', 'الشعبة', 'status']]
            report_df.columns = ['اللجنة', 'اسم الطالب', 'الشعبة', 'الحالة']
            st.dataframe(report_df, use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns(2)
            with c1:
                link_abs = get_wa_link(df_all[df_all['status'] == "غائب"], "الغائبين", d)
                if link_abs: st.markdown(f'<a href="{link_abs}" target="_blank" class="wa-link wa-absent">🚫 إرسال الغائبين</a>', unsafe_allow_html=True)
            with c2:
                link_late = get_wa_link(df_all[df_all['status'] == "متأخر"], "المتأخرين", d)
                if link_late: st.markdown(f'<a href="{link_late}" target="_blank" class="wa-link wa-late">⏳ إرسال المتأخرين</a>', unsafe_allow_html=True)

    with tab2:
        st.subheader("🏘️ متابعة سجل تحضير اللجان اليوم")
        # جلب كافة عمليات التحضير لليوم
        att_today = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        
        # تجميع أسماء المعلمين لكل لجنة للحفاظ على الترتيب
        done_dict = {}
        for i in att_today.data:
            com = str(i['committee'])
            t_name = i['teacher_name']
            if com not in done_dict:
                done_dict[com] = []
            if t_name not in done_dict[com]:
                done_dict[com].append(t_name)
        
        res_s = supabase.table('students').select("committee").execute()
        all_c = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
        
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ لجان تم رصدها (بالترتيب)")
            for c in all_c:
                if c in done_dict:
                    # عرض القائمة من الأول إلى الأخير
                    teachers_list = " ⬅️ ".join(done_dict[c])
                    st.markdown(f"📍 **لجنة {c}**: <span class='teacher-badge'>{teachers_list}</span>", unsafe_allow_html=True)
        with c2:
            st.error("❌ لجان لم تُرصد")
            for c in all_c:
                if c not in done_dict:
                    st.write(f"⚠️ لجنة {c}")

    with tab3:
        pwd = st.text_input("أدخل رمز البيانات (4321):", type="password")
        if pwd == "4321":
            st.subheader("🗑️ حذف تحضير تاريخ محدد")
            del_date = st.date_input("اختر التاريخ:", datetime.now(), key="del_date")
            if st.button("❌ حذف السجلات"):
                supabase.table('attendance').delete().eq("date", str(del_date)).execute()
                st.warning(f"تم الحذف لتاريخ {del_date}")
            st.divider()
            res_bk = supabase.table('students').select("*").execute()
            if res_bk.data:
                df_bk = pd.DataFrame(res_bk.data)
                col_csv, col_xlsx = st.columns(2)
                with col_csv:
                    st.download_button("📥 تحميل CSV", df_bk.to_csv(index=False).encode('utf-8-sig'), "students.csv", use_container_width=True)
                with col_xlsx:
                    out = io.BytesIO()
                    with pd.ExcelWriter(out, engine='openpyxl') as wr: df_bk.to_excel(wr, index=False)
                    st.download_button("📊 تحميل Excel", out.getvalue(), "students.xlsx", use_container_width=True)
            up = st.file_uploader("تحديث الطلاب:")
            if up and st.button("🚀 رفع"):
                df_new = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                supabase.table('students').delete().neq('committee', '0').execute()
                supabase.table('students').insert(df_new.to_dict('records')).execute()
                st.success("تم التحديث!")
