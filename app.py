import streamlit as st
import pandas as pd
import plotly.express as px

st.title("EC2 Instance EDA Dashboard")
df = pd.read_csv("ec2dataset.csv")
st.header("Dataset Overview")
st.write("Dataset Preview")
st.dataframe(df)

st.subheader("Dataset Information")
col1, col2, col3 = st.columns(3)
col1.metric("Number of Instances", len(df))
col2.metric("Number of Columns", len(df.columns))
col3.metric("Missing Values", df.isna().sum().sum())

st.subheader("Dataset Structure")
st.write("Columns:")
st.write(df.columns.tolist())
st.subheader("Data Types")
st.write(df.dtypes)

df["Memory_GiB"] = (
    df["Instance Memory"]
    .str.extract(r"([\d.]+)")
    .astype(float)
)

df["vCPU_Count"] = (
    df["vCPUs"]
    .str.extract(r"(\d+)")
    .astype(float)
)

def clean_price(value):
    if pd.isna(value):
        return None
    value = str(value)
    if "unavailable" in value.lower():
        return None
    return float(
        value.replace("$", "")
        .replace("hourly", "")
        .strip()
    )

price_columns = [
    "On Demand",
    "Linux Reserved cost",
    "Linux Spot Minimum cost",
    "Windows On Demand cost",
    "Windows Reserved cost"
]

for column in price_columns:
    df[column + "_USD"] = df[column].apply(clean_price)
df["Monthly_On_Demand"] = df["On Demand_USD"] * 730
# Calculate cost-analysis columns
df["Cost_Per_GiB"] = (
    df["On Demand_USD"] /
    df["Memory_GiB"]
)

df["Cost_Per_vCPU"] = (
    df["On Demand_USD"] /
    df["vCPU_Count"]
)

df["Memory_per_vCPU"] = (
    df["Memory_GiB"] /
    df["vCPU_Count"]
)


# Categorize instance storage
def categorize_storage(value):
    if pd.isna(value):
        return "Other"

    storage = str(value).upper()

    # Check NVMe before SSD because some values contain both words
    if "NVME" in storage:
        return "NVMe"
    elif "SSD" in storage:
        return "SSD"
    elif "HDD" in storage:
        return "HDD"
    elif "EBS" in storage:
        return "EBS"
    else:
        return "Other"


df["Storage_Type"] = df["Instance Storage"].apply(
    categorize_storage
)

st.subheader("Monthly On-Demand Cost")

st.dataframe(
    df[
    [
        "Name",
        "API Name",
        "Memory_GiB",
        "vCPU_Count",
        "On Demand_USD",
        "Monthly_On_Demand"
                            
    ]
    ]
)

st.sidebar.header("Interactive Filters")

# Memory filter
max_memory = float(
    df["Memory_GiB"].dropna().max()
)

memory_filter = st.sidebar.slider(
    "Maximum Memory (GiB)",
    min_value=0.5,
    max_value=max_memory,
    value=max_memory
)

# vCPU filter
cpu_values = sorted(
    df["vCPU_Count"]
    .dropna()
    .unique()
    .tolist()
)

selected_cpu = st.sidebar.multiselect(
    "vCPU Count",
    options=cpu_values,
    default=cpu_values
)

