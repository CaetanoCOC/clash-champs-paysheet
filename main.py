
import streamlit as st
import pandas as pd
import plotly.express as px

def process_sheet(file):
    df = pd.read_excel(file, sheet_name=0)
    df.columns = df.iloc[0]
    df = df[1:]

    df.rename(columns={
        df.columns[0]: "Pack/Order#",
        df.columns[1]: "Base#",
        df.columns[2]: "Level"
    }, inplace=True)

    df["Pack/Order#"] = pd.to_numeric(df["Pack/Order#"], errors="coerce")
    df["Base#"] = pd.to_numeric(df["Base#"], errors="coerce")
    # Extrai apenas os dígitos do campo "Level" (ex: "CTh17" → "17")
    df["Level"] = df["Level"].astype(str).str.extract(r"(\d+)", expand=False)
    df["Level"] = pd.to_numeric(df["Level"], errors="coerce")


    df_long = df.melt(
        id_vars=["Pack/Order#", "Base#", "Level"],
        var_name="Date", value_name="Value"
    )

    df_long["Date"] = pd.to_datetime(df_long["Date"], errors="coerce")
    df_long = df_long.dropna(subset=["Date"])
    df_long["Date"] = df_long["Date"].dt.to_period("M").dt.to_timestamp()

    df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")
    df_long = df_long.dropna(subset=["Value", "Level"])

    return df_long.sort_values(by=["Base#", "Level", "Date"], ascending=False)

# STREAMLIT APP
st.title("Clash Champs Paysheet")
uploaded_file = st.file_uploader("Upload your spreadsheet (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = process_sheet(uploaded_file)

    # -- SIDEBAR FILTERS --
    st.sidebar.header("Filters")

    available_years = sorted(df["Date"].dt.year.unique())
    month_names = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    month = st.sidebar.selectbox("Select month", options=list(month_names.keys()), format_func=lambda x: month_names[x])
    year = st.sidebar.selectbox("Select year", options=available_years)

    # Sidebar image
    st.sidebar.image("bk_img.png", width=200)

    # -- FILTER DATA --
    filtered_df = df[(df["Date"].dt.month == month) & (df["Date"].dt.year == year)]

    st.subheader(f"{month_names[month]} {year}")

    if not filtered_df.empty:
        total_value = filtered_df["Value"].sum()
        st.metric(
            label="💰 Total sales for the month",
            value=f"$ {total_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

        sales_by_level = filtered_df.groupby("Level").agg(
            TotalValue=pd.NamedAgg(column="Value", aggfunc="sum"),
            TotalBases=pd.NamedAgg(column="Base#", aggfunc="count")
        ).reset_index()

        level_order = list(range(9, 18))
        sales_by_level = sales_by_level.set_index("Level").reindex(level_order).fillna(0).reset_index()

        sales_by_level["FormattedValue"] = sales_by_level["TotalValue"].apply(
            lambda x: f"$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

        fig = px.bar(
            sales_by_level,
            x="TotalBases",
            y="Level",
            text="FormattedValue",
            orientation="h",
            title=f"Sales by Level - {month_names[month]} {year}",
            color_discrete_sequence=["#BDB76B"],
            hover_data={"FormattedValue": True, "TotalBases": True, "TotalValue": False}
        )

        fig.update_traces(textposition="outside")

        fig.update_layout(
            width=900,
            height=60 * len(level_order),
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font=dict(color='white', size=14),
            title_x=0.0,
            xaxis=dict(title="Number of Bases Sold", color='white'),
            yaxis=dict(
                title="Level",
                color='white',
                categoryorder="array",
                categoryarray=level_order
            ),
        )

        st.plotly_chart(fig, use_container_width=True)
        st.subheader(f"Filtered data: {month_names[month]} {year}")
        st.dataframe(filtered_df)

    else:
        st.warning("⚠️ No data found for the selected period.")
        st.plotly_chart(px.bar(title="No data for the selected period"), use_container_width=True)
        st.dataframe(pd.DataFrame(columns=df.columns))
