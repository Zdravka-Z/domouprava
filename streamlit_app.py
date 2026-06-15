import streamlit as st
import pandas as pd
import datetime
import json
import os

st.set_page_config(page_title="Дигитална Домоуправа", page_icon="🏢", layout="wide")

DB_FILE = "vhod_database.json"
ADMIN_EMAIL = "zdravkka@gmail.com" # Променете с вашия истински имейл

# ФУНКЦИИ ЗА ЗАПАЗВАНЕ И ЗАРЕЖДАНЕ НА ДАННИТЕ
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["apartments"] = pd.DataFrame(data["apartments"])
            return data
    else:
        apts_list = []
        for i in range(1, 11):
            apts_list.append({
                "Апартамент": f"Ап. {i}",
                "Собственик": f"Собственик {i}",
                "Живущи": 1,
                "Салдо (лв)": 0.0,
                "Имейл": ""
            })
        return {
            "apartments": pd.DataFrame(apts_list),
            "cashbox": 0.0,
            "expenses": [],
            "news": [{"Дата": datetime.date.today().strftime("%d.%m.%Y"), "Заглавие": "Добре дошли!", "Текст": "Приложението е активно."}],
            "polls": []
        }

def save_data(data):
    data_to_save = data.copy()
    data_to_save["apartments"] = data_to_save["apartments"].to_dict(orient="records")
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

# Зареждане на базата данни в сесията
if "db" not in st.session_state:
    st.session_state.db = load_data()

db = st.session_state.db

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
            st.sidebar.error("❌ Непознат имейл или грешна парола!")
else:
    st.sidebar.success(f"Влезли сте като: {st.session_state.user_email}")
    if st.sidebar.button("Изход"):
        st.session_state.logged_in = False
        st.session_state.is_admin = False
        st.session_state.user_email = ""
        st.rerun()