# Network-performance filter
network_values = sorted(
    df["Network Performance"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

selected_network = st.sidebar.multiselect(
    "Network Performance",
    options=network_values,
    default=network_values
)

# Storage filter
storage_values = [
    storage_type
    for storage_type in ["EBS", "SSD", "NVMe", "HDD", "Other"]
    if storage_type in df["Storage_Type"].unique()
]

selected_storage = st.sidebar.multiselect(
    "Storage Type",
    options=storage_values,
    default=storage_values
)

# Maximum hourly-price filter
max_hourly_price = float(
    df["On Demand_USD"]
    .dropna()
    .max()
)

hourly_price_filter = st.sidebar.slider(
    "Maximum Hourly Price ($)",
    min_value=0.0,
    max_value=max_hourly_price,
    value=max_hourly_price,
    step=0.01
)

# Maximum monthly-cost filter
max_monthly_cost = float(
    df["Monthly_On_Demand"]
    .dropna()
    .max()
)

monthly_cost_filter = st.sidebar.slider(
    "Maximum Monthly Cost ($)",
    min_value=0.0,
    max_value=max_monthly_cost,
    value=max_monthly_cost,
    step=10.0
)

# Apply every selected filter
filtered_df = df[
    (df["Memory_GiB"] <= memory_filter) &
    (df["vCPU_Count"].isin(selected_cpu)) &
    (
        df["Network Performance"]
        .astype(str)
        .isin(selected_network)
    ) &
    (df["Storage_Type"].isin(selected_storage)) &
    (df["On Demand_USD"] <= hourly_price_filter) &
    (df["Monthly_On_Demand"] <= monthly_cost_filter)
].copy()

st.subheader("Filtered EC2 Instances")

st.write(
    f"{len(filtered_df)} instances found"
)

st.dataframe(
    filtered_df,
    use_container_width=True
)

# Prevent errors if the filters return no results
if filtered_df.empty:
    st.warning(
        "No EC2 instances match the selected filters. "
        "Increase one or more filter values."
    )
    st.stop()

st.subheader("Key Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Number of Instances",
    len(filtered_df)
)

col2.metric(
    "Average Memory",
    f"{filtered_df['Memory_GiB'].mean():.2f} GiB"
)

col3.metric(
    "Average vCPUs",
    f"{filtered_df['vCPU_Count'].mean():.1f}"
)

col4.metric(
    "Average Hourly Cost",
    f"${filtered_df['On Demand_USD'].mean():.4f}"
)

col5, col6, col7 = st.columns(3)

col5.metric(
    "Average Monthly Cost",
    f"${filtered_df['Monthly_On_Demand'].mean():.2f}"
)

col6.metric(
    "Average Cost per GiB",
    f"${filtered_df['Cost_Per_GiB'].mean():.4f}"
)

col7.metric(
    "Average Cost per vCPU",
    f"${filtered_df['Cost_Per_vCPU'].mean():.4f}"
)
st.subheader("Exploratory Data Analysis")
st.subheader("Memory Distribution")
fig = px.histogram(
    filtered_df,
    x = "Memory_GiB",
    nbins = 30,
    title = "Distirbution of EC2 Memory"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("vCPU Distribution")
fig = px.histogram(
    filtered_df,
    x="vCPU_Count",
    title="Distribution of vCPUs"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Memory vs vCPUs")
fig = px.scatter(
    filtered_df,
    x="vCPU_Count",
    y="Memory_GiB",
    hover_name="API Name",
    hover_data=["On Demand_USD"],
    title="EC2 Memory vs vCPU"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Memory vs On-Demand Cost")

fig = px.scatter(
    filtered_df,
    x="Memory_GiB",
    y="On Demand_USD",
    hover_name="API Name",
    size="vCPU_Count",
    title="Memory vs EC2 On-Demand Cost"
)

st.plotly_chart(fig, use_container_width=True)

st.header("EC2 Cost Analysis")
st.subheader("Lowest-Cost EC2 Instances")
cheapest = (
    filtered_df
    .sort_values("On Demand_USD")
    [
        [
            "Name",
            "API Name",
            "Memory_GiB",
            "vCPU_Count",
            "On Demand_USD",
            "Monthly_On_Demand"
        ]
    ]
    .head(10)
)

st.dataframe(cheapest)

st.subheader("Highest-Cost EC2 Instances")
most_expensive = (
    filtered_df
    .sort_values(
        "On Demand_USD",
        ascending=False
    )
    [
        [
            "Name",
            "API Name",
            "Memory_GiB",
            "vCPU_Count",
            "On Demand_USD",
            "Monthly_On_Demand"
        ]
    ]
    .head(10)
)

st.dataframe(most_expensive)

pricing = filtered_df[
    [
        "Name",
        "API Name",
        "On Demand_USD",
        "Linux Reserved cost_USD",
        "Linux Spot Minimum cost_USD",
        "Windows On Demand cost_USD",
        "Windows Reserved cost_USD"
    ]
]

st.subheader("EC2 Pricing Comparison")
st.dataframe(pricing)

selected_instance = st.selectbox(
    "Select an EC2 Instance",
    filtered_df["API Name"]
    .dropna()
    .unique()
)
instance = filtered_df[
    filtered_df["API Name"] == selected_instance
].iloc[0]

pricing_data = pd.DataFrame({
    "Pricing Model": [
        "On Demand",
        "Linux Reserved",
        "Linux Spot"
    ],
    "Hourly Cost": [
        instance["On Demand_USD"],
        instance["Linux Reserved cost_USD"],
        instance["Linux Spot Minimum cost_USD"]
    ]
})

pricing_data = pricing_data.dropna()
pricing_data["Monthly Cost"] = (
    pricing_data["Hourly Cost"] * 730
)

fig = px.bar(
    pricing_data,
    x="Pricing Model",
    y="Hourly Cost",
    title=f"Pricing Comparison: {selected_instance}"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.dataframe(pricing_data)

st.subheader("Cost Efficiency Analysis")

efficiency = (
    filtered_df
    .sort_values("Cost_Per_GiB")
    [
        [
            "Name",
            "API Name",
            "Memory_GiB",
            "vCPU_Count",
            "On Demand_USD",
            "Monthly_On_Demand",
            "Cost_Per_GiB",
            "Cost_Per_vCPU"
        ]
    ]
    .head(15)
)

st.dataframe(
    efficiency,
    use_container_width=True
)

st.subheader("Instances with High Memory per vCPU")

high_memory_ratio = (
    filtered_df
    .sort_values(
        "Memory_per_vCPU",
        ascending=False
    )
    [
        [
            "Name",
            "API Name",
            "Memory_GiB",
            "vCPU_Count",
            "Memory_per_vCPU",
            "On Demand_USD",
            "Monthly_On_Demand"
        ]
    ]
    .head(15)
)

st.dataframe(
    high_memory_ratio,
    use_container_width=True
)

st.subheader("Cost per GiB of Memory")

efficiency = (
    filtered_df
    .sort_values("Cost_Per_GiB")
    [
        [
            "Name",
            "API Name",
            "Memory_GiB",
            "vCPU_Count",
            "On Demand_USD",
            "Cost_Per_GiB"
        ]
    ]
    .head(15)
)

st.dataframe(efficiency)


csv = filtered_df.to_csv(index=False)

st.download_button(
    label="Download Filtered Dataset",
    data=csv,
    file_name="filtered_ec2_instances.csv",
    mime="text/csv"
)
