import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io
from weasyprint import HTML  # استيراد مكتبة توليد الـ PDF الاحترافية

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
        f"🏫 *الصف ثالث ثانوي:*%0A"
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


# 🎯 [دالة مضافة جديدة]: لتوليد ملف الـ PDF بحيث يظهر كل طالب في صفحة منفصلة تماماً
def export_attendance_to_pdf(df, report_date, valid_teachers_set):
    days_ar = {"Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}
    day_name_en = report_date.strftime('%A')
    day_name_ar = days_ar.get(day_name_en, day_name_en)
    date_str = report_date.strftime('%Y-%m-%d')
    
    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4 portrait;
                margin: 20mm 15mm;
            }}
            body {{
                font-family: 'Cairo', 'Times New Roman', serif;
                margin: 0;
                padding: 0;
                color: #333;
                background-color: #ffffff;
            }}
            .student-card {{
                page-break-after: always;
                border: 3px double #1a237e;
                padding: 30px;
                border-radius: 15px;
                height: 85%;
                position: relative;
            }}
            /* منع إضافة صفحة فارغة في نهاية الملف */
            .student-card:last-child {{
                page-break-after: avoid;
            }}
            .pdf-header {{
                text-align: center;
                border-bottom: 3px solid #ff9800;
                padding-bottom: 15px;
                margin-bottom: 40px;
            }}
            .pdf-header h2 {{
                margin: 5px 0;
                color: #1a237e;
                font-size: 24px;
                font-weight: bold;
            }}
            .pdf-header h4 {{
                margin: 5px 0;
                color: #555;
                font-size: 16px;
            }}
            .report-title {{
                text-align: center;
                font-size: 22px;
                font-weight: bold;
                background-color: #f0f2f6;
                padding: 10px;
                border-radius: 8px;
                margin-bottom: 40px;
                color: #1a237e;
                border: 1px solid #d1d9e6;
            }}
            .info-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 5px;
            }}
            .info-table th, .info-table td {{
                border: 1px solid #b0bec5;
                padding: 15px;
                font-size: 16px;
                text-align: right;
            }}
            .info-table th {{
                background-color: #1a237e;
                color: white;
                width: 25%;
                font-weight: bold;
            }}
            .info-table td {{
                background-color: #fafafa;
                font-weight: bold;
            }}
            .pdf-footer {{
                position: absolute;
                bottom: 30px;
                left: 30px;
                right: 30px;
                text-align: left;
                border-top: 1px dashed #b0bec5;
                padding-top: 15px;
                font-size: 14px;
                color: #777;
            }}
            .signature-section {{
                margin-top: 60px;
                width: 100%;
                display: block;
            }}
            .signature-box {{
                float: left;
                width: 200px;
                text-align: center;
                font-size: 16px;
                font-weight: bold;
                line-height: 1.8;
            }}
            .clearfix {{
                clear: both;
            }}
        </style>
    </head>
    <body>
    """
    
    for _, row in df.iterrows():
        resolved_observer = get_clean_observer_string(row.get('teacher_name', ''), valid_teachers_set)
        
        html_content += f"""
        <div class="student-card">
            <div class="pdf-header">
                <h2>مدرسة القطيف الثانوية</h2>
                <h4>نظام الانضباط المدرسي الذكي (بصمة تميز)</h4>
            </div>
            
            <div class="report-title">إشعار رصد حالة طالب يومي ({row['status']})</div>
            
            <table class="info-table">
                <tr>
                    <th>اسم الطالب</th>
                    <td>{row['student_name']}</td>
                </tr>
                <tr>
                    <th>الشعبة الدراسية</th>
                    <td>{row.get('الشعبة', '---')}</td>
                </tr>
                <tr>
                    <th>رقم اللجنة</th>
                    <td>{row['committee']}</td>
                </tr>
                <tr>
                    <th>حالة الرصد</th>
                    <td>{row['status']}</td>
                </tr>
                <tr>
                    <th>اليوم</th>
                    <td>{day_name_ar}</td>
                </tr>
                <tr>
                    <th>التاريخ</th>
                    <td>{date_str}</td>
                </tr>
                <tr>
                    <th>الملاحظ / المعلمون</th>
                    <td>{resolved_observer}</td>
                </tr>
            </table>
            
            <div class="signature-section">
                <div class="signature-box">
                    مدير المدرسة<br>
                    أ. فراس آل عبدالمحسن<br>
                    التوقيع: ........................
                </div>
                <div class="clearfix"></div>
            </div>
            
            <div class="pdf-footer">
                تم استخراج هذا التقرير تلقائياً عبر منصة بصمة تميز الموحدة.
            </div>
        </div>
        """
        
    html_content += """
    </body>
    </html>
    """
    
    # تحويل كود الـ HTML إلى ملف PDF باحترافية تامة عبر WeasyPrint
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes


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
        all_classes = sorted(list(df_std_classes['class_name'].unique()))
        
        grades_map = {"أول ثانوي": "1", "ثاني ثانوي": "2", "ثالث ثانوي": "3"}
        selected_grade_label = st.selectbox("اختر الصف الدراسي:", ["---"] + list(grades_map.keys()))
        
        if selected_grade_label != "---":
            grade_prefix = grades_map[selected_grade_label]
            filtered_classes = [c for c in all_classes if c.startswith(grade_prefix)]
            selected_class = st.selectbox("اختر الشعبة:", ["---"] + filtered_classes)
            
            if selected_class != "---":
                students_in_class = supabase.table('students').select("*").eq("class_name", selected_class).execute()
                if students_in_class.data:
                    all_today_attendance = supabase.table('attendance').select("*").eq("date", today).execute()
                    att_map, comm_map, tech_map = {}, {}, {}
                    if all_today_attendance.data:
                        for att in all_today_attendance.data:
                            att_map[att['student_name']] = att['status']
                            comm_map[att['student_name']] = att['committee']
                            tech_map[att['student_name']] = att['teacher_name']
                    
                    st.write("---")
                    morning_results = []
                    c_total, c_p, c_a, c_l = len(students_in_class.data), 0, 0, 0
                    
                    for s in students_in_class.data:
                        s_name = s['student_name']
                        current_status = att_map.get(s_name, "حاضر")
                        student_committee = str(s.get('committee', 'بدون لجنة'))
                        final_committee = comm_map.get(s_name, student_committee)
                        final_teachers = tech_map.get(s_name, "لجنة التأخر الصباحي")
                        if "لجنة التأخر الصباحي" not in final_teachers:
                            final_teachers = f"{final_teachers} | لجنة التأخر الصباحي"
                            
                        choice = st.radio(f"👤 {s_name} (لجنة الطالب: {final_committee})", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(current_status), key=f"morning_{s_name}", horizontal=True)
                        morning_results.append({"student_name": s_name, "committee": final_committee, "status": choice, "date": today, "teacher_name": final_teachers})
                        
                        if choice == "حاضر": c_p += 1
                        elif choice == "غائب": c_a += 1
                        elif choice == "متأخر": c_l += 1
                        
                    st.write("")
                    col_save_m, col_back_m = st.columns(2)
                    with col_save_m:
                        if st.button("💾 اعتماد وتحديث رصد التأخر الصباحي", use_container_width=True, type="primary"):
                            for record in morning_results:
                                supabase.table('attendance').delete().eq("student_name", record['student_name']).eq("date", today).execute()
                            supabase.table('attendance').insert(morning_results).execute()
                            st.success("✅ تم حفظ وتزامن البيانات بنجاح!")
                            time.sleep(1.5); st.rerun()
                    with col_back_m:
                        if st.button("⬅️ إلغاء والتراجع", use_container_width=True): confirm_back_dialog()
                            
                    st.markdown(f'''
                        <div class="stats-footer-container">
                            <span class="stat-badge stat-total">طلاب الشعبة ( {c_total} )</span>
                            <span class="stat-badge stat-present">حاضر ( {c_p} )</span>
                            <span class="stat-badge stat-absent">غائب ( {c_a} )</span>
                            <span class="stat-badge stat-late">متأخر ( {c_l} )</span>
                        </div>
                    ''', unsafe_allow_html=True)

# --- 5. صفحة الشكر ---
elif st.session_state.page == "thank_you":
    st.snow()
    st.markdown(f'<div class="thank-you-box"><h1>✅ تم الرصد بنجاح</h1><h2>أ. {st.session_state.get("teacher", "")}</h2></div>', unsafe_allow_html=True)
    if st.button("🏠 العودة للرئيسية", use_container_width=True): st.session_state.page = "home"; st.rerun()

# --- 6. لوحة الإدارة ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 تقارير الانضباط", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    # جلب أسماء المعلمين الرسمية للربط والمطابقة بدقة داخل لوحة الإدارة مرة واحدة كاش
    try:
        res_teachers = supabase.table("teachers").select("name_tech").execute()
        valid_teachers_set = {str(t['name_tech']).strip() for t in res_teachers.data} if res_teachers.data else set()
    except Exception:
        valid_teachers_set = set()

    with tab1: # تقارير الانضباط
        col_date, col_filter = st.columns(2)
        with col_date:
            d_rep = st.date_input("اختر تاريخ التقرير:", datetime.now())
        with col_filter:
            filter_status = st.selectbox("عرض تصنيف الحالات بالجدول:", ["الكل (الغياب والتأخر)", "الغياب فقط", "التأخر فقط"])
            
        res_att = supabase.table("attendance").select("*").eq("date", str(d_rep)).execute()
        
        if res_att.data:
            df_all = pd.DataFrame(res_att.data)
            df_all['c_sort'] = pd.to_numeric(df_all['committee'], errors='coerce').fillna(0)
            df_all = df_all.sort_values(by='c_sort')
            
            with st.expander("⚠️ خيارات الحذف"):
                if st.button(f"🗑️ حذف كافة سجلات يوم {d_rep}", use_container_width=True):
                    supabase.table("attendance").delete().eq("date", str(d_rep)).execute()
                    st.warning("تم حذف سجلات اليوم المختار."); st.rerun()
            
            res_std = supabase.table("students").select("student_name, class_name").execute()
            s_map = dict(zip([i['student_name'] for i in res_std.data], [i['class_name'] for i in res_std.data]))
            df_all['الشعبة'] = df_all['student_name'].map(s_map).fillna("---")
            
            df_stats = df_all.copy()
            df_stats['الشعبة_str'] = df_stats['الشعبة'].astype(str)
            
            g1_abs = len(df_stats[(df_stats['الشعبة_str'].str.startswith('1')) & (df_stats['status'] == 'غائب')])
            g1_lat = len(df_stats[(df_stats['الشعبة_str'].str.startswith('1')) & (df_stats['status'] == 'متأخر')])
            g2_abs = len(df_stats[(df_stats['الشعبة_str'].str.startswith('2')) & (df_stats['status'] == 'غائب')])
            g2_lat = len(df_stats[(df_stats['الشعبة_str'].str.startswith('2')) & (df_stats['status'] == 'متأخر')])
            g3_abs = len(df_stats[(df_stats['الشعبة_str'].str.startswith('3')) & (df_stats['status'] == 'غائب')])
            g3_lat = len(df_stats[(df_stats['الشعبة_str'].str.startswith('3')) & (df_stats['status'] == 'متأخر')])
            
            st.markdown("### 📈 إحصائيات الانضباط التفصيلية للمراحل")
            c_g1, c_g2, c_g3 = st.columns(3)
            with c_g1: st.markdown(f'<div class="admin-grade-box"><div class="admin-grade-title">أول ثانوي</div><div class="grade-stat-sub" style="color: #c62828;">🚫 الغائبين: {g1_abs}</div><div class="grade-stat-sub" style="color: #ef6c00;">⏳ المتأخرين: {g1_lat}</div></div>', unsafe_allow_html=True)
            with c_g2: st.markdown(f'<div class="admin-grade-box"><div class="admin-grade-title">ثاني ثانوي</div><div class="grade-stat-sub" style="color: #c62828;">🚫 الغائبين: {g2_abs}</div><div class="grade-stat-sub" style="color: #ef6c00;">⏳ المتأخرين: {g2_lat}</div></div>', unsafe_allow_html=True)
            with c_g3: st.markdown(f'<div class="admin-grade-box"><div class="admin-grade-title">ثالث ثانوي</div><div class="grade-stat-sub" style="color: #c62828;">🚫 الغائبين: {g3_abs}</div><div class="grade-stat-sub" style="color: #ef6c00;">⏳ المتأخرين: {g3_lat}</div></div>', unsafe_allow_html=True)
            
            st.write("")
            wa_grade_link = get_wa_grade_stats_link(d_rep, g1_abs, g1_lat, g2_abs, g2_lat, g3_abs, g3_lat)
            st.markdown(f'<a href="{wa_grade_link}" target="_blank" class="wa-link wa-stats">📊 إرسال إحصائية المراحل التفصيلية عبر الواتساب</a>', unsafe_allow_html=True)
            
            # --- 💾 أزرار ترحيل كشوفات الانضباط المستقلة إلى Excel و PDF الفردي ---
            st.markdown("### 💾 ترحيل الكشوفات والتقارير الفردية")
            col_excel_abs, col_excel_lat, col_pdf_individual = st.columns(3)
            
            with col_excel_abs:
                df_absent_only = df_all[df_all['status'] == 'غائب'].copy()
                if not df_absent_only.empty:
                    excel_absent_data = export_attendance_to_excel(df_absent_only, d_rep, "الغياب اليومي", valid_teachers_set)
                    st.download_button(
                        label="🚫 ترحيل (الغياب) إلى Excel",
                        data=excel_absent_data,
                        file_name=f"كشف_الغياب_{d_rep}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.button("🚫 لا يوجد غياب لترحيله", disabled=True, use_container_width=True)
                    
            with col_excel_lat:
                df_late_only = df_all[df_all['status'] == 'متأخر'].copy()
                if not df_late_only.empty:
                    excel_late_data = export_attendance_to_excel(df_late_only, d_rep, "التأخر الصباحي", valid_teachers_set)
                    st.download_button(
                        label="⏳ ترحيل (التأخر) إلى Excel",
                        data=excel_late_data,
                        file_name=f"كشف_التأخر_{d_rep}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.button("⏳ لا يوجد تأخر لترحيله", disabled=True, use_container_width=True)

            # 🛠️ [الزر المستهدف الجديد]: ترحيل تقرير PDF منفصل لكل طالب جاهز للطباعة المباشرة
            with col_pdf_individual:
                df_report_students = df_all[df_all['status'].isin(['غائب', 'متأخر'])].copy()
                if not df_report_students.empty:
                    with st.spinner("⏳ جاري توليد إشعارات الطلاب الفردية (PDF)..."):
                        pdf_data = export_attendance_to_pdf(df_report_students, d_rep, valid_teachers_set)
                    st.download_button(
                        label="📄 طباعة إشعارات الطلاب الفردية (PDF)",
                        data=pdf_data,
                        file_name=f"إشعارات_الطلاب_منفصلة_{d_rep}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.button("📄 لا توجد حالات لطباعة إشعاراتها", disabled=True, use_container_width=True)
            
            st.markdown("---")
            
            report_df = df_all[df_all['status'].isin(['غائب', 'متأخر'])].copy()
            if filter_status == "الغياب فقط": report_df = report_df[report_df['status'] == "غائب"].copy()
            elif filter_status == "التأخر فقط": report_df = report_df[report_df['status'] == "متأخر"].copy()
            
            if not report_df.empty:
                st.dataframe(report_df[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee':'اللجنة','student_name':'الطالب','status':'الحالة','teacher_name':'المعلمون'}), use_container_width=True, hide_index=True)
                c1, c2 = st.columns(2)
                with c1:
                    if filter_status != "التأخر فقط":
                        l1 = get_wa_link(report_df[report_df['status'] == "غائب"], "الغائبين", d_rep)
                        if l1: st.markdown(f'<a href="{l1}" target="_blank" class="wa-link wa-absent">🚫 إرسال الغائبين</a>', unsafe_allow_html=True)
                with c2:
                    if filter_status != "الغياب فقط":
                        l2 = get_wa_link(report_df[report_df['status'] == "متأخر"], "المتأخرين", d_rep)
                        if l2: st.markdown(f'<a href="{l2}" target="_blank" class="wa-link wa-late">⏳ إرسال المتأخرين</a>', unsafe_allow_html=True)
            else:
                st.info(f"لا توجد سجلات مطابقة لـ ({filter_status}) في هذا التاريخ.")
        else: st.info("لا توجد بيانات لهذا التاريخ.")

    with tab2: # حالة اللجان
        st.subheader("🏘️ حالة رصد اللجان اللحظية")
        att_now = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        comm_status = {}
        for r in att_now.data:
            c_id = str(r['committee'])
            t_names = str(r['teacher_name']).split(" | ")
            clean_names = []
            for name in t_names:
                if name.strip() and name.strip() not in clean_names: clean_names.append(name.strip())
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

    with tab3: # إدارة البيانات
        if st.text_input("رمز الأمان لإدارة البيانات:", type="password") == "4321":
            df_s = pd.DataFrame(supabase.table('students').select("*").execute().data)
            if not df_s.empty:
                buf_s = io.BytesIO()
                with pd.ExcelWriter(buf_s) as wr: df_s.to_excel(wr, index=False)
                st.download_button("📥 تحميل سجل الطلاب الحالي (Excel)", buf_s.getvalue(), "students_backup.xlsx", use_container_width=True)
            st.divider()
            df_t = pd.DataFrame(supabase.table('teachers').select("*").execute().data)
            if not df_t.empty:
                buf_t = io.BytesIO()
                with pd.ExcelWriter(buf_t) as wr: df_t.to_excel(wr, index=False)
                st.download_button("📥 تحميل سجل المعلمين الحالي (Excel)", buf_t.getvalue(), "teachers_backup.xlsx", use_container_width=True)
            
            st.markdown("---")
            target_table = st.selectbox("اختر الجدول المراد تحديث بياناته:", ["---", "Students (الطلاب)", "Teachers (المعلمون)"])
            if target_table != "---":
                uploaded_file = st.file_uploader("اختر ملف Excel أو CSV المُراد رفعه:", type=["xlsx", "csv"])
                if uploaded_file is not None:
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            file_bytes = uploaded_file.read()
                            sample = file_bytes[:1024].decode('utf-8', errors='ignore')
                            uploaded_file.seek(0)
                            delim = ';' if ';' in sample.split('\n')[0] and sample.count(';') > sample.count(',') else ','
                            df_uploaded = pd.read_csv(uploaded_file, sep=delim)
                        else:
                            df_uploaded = pd.read_excel(uploaded_file)
                        st.dataframe(df_uploaded.head(), use_container_width=True)
                        if st.button("🚀 تأكيد مسح البيانات القديمة ورفع الجديدة", use_container_width=True, type="primary"):
                            df_uploaded = df_uploaded.astype(str).replace('nan', None).replace('NaN', None)
                            records_to_insert = df_uploaded.to_dict(orient='records')
                            if target_table == "Students (الطلاب)":
                                supabase.table("students").delete().neq("student_name", "🔴🔴🔴").execute()
                                supabase.table("students").insert(records_to_insert).execute()
                                st.success("⚡ تم تحديث سجل الطلاب بنجاح!")
                            elif target_table == "Teachers (المعلمون)":
                                supabase.table("teachers").delete().neq("name_tech", "🔴🔴🔴").execute()
                                supabase.table("teachers").insert(records_to_insert).execute()
                                st.success("⚡ تم تحديث سجل المعلمين بنجاح!")
                            time.sleep(1.5); st.rerun()
                    except Exception as e:
                        st.error(f"حدث خطأ: {e}")