# ==================== НАВИГАЦИЯ И СТРАНИЦИ ====================
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

    # 🏠 НАЧАЛНО ТАБЛО
    if page == "Начално табло":
        st.title("🏢 Дигитално табло на етажната собственост")
        st.metric(label="💰 Налични пари в общата каса", value=f"{db['cashbox']} лв.")
        
        if st.session_state.is_admin:
            st.subheader("📊 Текущо състояние на всички апартаменти")
            view_df = db["apartments"].copy()
            view_df["Месечна такса"] = 10 + (view_df["Живущи"] * 5)
            st.dataframe(view_df[["Апартамент", "Собственик", "Живущи", "Месечна такса", "Салдо (лв)", "Имейл"]], use_container_width=True)
        else:
            st.markdown("---")
            st.subheader(f"📊 Финансов статус за {user_apt} ({user_row['Собственик']})")
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"👥 Брой живущи: **{user_residents}**")
                st.info(f"💶 Вашата месечна такса: **{monthly_fee} лв.**")
            with c2:
                if user_saldo < 0:
                    st.error(f"📉 Дължима сума към момента: **{abs(user_saldo)} лв.**")
                elif user_saldo > 0:
                    st.success(f"📈 Предплатена сума (кредит): **{user_saldo} лв.**")
                else:
                    st.success("✅ Нямате текущи задължения.")

        st.markdown("---")
        st.subheader("🧾 Хронология на разходите")
        if not db["expenses"]:
            st.write("Няма регистрирани разходи.")
        for exp in db["expenses"]:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"📅 **{exp['Дата']}** | {exp['Описание']} | 💵 **{exp['Сума']} лв.**")
            with col2:
                st.image(exp["Снимка"], caption="Касова бележка", width=120)

    # 💵 ПЛАЩАНИЯ (АДМИН)
    elif page == "Плащания & Разходи (Админ)":
        st.title("⚙️ Финансово управление")
        tab1, tab2, tab3 = st.tabs(["Внасяне на такса", "Добавяне на разход", "🔄 Месечно начисляване"])
        
        with tab1:
            apt_to_pay = st.selectbox("Изберете апартамент:", db["apartments"]["Апартамент"])
            idx = db["apartments"][db["apartments"]["Апартамент"] == apt_to_pay].index[0]
            current_saldo = db["apartments"].at[idx, "Салдо (лв)"]
            
            st.write(f"Текущо салдо: **{current_saldo} лв.**")
            amount_paid = st.number_input("Въведете платената сума (лв):", min_value=0.0, step=5.0)
            
            if st.button("💰 Запиши плащането"):
                db["apartments"].at[idx, "Салдо (лв)"] += amount_paid
                db["cashbox"] += amount_paid
                save_data(db)
                st.success("Плащането е запазено успешно!")
                st.rerun()
                
        with tab2:
            exp_desc = st.text_input("Описание на разхода:")
            exp_amount = st.number_input("Сума (лв):", min_value=0.0)
            exp_pic = st.text_input("Линк към снимка на бележката:", value="https://placeholder.com")
            
            if st.button("❌ Запиши разхода"):
                if db["cashbox"] >= exp_amount:
                    db["cashbox"] -= exp_amount
                    db["expenses"].append({
                        "Дата": datetime.date.today().strftime("%d.%m.%Y"),
                        "Описание": exp_desc,
                        "Сума": exp_amount,
                        "Снимка": exp_pic
                    })
                    save_data(db)
                    st.success("Разходът е записан!")
                    st.rerun()
                else:
                    st.error("Няма достатъчно пари в касата!")

        with tab3:
            st.subheader("🔄 Автоматично събиране на месечни такси")
            st.warning("Внимание: Натискайте бутона веднъж месечно. Той ще извади таксата от салдото на всеки апартамент.")
            if st.button("🚀 Начисли таксите за нов месец"):
                for i, row in db["apartments"].iterrows():
                    fee = 10 + (row["Живущи"] * 5)
                    db["apartments"].at[i, "Салдо (лв)"] -= fee
                save_data(db)
                st.success("Всички месечни такси бяха начислени автоматично!")
                st.rerun()

    # ⚙️ НАСТРОЙКИ (АДМИН ПАНЕЛ)
    elif page == "Настройки на входа (Админ)":
        st.title("👥 Админ панел: Управление на съседи и начални суми")
        
        st.subheader("1. Настройка на Касата")
        current_cash = st.number_input("Текущи налични пари в касата на входа (лв):", value=float(db["cashbox"]))
        if st.button("💾 Обнови касата"):
            db["cashbox"] = current_cash
            save_data(db)
            st.success("Касата е обновена!")
            st.rerun()
            
        st.markdown("---")
        st.subheader("2. Редактиране на Апартамент")
        apt_to_edit = st.selectbox("Изберете апартамент за промяна:", db["apartments"]["Апартамент"])
        idx = db["apartments"][db["apartments"]["Апартамент"] == apt_to_edit].index[0]
        
        new_owner = st.text_input("Име на собственик:", value=db["apartments"].at[idx, "Собственик"])
        new_residents = st.number_input("Брой живущи:", min_value=0, value=int(db["apartments"].at[idx, "Живущи"]))
        new_email = st.text_input("Имейл за вход:", value=db["apartments"].at[idx, "Имейл"]).strip().lower()
        new_saldo = st.number_input("Текущо салдо (минус за дълг, плюс за кредит):", value=float(db["apartments"].at[idx, "Салдо (лв)"]))
        
        if st.button("💾 Запази промените за апартамента"):
            db["apartments"].at[idx, "Собственик"] = new_owner
            db["apartments"].at[idx, "Живущи"] = new_residents
            db["apartments"].at[idx, "Имейл"] = new_email
            db["apartments"].at[idx, "Салдо (лв)"] = new_saldo
            save_data(db)
            st.success(f"Данните за {apt_to_edit} са запазени!")
            st.rerun()

    # 📢 СЪОБЩЕНИЯ
    elif page == "Съобщения & Новини":
        st.title("📢 Съобщения")
        if st.session_state.is_admin:
            with st.form("new_post"):
                title = st.text_input("Заглавие:")
                text = st.text_area("Съдържание:")
                if st.form_submit_button("Публикувай"):
                    db["news"].insert(0, {"Дата": datetime.date.today().strftime("%d.%m.%Y"), "Заглавие": title, "Текст": text})
                    save_data(db)
