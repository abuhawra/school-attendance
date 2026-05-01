with tab2:
        # إصلاح حالة اللجان
        st.subheader(f"🏘️ متابعة اللجان ليوم: {datetime.now().date()}")
        # جلب قائمة اللجان الكلية
        all_s_data = supabase.table('students').select("committee").execute()
        total_coms = sorted(list(set([str(i['committee']) for i in all_s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        # جلب اللجان التي رصدت اليوم
        done_res = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        # تقليل البيانات لمنع تكرار اللجان في العرض
        done_coms_map = {str(i['committee']): i['teacher_name'] for i in done_res.data}
        
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ لجان تم رصدها")
            for c in total_coms:
                if c in done_coms_map: st.write(f"📍 لجنة {c} (المعلم: {done_coms_map[c]})")
        with c2:
            st.error("❌ لجان لم ترصد بعد")
            for c in total_coms:
                if c not in done_coms_map: st.write(f"⚠️ لجنة {c}")

    with tab3:
        # إعادة خانة الرقم السري للبيانات
        st.subheader("🔐 إدارة قاعدة البيانات")
        db_pass = st.text_input("أدخل الرقم السري للتحكم (4321):", type="password")
        if db_pass == "4321":
            st.success("صلاحية الإدارة مفعلة")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("### 📥 النسخ الاحتياطي")
                std_res = supabase.table('students').select("*").execute()
                if std_res.data:
                    df_std = pd.DataFrame(std_res.data)
                    st.download_button("💾 تحميل CSV", data=df_std.to_csv(index=False).encode('utf-8-sig'), file_name="students.csv")
            with col_b:
                st.markdown("### 🔄 الاستعادة")
                up_file = st.file_uploader("ارفع ملف النسخة:", type=["csv", "xlsx"])
                if up_file and st.button("🚀 بدء الاستعادة"):
                    df_up = pd.read_csv(up_file) if up_file.name.endswith('.csv') else pd.read_excel(up_file)
                    supabase.table('students').delete().neq('student_name', 'none').execute()
                    recs = df_up.to_dict('records')
                    for r in recs: r.pop('id', None)
                    supabase.table('students').insert(recs).execute()
                    st.success("تمت الاستعادة بنجاح"); st.rerun()
