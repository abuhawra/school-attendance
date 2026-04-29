# --- 2. لوحة الإدارة (إضافة منطقة الحذف وتأكيد المسح) ---
elif page == "📊 لوحة الإدارة":
    st.header("📊 لوحة الإدارة والتقارير")
    if st.sidebar.text_input("كلمة المرور", type="password") == "1234":
        
        # التحكم في النظام
        status = get_system_status()
        col_status, col_delete = st.columns([2, 1])
        
        with col_status:
            if status:
                st.success("🟢 النظام الآن: مفتوح")
                if st.button("🔴 إيقاف الرصد"):
                    supabase.table("settings").update({"is_open": False}).eq("setting_name", "attendance_status").execute()
                    st.rerun()
            else:
                st.error("🔴 النظام الآن: مغلق")
                if st.button("🟢 تفعيل الرصد"):
                    supabase.table("settings").update({"is_open": True}).eq("setting_name", "attendance_status").execute()
                    st.rerun()

        # --- إضافة منطقة الحذف ---
        with col_delete:
            st.warning("🗑️ منطقة الحذف")
            delete_date = st.date_input("اختر تاريخاً لحذفه", datetime.now(), key="del_date")
            
            # خاصية تأكيد الحذف
            if st.button(f"⚠️ مسح غياب يوم {delete_date}"):
                st.session_state.confirm_delete = True
            
            if st.session_state.get('confirm_delete', False):
                st.error(f"هل أنت متأكد من حذف جميع بيانات يوم {delete_date}؟")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ نعم، احذف"):
                        supabase.table('attendance').delete().eq('date', str(delete_date)).execute()
                        st.success(f"تم مسح بيانات يوم {delete_date} بنجاح.")
                        st.session_state.confirm_delete = False
                        time.sleep(1)
                        st.rerun()
                with col_no:
                    if st.button("❌ تراجع"):
                        st.session_state.confirm_delete = False
                        st.rerun()

        st.divider()
        report_date = st.date_input("📅 تاريخ المتابعة", datetime.now())
        
        # جلب البيانات للتقارير
        att_res = supabase.table('attendance').select("*").eq('date', str(report_date)).execute()
        std_res = supabase.table('students').select("student_name, section, committee").execute()
        
        tab1, tab2 = st.tabs(["⚠️ كشف الغياب التفصيلي", "🚩 حالة اللجان"])
        
        with tab1:
            if att_res.data:
                df_att = pd.DataFrame(att_res.data)
                df_std = pd.DataFrame(std_res.data)
                merged = pd.merge(df_att, df_std, on='student_name', how='left')
                
                report_df = merged[merged['status'].isin(['غائب', 'متأخر'])][['student_name', 'section', 'committee_x', 'status']]
                report_df.columns = ['الاسم', 'الشعبة', 'اللجنة', 'الحالة']
                
                # زر الواتساب التفصيلي المصلح
                wa_msg = f"*تقرير الغياب التفصيلي - {report_date}*\n\n"
                for _, row in report_df.iterrows():
                    wa_msg += f"👤 {row['الاسم']}\n🏢 الشعبة: {row['الشعبة']} | 🎯 اللجنة: {row['اللجنة']}\n🚩 الحالة: *{row['الحالة']}*\n"
                    wa_msg += "------------------\n"
                
                st.link_button("📱 إرسال الكشف التفصيلي عبر واتساب", f"https://wa.me/?text={urllib.parse.quote(wa_msg)}")
                st.table(report_df)
            else: st.info("لا توجد سجلات لهذا التاريخ.")

        with tab2:
            # تقرير حالة اللجان
            all_c = set([str(s['committee']) for s in std_res.data if s['committee']])
            done_c = set([str(a['committee']) for a in att_res.data])
            not_done = sorted(list(all_c - done_c), key=smart_sort)
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.success(f"✅ لجان رصدت ({len(done_c)}):")
                st.write(", ".join(sorted(list(done_c), key=smart_sort)))
            with col_b:
                st.error(f"❌ لجان لم ترصد ({len(not_done)}):")
                st.write(", ".join(not_done))
    else: st.info("أدخل كلمة المرور في القائمة الجانبية.")
