import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io

# مكتبات معالجة النصوص العربية وتوليد الـ PDF المستقرة
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

# 1. إعدادات الاتصال بقاعدة البيانات (Supabase)
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# --- 🎯 2. ضبط إعدادات التطبيق الرسمية ---
st.set_page_config(
    page_title="بصمة تميز - القطيف الثانوية", 
    page_icon="🎯", 
    layout="wide"
)

# --- 📱 3. حقن ملفات الـ PWA تلقائياً عبر الجافاسكريبت ---
pwa_js = """
<script>
const manifest = {
  "short_name": "بصمة تميز",
  "name": "بصمة تميز - القطيف الثانوية",
  "icons": [
    {
      "src": "https://img.icons8.com/emoji/96/bullseye.png",
      "type": "image/png",
      "sizes": "96x96"
    },
    {
      "src": "https://img.icons8.com/emoji/512/bullseye.png",
      "type": "image/png",
      "sizes": "512x512"
    }
  ],
  "start_url": "/",
  "background_color": "#1a237e",
  "theme_color": "#1a237e",
  "display": "standalone",
  "orientation": "portrait"
};

const stringManifest = JSON.stringify(manifest);
const blob = new Blob([stringManifest], {type: 'application/json'});
const manifestURL = URL.createObjectURL(blob);
let link = document.createElement('link');
link.rel = 'manifest';
link.href = manifestURL;
document.head.appendChild(link);

if ('serviceWorker' in navigator) {
  const swCode = `
    self.addEventListener('install', function(e) { self.skipWaiting(); });
    self.addEventListener('fetch', function(e) { e.respondWith(fetch(e.request)); });
  `;
  const swBlob = new Blob([swCode], {type: 'application/javascript'});
  const swURL = URL.createObjectURL(swCode);
  navigator.serviceWorker.register(swURL).then(function() {
    console.log('PWA Service Worker Registered Successfully.');
  }).catch(function(error) {
    console.log('Service Worker Registration Failed:', error);
  });
}
</script>
"""
st.markdown(pwa_js, unsafe_allow_html=True)

