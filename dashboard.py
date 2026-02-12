import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="Lab Timetable Dashboard",
    page_icon="📅",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Load data


@st.cache_data
def load_data():
    df = pd.read_excel("22-5-7-23-Labs.xlsx")

    # Convert time to proper format
    df['Start_Time'] = df['Start'].apply(
        lambda x: f"{x//100:02d}:{x % 100:02d}")
    df['End_Time'] = df['End'].apply(lambda x: f"{x//100:02d}:{x % 100:02d}")
    df['Start_Hour'] = df['Start'] // 100
    df['Duration'] = (df['End'] - df['Start']) // 100 + \
        ((df['End'] - df['Start']) % 100) / 60

    # Map day codes to full names
    day_map = {'U': 'Sunday', 'M': 'Monday', 'T': 'Tuesday',
               'W': 'Wednesday', 'R': 'Thursday', 'S': 'Saturday'}
    df['Day_Full'] = df['Days'].map(day_map).fillna(df['Days'])

    # Create course code
    df['Course'] = df['Subject'] + ' ' + df['Number'].astype(str)

    # Create room identifier
    df['Room_ID'] = 'Bldg ' + \
        df['Bldg'].astype(str) + ' - Room ' + df['Room'].astype(str)

    return df


df = load_data()

# Title
st.title("📅 Lab Timetable Dashboard")
st.markdown("---")

# ============== ANALYTICS SECTION ==============
st.header("📊 Analytics Overview")

# Top metrics row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Lab Sessions", len(df))
with col2:
    st.metric("Unique Courses", df['Course'].nunique())
with col3:
    st.metric("Buildings", df['Bldg'].nunique())
with col4:
    st.metric("Rooms", df['Room_ID'].nunique())
with col5:
    st.metric("Subjects", df['Subject'].nunique())

st.markdown("---")

# Analytics charts row
chart_col1, chart_col2, chart_col3 = st.columns(3)

with chart_col1:
    st.subheader("Sessions by Day")
    day_order = ['Sunday', 'Monday', 'Tuesday',
                 'Wednesday', 'Thursday', 'Saturday']
    day_counts = df['Day_Full'].value_counts().reindex(
        [d for d in day_order if d in df['Day_Full'].values])
    fig_days = px.bar(
        x=day_counts.index,
        y=day_counts.values,
        color=day_counts.values,
        color_continuous_scale='Blues',
        labels={'x': 'Day', 'y': 'Sessions'}
    )
    fig_days.update_layout(
        showlegend=False, coloraxis_showscale=False, height=300)
    st.plotly_chart(fig_days, width="stretch")

with chart_col2:
    st.subheader("Sessions by Hour")
    hour_counts = df['Start_Hour'].value_counts().sort_index()
    fig_hours = px.area(
        x=hour_counts.index,
        y=hour_counts.values,
        labels={'x': 'Hour', 'y': 'Sessions'}
    )
    fig_hours.update_layout(height=300)
    st.plotly_chart(fig_hours, width="stretch")

with chart_col3:
    st.subheader("Top 10 Subjects")
    subject_counts = df['Subject'].value_counts().head(10)
    fig_subjects = px.pie(
        values=subject_counts.values,
        names=subject_counts.index,
        hole=0.4
    )
    fig_subjects.update_layout(height=300)
    st.plotly_chart(fig_subjects, width="stretch")

# Room utilization heatmap
st.subheader("🔥 Room Utilization Heatmap (Sessions per Day)")

# Create pivot table for heatmap
day_order_map = {'U': 0, 'M': 1, 'T': 2, 'W': 3, 'R': 4, 'S': 5}
df['Day_Order'] = df['Days'].map(day_order_map)

# Get top 15 most used rooms for the heatmap
top_rooms = df['Room_ID'].value_counts().head(15).index.tolist()
heatmap_data = df[df['Room_ID'].isin(top_rooms)].groupby(
    ['Room_ID', 'Day_Full']).size().unstack(fill_value=0)

# Reorder columns
day_cols = [d for d in day_order if d in heatmap_data.columns]
heatmap_data = heatmap_data[day_cols]

fig_heatmap = px.imshow(
    heatmap_data.values,
    x=heatmap_data.columns,
    y=heatmap_data.index,
    color_continuous_scale='YlOrRd',
    aspect='auto',
    labels={'color': 'Sessions'}
)
fig_heatmap.update_layout(height=400)
st.plotly_chart(fig_heatmap, width="stretch")

st.markdown("---")

# ============== CALENDAR TIMETABLE SECTION ==============
st.header("📅 Calendar View")

# Filters in a more compact layout
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    selected_building = st.selectbox(
        "Building",
        options=['All'] + sorted(df['Bldg'].unique().tolist())
    )

with filter_col2:
    if selected_building == 'All':
        room_options = sorted(df['Room'].unique().tolist())
    else:
        room_options = sorted(
            df[df['Bldg'] == selected_building]['Room'].unique().tolist())
    selected_room = st.selectbox(
        "Room",
        options=['All'] + room_options
    )

with filter_col3:
    selected_subject = st.selectbox(
        "Subject",
        options=['All'] + sorted(df['Subject'].unique().tolist())
    )

with filter_col4:
    day_order = ['Sunday', 'Monday', 'Tuesday',
                 'Wednesday', 'Thursday', 'Saturday']
    day_options = [d for d in day_order if d in df['Day_Full'].values]
    selected_day = st.selectbox(
        "Day",
        options=['All'] + day_options
    )

