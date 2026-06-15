import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Дигитална Домоуправа", page_icon="🏢", layout="wide")

# Имейл на домоуправителя (променете го с вашия истински имейл)
ADMIN_EMAIL = "zdravkka@gmail.com"

# 1. ИНИЦИАЛИЗАЦИЯ НА БАЗАТА ДАННИ
if "database" not in st.session_state:
    apts_list = []
    for i in range(1, 11):
        apts_list.append({
            "Апартамент": f"Ап. {i}",
            "Собственик": f"Собственик Ап. {i}",
            "Живущи": 1,
            "Салдо (лв)": 0.0,
            "Имейл": ""
        })
    
    st.session_state.database = {
        "apartments": pd.DataFrame(apts_list),
        "cashbox": 0.0,
        "expenses": [],
        "news": [{"Дата": datetime.date.today().strftime("%d.%m.%Y"), "Заглавие": "Добре дошли!", "Текст": "Приложението на нашия вход вече е активно."}],
        "polls": []
    }

db = st.session_state.database

# ==================== СИСТЕМА ЗА ВХОД ====================
st.sidebar.title("🔐 Вход в приложението")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.is_admin = False

if not st.session_state.logged_in:
    email_input = st.sidebar.text_input("Въведете вашия имейл:").strip().lower()
    password_input = st.sidebar.text_input("Парола на входа:", type="password")
    
    if st.sidebar.button("Влизане"):
        if email_input == ADMIN_EMAIL and password_input == "vhod123":
            st.session_state.logged_in = True
            st.session_state.user_email = email_input
            st.session_state.is_admin = True
            st.rerun()
        elif email_input in db["apartments"]["Имейл"].str.lower().values and password_input == "vhod123":
            st.session_state.logged_in = True
            st.session_state.user_email = email_input
            st.session_state.is_admin = False
            st.rerun()
        else:
            st.sidebar.error("❌ Непознат имейл или грешна парола на входа!")
else:
    st.sidebar.success(f"Влезли сте като: {st.session_state.user_email}")
    if st.session_state.is_admin:
        st.sidebar.info("👑 Роля: Домоуправител")
    if st.sidebar.button("Изход"):
        st.session_state.logged_in = False
        st.session_state.is_admin = False
        st.session_state.user_email = ""
        st.rerun()

