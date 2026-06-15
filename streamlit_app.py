import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# Конфигурация на страницата
st.set_page_config(page_title="Дигитална Домоуправа", page_icon="🏢", layout="wide")

ADMIN_EMAIL = "zdravkka@gmail.com"

# ==================== СВЪРЗВАНЕ С GOOGLE SHEETS ====================
conn = st.connection("gsheets", type=GSheetsConnection)

# ФУНКЦИИ ЗА ЗАПАЗВАНЕ И ЗАРЕЖДАНЕ НА ДАННИТЕ ЧРЕЗ GOOGLE SHEETS
def load_data():
    try:
        # Четене на отделните табове от Гугъл таблицата
        apts = conn.read(worksheet="apartments")
        cash_df = conn.read(worksheet="cashbox")
        exp_df = conn.read(worksheet="expenses")
        news_df = conn.read(worksheet="news")
        polls_df = conn.read(worksheet="polls")
        
        # Конвертиране в списъци/речници за съвместимост с останалия код
        expenses_list = exp_df.to_dict(orient="records") if not exp_df.empty else []
        news_list = news_df.to_dict(orient="records") if not news_df.empty else []
        polls_list = polls_df.to_dict(orient="records") if not polls_df.empty else []
        
        # Взимане на общата каса
        cash_value = float(cash_df.iloc[0, 0]) if not cash_df.empty else 0.0
        
        return {
            "apartments": apts,
            "cashbox": cash_value,
            "expenses": expenses_list,
            "news": news_list,
            "polls": polls_list
        }
    except Exception as e:
        # Първоначална структура, ако таблицата е напълно празна
        apts_list = []
        for i in range(1, 11):
            apts_list.append({
                "Апартамент": f"Ап. {i}",
                "Собственик": f"Собственик {i}",
                "Живущи": 1,
                "Салдо (€)": 0.0,
                "Имейл": ADMIN_EMAIL if i == 1 else ""
            })
        return {
            "apartments": pd.DataFrame(apts_list),
            "cashbox": 0.0,
            "expenses": [],
            "news": [{"Дата": datetime.date.today().strftime("%d.%m.%Y"), "Заглавие": "Добре дошли!", "Текст": "Приложението е активно."}],
            "polls": []
        }

def save_data(data):
    # Записване на всеки таб обратно в Google Sheets
    conn.update(worksheet="apartments", data=data["apartments"])
    
    cash_df = pd.DataFrame([[data["cashbox"]]], columns=["Каса"])
    conn.update(worksheet="cashbox", data=cash_df)
    
    exp_df = pd.DataFrame(data["expenses"]) if data["expenses"] else pd.DataFrame(columns=["Дата", "Описание", "Сума", "Снимка"])
    conn.update(worksheet="expenses", data=exp_df)
    
    news_df = pd.DataFrame(data["news"]) if data["news"] else pd.DataFrame(columns=["Дата", "Заглавие", "Текст"])
    conn.update(worksheet="news", data=news_df)
    
    polls_df = pd.DataFrame(data["polls"]) if data["polls"] else pd.DataFrame(columns=["Въпрос", "Опции", "Гласове"])
    conn.update(worksheet="polls", data=polls_df)

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
        user_saldo = user_row["Салдо (€)"]
        monthly_fee = 10 + (user_residents * 5) # Базова такса изчислена в евро

    # 🏠 НАЧАЛНО ТАБЛО
    if page == "Начално табло":
        st.title("🏢 Дигитално табло на етажната собственост")
        st.metric(label="💶 Налични пари в общата каса", value=f"{db['cashbox']} €")
        
        if st.session_state.is_admin:
            st.subheader("📊 Текущо състояние на всички апартаменти")
            view_df = db["apartments"].copy()
            view_df["Месечна такса (€)"] = 10 + (view_df["Живущи"] * 5)
            st.dataframe(view_df[["Апартамент", "Собственик", "Живущи", "Месечна такса (€)", "Салдо (€)", "Имейл"]], use_container_width=True)
        else:
            st.markdown("---")
            st.subheader(f"📊 Финансов статус за {user_apt} ({user_row['Собственик']})")
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"👥 Брой живущи: **{user_residents}**")
                st.info(f"💶 Вашата месечна такса: **{monthly_fee} €**")
            with c2:
                if user_saldo < 0:
                    st.error(f"📉 Дължима сума към момента: **{abs(user_saldo)} €**")
                elif user_saldo > 0:
                    st.success(f"📈 Предплатена сума (кредит): **{user_saldo} €**")
                else:
                    st.success("✅ Нямате текущи задължения.")

        st.markdown("---")
        st.subheader("🧾 Хронология на разходите")
        if not db["expenses"]:
            st.write("Няма регистрирани разходи.")
        for exp in db["expenses"]:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"📅 **{exp['Дата']}** | {exp['Описание']} | 💶 **{exp['Сума']} €**")
            with col2:
                st.image(exp["Снимка"], caption="Касова бележка", width=120)

    # 💵 ПЛАЩАНИЯ (АДМИН)
    elif page == "Плащания & Разходи (Админ)":
        st.title("⚙️ Финансово управление")
        tab1, tab2, tab3 = st.tabs(["Внасяне на такса", "Добавяне на разход", "🔄 Месечно начисляване"])
        
        with tab1:
            apt_to_pay = st.selectbox("Изберете апартамент:", db["apartments"]["Апартамент"])
            idx = db["apartments"][db["apartments"]["Апартамент"] == apt_to_pay].index[0]
            current_saldo = db["apartments"].at[idx, "Салдо (€)"]
            
            st.write(f"Текущо салдо: **{current_saldo} €**")
            amount_paid = st.number_input("Въведете платената сума (€):", min_value=0.0, step=5.0)
            
            if st.button("💶 Запиши плащането"):
                db["apartments"].at[idx, "Салдо (€)"] += amount_paid
                db["cashbox"] += amount_paid
                save_data(db)
                st.success("Плащането е запазено успешно!")
                st.rerun()
                
        with tab2:
            exp_desc = st.text_input("Описание на разхода:")
            exp_amount = st.number_input("Сума (€):", min_value=0.0)
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
                    st.success("Разходът е записан успешно!")
                    st.rerun()
                else:
                    st.error("Няма достатъчно пари в касата!")

    # Заглушки за останалите страници, за да не дава грешка приложението
    elif page == "Съобщения & Новини":
        st.title("📢 Съобщения & Новини")
        st.write("Секцията е в процес на свързване.")
    elif page == "Анкети":
        st.title("🗳️ Анкети и гласуване")
        st.write("Секцията е в процес на свързване.")
    elif page == "Бланки":
        st.title("📄 Документи и бланки")
        st.write("Секцията е в процес на свързване.")
    elif page == "Настройки на входа (Админ)":
        st.title("🛠️ Настройки на етажната собственост")
        st.write("Секцията е в процес на свързване.")