# Apply filters
filtered_df = df.copy()
if selected_building != 'All':
    filtered_df = filtered_df[filtered_df['Bldg'] == selected_building]
if selected_room != 'All':
    filtered_df = filtered_df[filtered_df['Room'] == selected_room]
if selected_subject != 'All':
    filtered_df = filtered_df[filtered_df['Subject'] == selected_subject]
if selected_day != 'All':
    filtered_df = filtered_df[filtered_df['Day_Full'] == selected_day]

st.info(
    f"Showing {len(filtered_df)} sessions | Hover over blocks for details")

# Create Google Calendar-style view
if len(filtered_df) > 0:
    # Day order for calendar (columns)
    day_order = ['Sunday', 'Monday', 'Tuesday',
                 'Wednesday', 'Thursday', 'Saturday']
    days_in_data = [
        d for d in day_order if d in filtered_df['Day_Full'].values]

    # Prepare data for efficient timeline rendering
    timeline_df = filtered_df.copy()

    # Create datetime columns for timeline
    day_to_date = {
        'Sunday': '2024-01-07', 'Monday': '2024-01-08', 'Tuesday': '2024-01-09',
        'Wednesday': '2024-01-10', 'Thursday': '2024-01-11', 'Saturday': '2024-01-13'
    }
    timeline_df['Date'] = timeline_df['Day_Full'].map(day_to_date)
    timeline_df['Start_DT'] = pd.to_datetime(
        timeline_df['Date'] + ' ' + timeline_df['Start_Time'])
    timeline_df['End_DT'] = pd.to_datetime(
        timeline_df['Date'] + ' ' + timeline_df['End_Time'])

    # Create hover text
    timeline_df['Hover'] = timeline_df.apply(
        lambda r: f"<b>{r['Course']}</b><br>Section: {r['Section']}<br>Time: {r['Start_Time']}-{r['End_Time']}<br>Room: {r['Room_ID']}<br>Instructor: {r['Name'] if pd.notna(r['Name']) else 'TBA'}",
        axis=1
    )

    # Different view based on whether a specific day is selected
    if selected_day != 'All':
        # Single day view: Y-axis shows rooms so concurrent labs appear side-by-side
        # Sort rooms for consistent ordering
        rooms_sorted = sorted(timeline_df['Room_ID'].unique().tolist())

        fig = px.timeline(
            timeline_df,
            x_start='Start_DT',
            x_end='End_DT',
            y='Room_ID',
            color='Subject',
            hover_name='Course',
            hover_data={'Room_ID': False, 'Start_DT': False, 'End_DT': False,
                        'Section': True, 'Day_Full': True, 'Start_Time': True, 'End_Time': True},
            category_orders={'Room_ID': rooms_sorted},
            color_discrete_sequence=px.colors.qualitative.Set3
        )

        chart_height = max(400, len(rooms_sorted) * 35)
        fig.update_layout(
            title=f'📅 {selected_day} - Lab Schedule by Room',
            xaxis_title='Time',
            yaxis_title='Room',
            height=chart_height,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom",
                        y=1.02, xanchor="right", x=1),
            hovermode='closest'
        )
    else:
        # Weekly view: Y-axis shows days
        fig = px.timeline(
            timeline_df,
            x_start='Start_DT',
            x_end='End_DT',
            y='Day_Full',
            color='Subject',
            hover_name='Course',
            hover_data={'Day_Full': False, 'Start_DT': False, 'End_DT': False,
                        'Section': True, 'Room_ID': True, 'Start_Time': True, 'End_Time': True},
            category_orders={'Day_Full': days_in_data},
            color_discrete_sequence=px.colors.qualitative.Set3
        )

        fig.update_layout(
            title='Weekly Lab Schedule (Hover for details)',
            xaxis_title='Time',
            yaxis_title='',
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom",
                        y=1.02, xanchor="right", x=1),
            hovermode='closest'
        )

    # Format x-axis to show time
    fig.update_xaxes(
        tickformat='%H:%M',
        dtick=3600000  # 1 hour
    )

    st.plotly_chart(fig, width="stretch")

    # Quick stats about filtered data
    st.subheader("📋 Quick Stats")
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    with stat_col1:
        st.metric("Sessions", len(filtered_df))
    with stat_col2:
        st.metric("Courses", filtered_df['Course'].nunique())
    with stat_col3:
        st.metric("Rooms Used", filtered_df['Room_ID'].nunique())
    with stat_col4:
        busiest_day = filtered_df['Day_Full'].value_counts(
        ).idxmax() if len(filtered_df) > 0 else "N/A"
        st.metric("Busiest Day", busiest_day)

    st.markdown("---")

    # Data table (collapsible)
    with st.expander("📑 View Detailed Data Table"):
        display_cols = ['Day_Full', 'Start_Time', 'End_Time',
                        'Room_ID', 'Course', 'Section', 'Name', 'Email']
        st.dataframe(
            filtered_df[display_cols].sort_values(['Day_Full', 'Start_Time']),
            width="stretch",
            height=400
        )

else:
    st.warning("No sessions match the selected filters.")

# Footer
st.markdown("---")
st.caption("Lab Timetable Dashboard | Data loaded from 22-5-7-23-Labs.xlsx")
