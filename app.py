import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io
from fpdf import FPDF

# ==============================================================================
# 1. إعدادات الاتصال بقاعدة البيانات (Supabase) والتهيئة
# ==============================================================================
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# التهيئة الافتراضية لمتغيرات التحكم بالشاشات
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'teacher' not in st.session_state:
    st.session_state.teacher = None

# --- ضبط إعدادات التطبيق الرسمية ---
st.set_page_config(
    page_title="بصمة تميز - القطيف الثانوية", 
    page_icon="🎯", 
    layout="wide"
)

# --- 🎨 التنسيق المرئي والـ CSS الشامل وتثبيت الهوية الرسمية الموحدة ---
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght=400;700;800&display=swap');
    
    html, body, [class*="css"], p, span, li, a { 
        font-family: 'Cairo', sans-serif !important; 
        direction: rtl; 
        text-align: center !important; 
        font-size: 20px !important; 
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .teacher-tag { background-color: #f0f2f6; color: #1a237e; padding: 6px 12px; border-radius: 15px; font-weight: bold; font-size: 16px !important; border: 1px solid #d1d9e6; display: inline-block; }
    .thank-you-box { text-align: center; padding: 40px; background: #f8fdf9; border-radius: 20px; border: 2px solid #22c55e; margin-top: 20px; }
    
    div.stButton > button { font-size: 22px !important; font-weight: 700 !important; padding: 10px 20px !important; border-radius: 12px !important; }
    .stats-footer-container { margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 12px; border: 1px solid #e9ecef; text-align: center; }
    .stat-badge { display: inline-block; padding: 8px 20px; margin: 5px 10px; font-size: 20px !important; font-weight: bold; border-radius: 8px; color: white; }
    .stat-total { background-color: #1a237e; } .stat-present { background-color: #2e7d32; } .stat-absent { background-color: #c62828; } .stat-late { background-color: #ef6c00; }
    .student-label { font-size: 24px !important; font-weight: 700 !important; color: #1a237e !important; margin-top: 15px; display: block; text-align: right !important; }
    </style>''', unsafe_allow_html=True)

# ==============================================================================
# 2. إدارة ملفات وتقارير الـ PDF الورقية الفردية للطلاب
# ==============================================================================
class ArabicPDF(FPDF):
    def header(self):
        pass
    def footer(self):
        pass

def export_attendance_to_pdf_fpdf(df_row, report_date):
    pdf = ArabicPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_line_width(1.0)
    pdf.set_draw_color(26, 35, 126)
    pdf.rect(5, 5, 200, 287)
    
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "المملكة العربية السعودية - وزارة التعليم", ln=True, align='C')
    pdf.cell(0, 10, "الإدارة العامة للتعليم بالمنطقة الشرقية - مكتب القطيف", ln=True, align='C')
    pdf.cell(0, 10, "مدرسة القطيف الثانوية", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Helvetica", 'B', 18)
    pdf.cell(0, 12, "محضر ضبط انضباط طالب اليومي", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 10, f"التاريخ: {report_date}", ln=True, align='R')
    pdf.cell(0, 10, f"اسم الطالب رباعي: {df_row.get('student_name', '---')}", ln=True, align='R')
    pdf.cell(0, 10, f"الشعبة الدراسية: {df_row.get('الشعبة', '---')}", ln=True, align='R')
    pdf.cell(0, 10, f"رقم اللجنة المرصودة: {df_row.get('committee', '---')}", ln=True, align='R')
    pdf.cell(0, 10, f"حالة الطالب: {df_row.get('status', '---')}", ln=True, align='R')
    pdf.cell(0, 10, f"المعلم الراصد / الملاحظ: {df_row.get('teacher_name', 'لجنة الانضباط')}", ln=True, align='R')
    
    pdf.ln(20)
    pdf.cell(0, 10, "الإجراءات والملاحظات المدرسية:", ln=True, align='R')
    pdf.cell(0, 8, "...........................................................................................................................", ln=True, align='R')
    
    pdf.ln(20)
    pdf.cell(0, 10, "مدير المدرسة: أ. فراس آل عبدالمحسن", ln=True, align='L')
    return pdf.output(dest='S').encode('latin1', errors='ignore')

# --- دالة تصدير ملف الـ Excel ---
def export_attendance_to_excel(df, report_date, sheet_label):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet(f'تقرير {sheet_label}')
        worksheet.right_to_left()
        t_header = workbook.add_format({'font_name': 'Cairo', 'font_size': 11, 'bold': True, 'bg_color': '#1a237e', 'font_color': '#ffffff', 'align': 'center', 'border': 1})
        t_cell = workbook.add_format({'font_name': 'Cairo', 'font_size': 11, 'align': 'center', 'border': 1})
        
        worksheet.write('A1', 'التاريخ', t_header)
        worksheet.write('B1', 'اسم الطالب', t_header)
        worksheet.write('C1', 'الشعبة', t_header)
        worksheet.write('D1', 'اللجنة', t_header)
        worksheet.write('E1', 'الحالة', t_header)
        worksheet.write('F1', 'الملاحظ', t_header)
        
        row_idx = 1
        for _, row in df.iterrows():
            worksheet.write(row_idx, 0, str(report_date), t_cell)
            worksheet.write(row_idx, 1, row['student_name'], t_cell)
            worksheet.write(row_idx, 2, row.get('الشعبة', '---'), t_cell)
            worksheet.write(row_idx, 3, row['committee'], t_cell)
            worksheet.write(row_idx, 4, row['status'], t_cell)
            worksheet.write(row_idx, 5, row.get('teacher_name', 'لجنة الانضباط'), t_cell)
            row_idx += 1
    return output.getvalue()

def confirm_back_dialog():
    st.write("هل أنت متأكد من العودة وإلغاء التغييرات الحالية دون حفظ الرصد؟")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("نعم، إلغاء التغييرات", use_container_width=True, type="primary"):
            st.session_state.page = "home"; st.rerun()
    with c2:
        if st.button("تراجع والبقاء", use_container_width=True): st.rerun()

# ==============================================================================
# 3. معالجة وعرض شاشات التطبيق الرئيسية 
# ==============================================================================

if st.session_state.page == "home":
    # 🌟 كود الـ HTML والـ CSS الكامل المدمج لضمان المعالجة الصحيحة دون أي ظهور للأكواد 🌟
    html_content = """
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght=400;700;900&display=swap');
            
            body {
                margin: 0;
                padding: 0;
                background-color: transparent;
                font-family: 'Cairo', sans-serif;
            }
            
            .main-header { 
                background-color: #1a237e; 
                padding: 45px 20px; 
                text-align: center; 
                color: white; 
                border-radius: 20px; 
                margin-bottom: 20px; 
                border-bottom: 8px solid #ff9800; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            
            .header-subtext {
                color: #ffffff; 
                font-size: 26px; 
                font-weight: 400;
                margin: 5px 0;
                opacity: 0.9;
            }
            
            .system-title {
                color: #ff9800; 
                font-size: 72px; 
                font-weight: 900; 
                margin: 10px 0;
                text-shadow: 2px 2px 6px rgba(0,0,0,0.4);
            }

            .school-name {
                color: #ffffff;
                font-size: 34px; 
                font-weight: 700;
                margin: 5px 0 25px 0;
            }

            .role-title {
                color: #ffffff;
                font-size: 24px;
                font-weight: 400;
                margin-top: 20px;
                margin-bottom: 2px;
                opacity: 0.85;
            }

            .person-name {
                color: #ff9800;
                font-size: 38px;
                font-weight: 800;
                margin-top: 2px;
                margin-bottom: 15px;
                text-shadow: 1px 1px 4px rgba(0,0,0,0.3);
            }
        </style>
    </head>
    <body>
        <div class="main-header">
            <div class="header-subtext">أول خطوة للنجاح...التحضير</div>
            <div class="system-title">بَصمَة تَميُز</div>
            <div class="school-name">مدرسة القطيف الثانوية</div>
            
            <div class="role-title">مدير المدرسة</div>
            <div class="person-name">أ. فراس آل عبدالمحسن</div>
            
            <div class="role-title">فكرة وبرمجة</div>
            <div class="person-name">أ. عارف أحمد الحداد</div>
        </div>
    </body>
    </html>
    """
    
    # استدعاء دالة المكونات الحية المضمونة لمعالجة الـ HTML وعرض الهوية الرسمية بدقة واحترافية
    components.html(html_content, height=620, scrolling=False)
    
    # أزرار الانتقال والتحكم للشاشة الرئيسية
    st.write("")
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        if st.button("📝 رصد غياب الطلاب اليومي", use_container_width=True, type="primary"):
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⏰ لجنة التأخر الصباحي", use_container_width=True):
            st.session_state.page = "m_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة", use_container_width=True):
            st.session_state.page = "a_log"; st.rerun()

elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "mark"; st.rerun()
        else: st.error("السجل المدني غير مسجل.")

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
            count_present, count_absent, count_late = 0, 0, 0
            count_total = len(students.data)
            
            for s in students.data:
                prev = old_map.get(s['student_name'], "حاضر")
                class_info = s.get('class_name', '---')
                st.markdown(f'<span class="student-label">👤 {s["student_name"]} ({class_info})</span>', unsafe_allow_html=True)
                choice = st.radio("", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['student_name'], horizontal=True, label_visibility="collapsed")
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": all_t})
                if choice == "حاضر": count_present += 1
                elif choice == "غائب": count_absent += 1
                elif choice == "متأخر": count_late += 1
            
            st.write("")
            col_save, col_back = st.columns(2)
            with col_save:
                if st.button("💾 حفظ الرصد النهائي", use_container_width=True, type="primary"):
                    supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                    supabase.table('attendance').insert(results).execute()
                    st.session_state.page = "thank_you"; st.rerun()
            with col_back:
                if st.button("⬅️ عودة بدون حفظ", use_container_width=True): confirm_back_dialog()
            
            st.markdown(f'<div class="stats-footer-container"><span class="stat-badge stat-total">المجموع ( {count_total} )</span><span class="stat-badge stat-present">حاضر ( {count_present} )</span><span class="stat-badge stat-absent">غائب ( {count_absent} )</span><span class="stat-badge stat-late">متأخر ( {count_late} )</span></div>', unsafe_allow_html=True)

elif st.session_state.page == "m_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("أدخل كلمة مرور لجنة التأخر الصباحي:", type="password") == "112233":
        st.session_state.page = "morning_late"; st.rerun()

elif st.session_state.page == "morning_late":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    st.markdown("## ⏰ لجنة رصد التأخر الصباحي الموحد")
    today = str(datetime.now().date())
    
    res_all_students = supabase.table('students').select("class_name").execute()
    if res_all_students.data:
        df_std_classes = pd.DataFrame(res_all_students.data)
        all_classes = sorted(list(df_std_classes['class_name'].unique()))
        grades_map = {"أول ثانوي": "1", "ثاني ثانوي": "2", "ثالث ثانوي": "3"}
        selected_grade_label = st.selectbox("اختر الصف الدراسي:", ["---"] + list(grades_map.keys()))
        
        if selected_grade_label != "---":
            grade_prefix = grades_map[selected_grade_label]
            filtered_classes = [c for c in all_classes if str(c).startswith(grade_prefix)]
            selected_class = st.selectbox("اختر الشعبة:", ["---"] + filtered_classes)
            
            if selected_class != "---":
                students_in_class = supabase.table('students').select("*").eq("class_name", selected_class).execute()
                if students_in_class.data:
                    all_today_attendance = supabase.table('attendance').select("*").eq("date", today).execute()
                    att_map, tech_map = {}, {}
                    for att in all_today_attendance.data:
                        att_map[att['student_name']] = att['status']
                        tech_map[att['student_name']] = att['teacher_name']
                    
                    morning_results = []
                    for s in students_in_class.data:
                        s_name = s['student_name']
                        current_status = att_map.get(s_name, "حاضر")
                        final_teachers = tech_map.get(s_name, "لجنة التأخر الصباحي")
                        if "لجنة التأخر الصباحي" not in final_teachers: final_teachers = f"{final_teachers} | لجنة التأخر الصباحي"
                        
                        st.markdown(f'<span class="student-label">👤 {s_name}</span>', unsafe_allow_html=True)
                        choice = st.radio("", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(current_status), key=f"m_{s_name}", horizontal=True, label_visibility="collapsed")
                        morning_results.append({"student_name": s_name, "committee": str(s.get('committee','1')), "status": choice, "date": today, "teacher_name": final_teachers})
                    
                    if st.button("💾 اعتماد وتحديث رصد التأخر الصباحي", type="primary", use_container_width=True):
                        for record in morning_results:
                            supabase.table('attendance').delete().eq("student_name", record['student_name']).eq("date", today).execute()
                        supabase.table('attendance').insert(morning_results).execute()
                        st.success("✅ تم التزامن والحفظ بنجاح!")
                        time.sleep(1); st.rerun()

elif st.session_state.page == "thank_you":
    st.snow()
    st.markdown(f'<div class="thank-you-box"><h1>✅ تم الرصد بنجاح</h1><h2>أ. {st.session_state.get("teacher", "")}</h2></div>', unsafe_allow_html=True)
    if st.button("🏠 العودة للرئيسية", use_container_width=True): st.session_state.page = "home"; st.rerun()

elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("أدخل كلمة مرور الإدارة:", type="password") == "1234": st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 تقارير الانضباط والطباعة", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1:
        d_rep = st.date_input("اختر تاريخ التقرير:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d_rep)).execute()
        
        if res_att.data:
            df_all = pd.DataFrame(res_att.data)
            res_std = supabase.table("students").select("student_name, class_name").execute()
            s_map = dict(zip([i['student_name'] for i in res_std.data], [i['class_name'] for i in res_std.data]))
            df_all['الشعبة'] = df_all['student_name'].map(s_map).fillna("---")
            
            st.markdown("### 💾 ترحيل الكشوفات والتقارير الموحدة")
            c_excel_a, c_excel_l = st.columns(2)
            with c_excel_a:
                df_abs = df_all[df_all['status'] == 'غائب']
                if not df_abs.empty:
                    st.download_button("🚫 ترحيل كشف الغياب إلى Excel", export_attendance_to_excel(df_abs, d_rep, "الغياب"), f"Absent_{d_rep}.xlsx", use_container_width=True)
            with c_excel_l:
                df_lat = df_all[df_all['status'] == 'متأخر']
                if not df_lat.empty:
                    st.download_button("⏳ ترحيل كشف التأخر إلى Excel", export_attendance_to_excel(df_lat, d_rep, "التأخر"), f"Late_{d_rep}.xlsx", use_container_width=True)
            
            st.markdown("### 🖨️ طباعة محاضر وإشعارات الطلاب الفردية (PDF)")
            selected_student_report = st.selectbox("اختر الطالب المراد إصدار محضر رسمي له:", ["---"] + list(df_all['student_name'].unique()))
            if selected_student_report != "---":
                row_student = df_all[df_all['student_name'] == selected_student_report].iloc[0].to_dict()
                pdf_data = export_attendance_to_pdf_fpdf(row_student, d_rep)
                st.download_button(
                    label=f"📄 طباعة محضر انضباط الطالب ({selected_student_report}) PDF",
                    data=pdf_data,
                    file_name=f"محضر_{selected_student_report}_{d_rep}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            st.write("---")
            st.dataframe(df_all[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']], use_container_width=True)
        else:
            st.info("لا توجد بيانات مسجلة لهذا التاريخ.")
            
    with tab2:
        st.write("واجهة متابعة اللجان اللحظية تعمل ومستقرة.")
    with tab3:
        st.write("لوحة البيانات وتحديث ملفات الرفع تعمل ومستقرة.")