# ==================== СТРАНИЦИ И НАВИГАЦИЯ ====================
if st.session_state.logged_in:
    menu_options = ["Начално табло", "Съобщения & Новини", "Анкети", "Бланки"]
    if st.session_state.is_admin:
        menu_options.insert(1, "Плащания & Разходи (Админ)")
        menu_options.insert(2, "Настройки на входа (Админ)")
        
    page = st.radio("Меню:", menu_options, horizontal=True)

    if not st.session_state.is_admin:
        user_row = db["apartments"][db["apartments"]["Имейл"].str.lower() == st.session_state.user_email].iloc[0]
        user_apt = user_row["Апартамент"]
        user_residents = user_row["Живущи"]
        user_saldo = user_row["Салдо (лв)"]
        monthly_fee = 10 + (user_residents * 5)

    # 🏠 СТРАНИЦА: НАЧАЛНО ТАБЛО
    if page == "Начално табло":
        st.title("🏢 Дигитално табло на етажната собственост")
        st.metric(label="💰 Налични пари в общата каса", value=f"{db['cashbox']} лв.")
        
        if st.session_state.is_admin:
            st.subheader("📊 Текущо състояние на всички апартаменти")
            view_df = db["apartments"].copy()
            view_df["Месечна такса"] = 10 + (view_df["Живущи"] * 5)
            st.dataframe(view_df[["Апартамент", "Собственик", "Живущи", "Месечна такса", "Салдо (лв)"]], use_container_width=True)
        else:
            st.markdown("---")
            st.subheader(f"📊 Финансов статус за {user_apt} ({user_row['Собственик']})")
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"👥 Брой живущи: **{user_residents}**")
                st.info(f"💶 Вашата месечна такса: **{monthly_fee} лв.** (10лв + {user_residents}х5лв)")
            with c2:
                if user_saldo < 0:
                    st.error(f"📉 Дължима сума към момента: **{abs(user_saldo)} лв.**")
                elif user_saldo > 0:
                    st.success(f"📈 Предплатена сума (кредит): **{user_saldo} лв.**")
                else:
                    st.success("✅ Нямате текущи задължения към касата.")

        st.markdown("---")
        st.subheader("🧾 Хронология на разходите на входа")
        if not db["expenses"]:
            st.write("Няма регистрирани разходи за този период.")
        for exp in db["expenses"]:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"📅 **{exp['Дата']}** | {exp['Описание']} | 💵 **{exp['Сума']} лв.**")
            with col2:
                st.image(exp["Snimka"], caption="Документ/Касова бележка", width=120)

    # 💵 СТРАНИЦА: ПЛАЩАНИЯ (САМО ЗА АДМИН)
    elif page == "Плащания & Разходи (Админ)":
        st.title("⚙️ Финансово управление (Домоуправител)")
        tab1, tab2 = st.tabs(["Внасяне на такса", "Добавяне на разход"])
        
        with tab1:
            apt_to_pay = st.selectbox("Изберете апартамент, който плаща:", db["apartments"]["Апартамент"])
            idx = db["apartments"][db["apartments"]["Апартамент"] == apt_to_pay].index[0]
            current_saldo = db["apartments"].at[idx, "Салдо (лв)"]
            
            st.write(f"Текущо салдо на {apt_to_pay}: **{current_saldo} лв.**")
            amount_paid = st.number_input("Въведете платената сума (лв):", min_value=0.0, step=5.0, key="pay_in")
            
            if st.button("💰 Потвърди и запиши плащането"):
                db["apartments"].at[idx, "Салдо (лв)"] += amount_paid
                db["cashbox"] += amount_paid
                st.success(f"Успешно отразено! Ново салдо на {apt_to_pay}: {current_saldo + amount_paid} лв.")
                st.rerun()
                
        with tab2:
            exp_desc = st.text_input("Описание на разхода (напр. Крушки за входа):")
            exp_amount = st.number_input("Сума (лв):", min_value=0.0, step=1.0, key="pay_out")
            exp_pic = st.text_input("Линк към снимка на бележката:", value="https://placeholder.com")
            
            if st.button("❌ Запиши разхода и извади от касата"):
                if db["cashbox"] >= exp_amount:
                    db["cashbox"] -= exp_amount
                    db["expenses"].append({
                        "Дата": datetime.date.today().strftime("%d.%m.%Y"),
                        "Описание": exp_desc,
                        "Сума": exp_amount,
                        "Snimka": exp_pic
                    })
                    st.success("Разходът е добавен успешно!")
                    st.rerun()
                else:
                    st.error("Грешка: В касата няма достатъчно средства за този разход!")

    # ⚙️ СТРАНИЦА: НАСТРОЙКИ (САМО ЗА АДМИН)
    elif page == "Настройки на входа (Админ)":
        st.title("👥 Управление на апартаментите и живущите")
        apt_to_edit = st.selectbox("Изберете апартамент за редактиране:", db["apartments"]["Апартамент"])
        idx = db["apartments"][db["apartments"]["Апартамент"] == apt_to_edit].index[0]
        
        new_owner = st.text_input("Име на собственик / Наемател:", value=db["apartments"].at[idx, "Собственик"])
        new_residents = st.number_input("Брой живущи:", min_value=0, max_value=20, value=int(db["apartments"].at[idx, "Живущи"]))
        new_email = st.text_input("Имейл за вход в приложението:", value=db["apartments"].at[idx, "Имейл"]).strip().lower()
        
        if st.button("💾 Запази промените за този апартамент"):
            db["apartments"].at[idx, "Собственик"] = new_owner
            db["apartments"].at[idx, "Живущи"] = new_residents
            db["apartments"].at[idx, "Имейл"] = new_email
            st.success(f"Данните за {apt_to_edit} бяха обновени успешно!")
            st.rerun()

    # 📢 СТРАНИЦА: СЪОБЩЕНИЯ
    elif page == "Съобщения & Новини":
        st.title("📢 Важни съобщения и Новини")
        if st.session_state.is_admin:
            with st.form("new_post"):
                title = st.text_input("Заглавие на съобщението:")
                text = st.text_area("Съдържание:")
                if st.form_submit_button("Публикувай"):
                    db["news"].insert(0, {"Дата": datetime.date.today().strftime("%d.%m.%Y"), "Заглавие": title, "Текст": text})
                    st.rerun()
        for msg in db["news"]:
            st.warning(f"**{msg['Заглавие']}** ({msg['Дата']})\n\n{msg['Текст']}")

    # 🗳️ СТРАНИЦА: АНКЕТИ
    elif page == "Анкети":
        st.title("🗳️ Анкети и гласувания")
        with st.expander("➕ Пусни нова анкета"):
            poll_q = st.text_input("Въпрос за гласуване:")
            if st.button("Създай анкета"):
                db["polls"].append({"Въпрос": poll_q, "Опции": {"Да": 0, "Не": 0}})
                st.rerun()
        for idx, poll in enumerate(db["polls"]):
            st.write(f"### {poll['Въпрос']}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Гласувай с 'Да'", key=f"y_{idx}"):
                    poll["Опции"]["Да"] += 1
                    st.rerun()
            with col2:
                if st.button(f"Гласувай с 'Не'", key=f"n_{idx}"):
                    poll["Опции"]["Не"] += 1
                    st.rerun()
            st.bar_chart(pd.DataFrame.from_dict(poll["Опции"], orient='index', columns=['Гласове']))

    # 📄 СТРАНИЦА: БЛАНКИ
    elif page == "Бланки":
        st.title("📄 Документи и бланки")
        st.markdown("- 📥 [Бланка за Декларация по ЗУЕС](https://example.com)")

else:
    st.info("👋 Моля, въведете вашия имейл и парола `vhod123` в лявото меню, за да отворите таблото.")
