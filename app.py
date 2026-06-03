def export_attendance_to_pdf_fpdf(df, report_date, valid_teachers_set):
    days_ar = {"Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}
    day_name_en = report_date.strftime('%A')
    day_name_ar = days_ar.get(day_name_en, day_name_en)
    date_str = report_date.strftime('%Y-%m-%d')
    
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # تحميل الخط العربي المستقر
    pdf.add_font("CustomArial", "", "arial.ttf", uni=True)
    pdf.set_font("CustomArial", size=12)
    
    def format_ar(text):
        if not text: return ""
        return get_display(arabic_reshaper.reshape(str(text)))

    for _, row in df.iterrows():
        pdf.add_page()
        
        # --- الترويسة الرسمية (يمين) ---
        pdf.set_font("CustomArial", style="", size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(140, 15)
        pdf.cell(55, 6, format_ar("المملكة العربية السعودية"), ln=True, align="R")
        pdf.set_x(140)
        pdf.cell(55, 6, format_ar("وزارة التعليم"), ln=True, align="R")
        pdf.set_x(140)
        pdf.cell(55, 6, format_ar("الإدارة العامة للتعليم بالمنطقة الشرقية"), ln=True, align="R")
        pdf.set_x(140)
        pdf.cell(55, 6, format_ar("مكتب التعليم بالقطيف"), ln=True, align="R")
        pdf.set_x(140)
        pdf.cell(55, 6, format_ar("مدرسة القطيف الثانوية"), ln=True, align="R")
        
        # --- شعار الرؤية (منتصف) ---
        pdf.set_font("CustomArial", style="B", size=14)
        pdf.set_xy(85, 18)
        pdf.cell(40, 6, format_ar("رؤية VISION"), ln=True, align="C")
        pdf.set_x(85)
        pdf.cell(40, 6, format_ar("2 3 0"), ln=True, align="C")
        pdf.set_font("CustomArial", style="", size=9)
        pdf.set_x(85)
        pdf.cell(40, 5, format_ar("وزارة التعليم"), ln=True, align="C")
        
        # --- إطار العنوان الرئيسي (مطابق تماماً للصورة المعروضة) ---
        pdf.set_draw_color(0, 32, 96) # اللون الكحلي الغامق للرسم الإداري
        pdf.set_line_width(0.6)
        pdf.rect(75, 45, 60, 10)
        pdf.set_xy(75, 47)
        pdf.set_font("CustomArial", style="B", size=13)
        pdf.cell(60, 6, format_ar("الاختبارات - محضر غياب"), align="C", ln=True)
        
        # --- العنوان العريض للمحضر ---
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.5)
        pdf.rect(15, 60, 180, 12)
        pdf.set_xy(15, 63)
        pdf.set_font("CustomArial", style="B", size=14)
        pdf.cell(180, 6, format_ar("محضر ( غـيـاب ) طالب في اختبارات نهاية الفصل الدراسي"), align="C", ln=True)
        
        # --- خانة اليوم والتاريخ المنفصلة ---
        # جزء التاريخ
        pdf.set_xy(80, 78)
        pdf.set_fill_color(217, 217, 217) # خلفية رمادية للعنوان الجانبي
        pdf.cell(30, 10, format_ar("التاريخ"), border=1, align="C", fill=True)
        pdf.cell(85, 10, format_ar(f"      /      /  ١٤٤٧ هـ  ( {date_str} )"), border=1, align="C")
        # جزء اليوم
        pdf.set_xy(15, 78)
        pdf.cell(20, 10, format_ar("اليوم"), border=1, align="C", fill=True)
        pdf.cell(45, 10, format_ar(day_name_ar), border=1, align="C", ln=True)
        
        # --- بيانات الطالب الأساسية ---
        pdf.set_xy(15, 93)
        pdf.cell(25, 10, format_ar("الاسم رباعي"), border=1, align="C", fill=True)
        pdf.set_font("CustomArial", style="B", size=12)
        pdf.cell(100, 10, format_ar(row['student_name']), border=1, align="R")
        pdf.set_font("CustomArial", style="", size=12)
        pdf.cell(20, 10, format_ar("الشعبة"), border=1, align="C", fill=True)
        pdf.cell(35, 10, format_ar(row.get('الشعبة', '---')), border=1, align="C", ln=True)
        
        # --- شبكة البيانات الأكاديمية والفترات ---
        pdf.set_xy(15, 108)
        pdf.cell(35, 8, format_ar("رقم اللجنة"), border=1, align="C", fill=True)
        pdf.cell(35, 8, format_ar("الصف"), border=1, align="C", fill=True)
        pdf.cell(40, 8, format_ar("المادة"), border=1, align="C", fill=True)
        pdf.cell(35, 8, format_ar("الفترة"), border=1, align="C", fill=True)
        pdf.cell(35, 8, format_ar("الفصل الدراسي"), border=1, align="C", fill=True, ln=True)
        
        # صف البيانات الفارغ المخصص للتعبئة اليدوية والمطابق لتصميم المحضر
        pdf.set_xy(15, 116)
        pdf.cell(35, 18, format_ar(row['committee']), border=1, align="C")
        pdf.cell(35, 18, format_ar(""), border=1, align="C")
        pdf.cell(40, 18, format_ar(""), border=1, align="C")
        
        # مربع خيارات الفترات التفاعلي داخل الجدول
        pdf.set_font("CustomArial", size=10)
        pdf.cell(35, 18, format_ar("[  ] الأولى   [  ] الثانية"), border=1, align="C")
        pdf.cell(35, 18, format_ar("[  ] الأول     [ X ] الثاني"), border=1, align="C", ln=True)
        
        # --- صندوق الإجراءات والملاحظات ---
        pdf.set_font("CustomArial", size=12)
        pdf.set_xy(15, 140)
        pdf.rect(15, 140, 180, 45)
        pdf.set_xy(18, 142)
        pdf.cell(174, 6, format_ar("الإجراءات والملاحظات الإدارية:"), ln=True, align="R")
        # خطوط التنقيط للكتابة
        pdf.set_text_color(150, 150, 150)
        pdf.set_x(18)
        pdf.cell(174, 10, format_ar(".........................................................................................................................................."), ln=True, align="R")
        pdf.set_x(18)
        pdf.cell(174, 10, format_ar(".........................................................................................................................................."), ln=True, align="R")
        
        # --- التوقيعات والاعتماد أسفل المحضر ---
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("CustomArial", style="B", size=13)
        pdf.set_xy(15, 200)
        pdf.cell(90, 6, format_ar("مدير المدرسة"), ln=True, align="C")
        pdf.set_x(15)
        pdf.cell(90, 8, format_ar("أ. فراس آل عبدالمحسن"), ln=True, align="C")
        
        resolved_observer = get_clean_observer_string(row.get('teacher_name', ''), valid_teachers_set)
        pdf.set_xy(105, 200)
        pdf.cell(90, 6, format_ar("الملاحظ / مراقب اللجنة"), ln=True, align="C")
        pdf.set_x(105)
        pdf.cell(90, 8, format_ar(resolved_observer), ln=True, align="C")
        
        # حيز التوقيع الصريح
        pdf.set_xy(15, 225)
        pdf.cell(90, 6, format_ar("التوقيع: ..................................."), align="C")
        pdf.cell(90, 6, format_ar("التوقيع: ..................................."), align="C")

    return bytes(pdf.output())