# --- 🎨 التنسيق المرئي والـ CSS ---
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Cairo', sans-serif; 
        direction: rtl; 
        text-align: right; 
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
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
    .wa-stats { background-color: #1a237e; border: 1px solid #ff9800; }
    .thank-you-box { text-align: center; padding: 40px; background: #f8fdf9; border-radius: 20px; border: 2px solid #22c55e; margin-top: 20px; }
    
    .stats-footer-container {
        margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 12px; border: 1px solid #e9ecef; text-align: center;
    }
    .stat-badge {
        display: inline-block; padding: 8px 20px; margin: 5px 10px; font-size: 18px; font-weight: bold; border-radius: 8px; color: white;
    }
    .stat-total { background-color: #1a237e; }
    .stat-present { background-color: #2e7d32; }
    .stat-absent { background-color: #c62828; }
    .stat-late { background-color: #ef6c00; }
    
    .admin-grade-box {
        background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .admin-grade-title { font-size: 18px; font-weight: bold; color: #1a237e; margin-bottom: 10px; border-bottom: 2px solid #ff9800; padding-bottom: 5px; }
    .grade-stat-sub { font-size: 15px; font-weight: 700; margin: 4px 0; }
    </style>
''', unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "home"

# --- 🛠️ دالات مساعدة وجلب الأسماء النظيفة ---

def get_clean_observer_string(raw_teacher_name, valid_teachers_set):
    if not raw_teacher_name:
        return "لجنة الانضباط"
    current_list = []
    for name in str(raw_teacher_name).split(" | "):
        clean_name = name.strip()
        if clean_name and clean_name not in current_list:
            if clean_name in valid_teachers_set or clean_name == "لجنة التأخر الصباحي":
                current_list.append(clean_name)
            else:
                matched = [real_name for real_name in valid_teachers_set if clean_name in real_name]
                if matched:
                    if matched[0] not in current_list: current_list.append(matched[0])
                else:
                    current_list.append(clean_name)
    return " | ".join(current_list) if current_list else "لجنة الانضباط"

def get_wa_link(df, status_type, d):
    if df.empty: return None
    df_sorted = df.copy()
    df_sorted['c_sort'] = pd.to_numeric(df_sorted['committee'], errors='coerce').fillna(0)
    df_sorted = df_sorted.sort_values(by='c_sort')
    header_emoji = "🚫" if "غائب" in status_type else "⏳"
    msg = f"{header_emoji} *قائمة {status_type}*%0A📅 *التاريخ:* {d}%0A-----------------%0A"
    for _, r in df_sorted.iterrows():
        msg += (
            f"📦 *اللجنة:* {r['committee']}%0A"
            f"👤 *الاسم:* {r['student_name']}%0A"
            f"🏫 *الشعبة:* {r.get('الشعبة','--')}%0A"
            f"⚠️ *الحالة:* {r['status']}%0A"
            f"-----------------%0A"
        )
    return f"https://wa.me/?text={msg}"

def get_wa_grade_stats_link(d, g1_a, g1_l, g2_a, g2_l, g3_a, g3_l):
    msg = (
        f"📊 *إحصائيات الانضباط التفصيلية للمراحل*%0A"
        f"📅 *التاريخ:* {d}%0A"
        f"-----------------%0A"
        f"🏫 *الصف أول ثانوي:*%0A"
        f"🚫 الغائبين: {g1_a}%0A"
        f"⏳ المتأخرين: {g1_l}%0A%0A"
        f"🏫 *الصف ثاني ثانوي:*%0A"
        f"🚫 الغائبين: {g2_a}%0A"
        f"⏳ المتأخرين: {g2_l}%0A%0A"
        f"🏫 *الصف third ثانوي:*%0A"
        f"🚫 الغائبين: {g3_a}%0A"
        f"⏳ المتأخرين: {g3_l}%0A%0A"
        f"-----------------%0A"
        f"🎯 *تم الإرسال عبر نظام بصمة تميز*"
    )
    return f"https://wa.me/?text={msg}"

# دالة توليد ملف إكسيل
def export_attendance_to_excel(df, report_date, sheet_label, valid_teachers_set):
    days_ar = {"Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}
    day_name_en = report_date.strftime('%A')
    day_name_ar = days_ar.get(day_name_en, day_name_en)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook  = writer.book
        worksheet = workbook.add_worksheet(f'تقرير {sheet_label}')
        worksheet.right_to_left()
        
        header_title_format = workbook.add_format({'font_name': 'Cairo', 'font_size': 11, 'bold': True, 'font_color': '#1a237e', 'align': 'right'})
        table_header_format = workbook.add_format({'font_name': 'Cairo', 'font_size': 11, 'bold': True, 'bg_color': '#1a237e', 'font_color': '#ffffff', 'align': 'center', 'border': 1})
        table_cell_format = workbook.add_format({'font_name': 'Cairo', 'font_size': 11, 'align': 'center', 'border': 1})
        
        worksheet.write('A1', f"اليوم: {day_name_ar}", header_title_format)
        
        worksheet.write('B1', 'التاريخ', table_header_format)
        worksheet.write('E1', 'اسم الطالب', table_header_format)
        worksheet.write('F1', 'الشعبة', table_header_format)
        worksheet.write('G1', 'اللجنة', table_header_format)
        worksheet.write('H1', 'الحالة', table_header_format)
        worksheet.write('I1', 'الملاحظ / المعلمون', table_header_format)
        
        row_idx = 1
        formatted_date_str = report_date.strftime('%Y-%m-%d')
        
        for _, row in df.iterrows():
            resolved_observer = get_clean_observer_string(row.get('teacher_name', ''), valid_teachers_set)
            worksheet.write(row_idx, 1, formatted_date_str, table_cell_format)
            worksheet.write(row_idx, 4, row['student_name'], table_cell_format)
            worksheet.write(row_idx, 5, row.get('الشعبة', '---'), table_cell_format)
            worksheet.write(row_idx, 6, row['committee'], table_cell_format)
            worksheet.write(row_idx, 7, row['status'], table_cell_format)
            worksheet.write(row_idx, 8, resolved_observer, table_cell_format)
            row_idx += 1
            
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 18)
        worksheet.set_column('E:E', 35)
        worksheet.set_column('F:H', 15)
        worksheet.set_column('I:I', 50) 
        
    return output.getvalue()


# توليد PDF باستخدام ملف الخط arial.ttf المرفوع مسبقاً
def export_attendance_to_pdf_fpdf(df, report_date, valid_teachers_set):
    days_ar = {"Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}
    day_name_en = report_date.strftime('%A')
    day_name_ar = days_ar.get(day_name_en, day_name_en)
    date_str = report_date.strftime('%Y-%m-%d')
    
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # تحميل الخط العربي المرفوع بالمستودع بدالة مستقرة
    pdf.add_font("CustomArial", "", "arial.ttf", uni=True)
    pdf.set_font("CustomArial", size=12)
    
    def format_ar(text):
        if not text: return ""
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)

    for _, row in df.iterrows():
        pdf.add_page()
        
        pdf.set_draw_color(26, 35, 126)
        pdf.set_solid_linewidth(1.5)
        pdf.rect(10, 10, 190, 277)
        
        pdf.set_text_color(26, 35, 126)
        pdf.set_font("CustomArial", size=20)
        pdf.cell(190, 15, format_ar("مدرسة القطيف الثانوية"), ln=True, align="C")
        
        pdf.set_font("CustomArial", size=11)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(190, 8, format_ar("نظام الانضباط المدرسي الذكي (بصمة تميز)"), ln=True, align="C")
        
        pdf.set_draw_color(255, 152, 0)
        pdf.set_solid_linewidth(1)
        pdf.line(15, 38, 195, 38)
        pdf.ln(12)
        
        pdf.set_fill_color(240, 242, 246)
        pdf.set_text_color(26, 35, 126)
        pdf.set_font("CustomArial", size=14)
        status_label = f"إشعار رصد حالة طالب يومي ({row['status']})"
        pdf.cell(170, 12, format_ar(status_label), ln=True, align="C", fill=True, center=True)
        pdf.ln(15)
        
        resolved_observer = get_clean_observer_string(row.get('teacher_name', ''), valid_teachers_set)
        data_items = [
            ("اسم الطالب:", row['student_name']),
            ("الشعبة الدراسية:", row.get('الشعبة', '---')),
            ("رقم اللجنة:", row['committee']),
            ("حالة الرصد:", row['status']),
            ("اليوم:", day_name_ar),
            ("التاريخ:", date_str),
            ("الملاحظ / المعلمون:", resolved_observer)
        ]
        
        pdf.set_font("CustomArial", size=12)
        for label, val in data_items:
            pdf.set_fill_color(26, 35, 126)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(50, 12, format_ar(label), border=1, align="R", fill=True)
            
            pdf.set_fill_color(250, 250, 250)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(120, 12, format_ar(val), border=1, align="R", fill=True, ln=True)
            
        pdf.ln(25)
        
        pdf.set_font("CustomArial", size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(60, 6, format_ar("مدير المدرسة"), ln=True, align="L")
        pdf.cell(60, 6, format_ar("أ. فراس آل عبدالمحسن"), ln=True, align="L")
        pdf.cell(60, 6, format_ar("التوقيع: ........................"), ln=True, align="L")
        
        pdf.set_y(272)
        pdf.set_font("CustomArial", size=9)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(170, 5, format_ar("تم استخراج هذا التقرير تلقائياً عبر منصة بصمة تميز الموحدة."), align="C")

    return pdf.output()


@st.dialog("⚠️ تأكيد التراجع")
def confirm_back_dialog():
    st.write("هل أنت متأكد من العودة وإلغاء التغييرات الحالية دون حفظ الرصد؟")
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("نعم، إلغاء التغييرات", use_container_width=True, type="primary"):
            st.session_state.page = "home"
            st.rerun()
    with c2:
        if st.button("تراجع والبقاء", use_container_width=True):
            st.rerun()

# --- 1. الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('''
        <div class="main-header">
            <h2 style="color:#ffffff; font-size: 22px; font-weight: 400; margin-top: 0; line-height: 0;">أول خطوة للنجاح...التحضير</h2>
            <h2 class="school-name">   </h2>
            <h2 style="color:#ff9800; font-size: 55px; font-weight: 800; margin-bottom: 0;">بَصمَة تَميُز</h2>
                 <h2 class="school-name">مدرسة</h2>
                 <h2 class="school-name">   </h2>
                <h2 class="school-name">القطيف الثانوية</h2>
                 <h2 class="school-name">   </h2>                
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
        if st.button("⏰ لجنة التأخر الصباحي", use_container_width=True):
            st.session_state.page = "m_log"; st.rerun()
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

# --- 3. واجهة رصد اللجان الفرعية ---
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
                label_text = f"👤 {s['student_name']} ({class_info})"
                
                choice = st.radio(label_text, ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['student_name'], horizontal=True)
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
                if st.button("⬅️ عودة بدون حفظ", use_container_width=True):
                    confirm_back_dialog()
            
            st.markdown(f'''
                <div class="stats-footer-container">
                    <span class="stat-badge stat-total">المجموع الكلي ( {count_total} )</span>
                    <span class="stat-badge stat-present">حاضر ( {count_present} )</span>
                    <span class="stat-badge stat-absent">غائب ( {count_absent} )</span>
                    <span class="stat-badge stat-late">متأخر ( {count_late} )</span>
                </div>
            ''', unsafe_allow_html=True)

# --- 🔐 نافذة التحقق من باسوورد لجنة التأخر الصباحي ---
elif st.session_state.page == "m_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    m_pass = st.text_input("أدخل كلمة مرور لجنة التأخر الصباحي:", type="password")
    if st.button("دخول للجنة"):
        if m_pass.strip() == "112233":
            st.session_state.page = "morning_late"; st.rerun()
        else: st.error("كلمة المرور غير صحيحة.")

# --- ⏰ 4. واجهة رصد لجنة التأخر الصباحي ---
elif st.session_state.page == "morning_late":
    if st.button("⬅️ تسجيل خروج من اللجنة"): st.session_state.page = "home"; st.rerun()
    st.markdown("## ⏰ لجنة رصد التأخر الصباحي الموحد")
    today = str(datetime.now().date())
    st.info(f"📅 تاريخ الرصد والمزامنة اليومي: {today}")
    
    res_all_students = supabase.table('students').select("class_name").execute()
    if res_all_students.data:
        df_std_classes = pd.DataFrame(res_all_students.data)
        df_std_classes['class_name'] = df_std_classes['class_name'].astype(str).str.strip()
        all_classes = sorted(list(df_std_classes['class_name'].
