from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st


DAY_ORDER = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Saturday"]
DAY_CODE_MAP = {
    "U": "Sunday",
    "M": "Monday",
    "T": "Tuesday",
    "W": "Wednesday",
    "R": "Thursday",
    "S": "Saturday",
}
CALENDAR_START_MINUTES = 6 * 60 + 30
CALENDAR_END_MINUTES = 23 * 60
PIXELS_PER_MINUTE = 1.05
CALENDAR_HEIGHT = int((CALENDAR_END_MINUTES - CALENDAR_START_MINUTES) * PIXELS_PER_MINUTE)
COLOR_SEQUENCE = [
    "#0f766e",
    "#1d4ed8",
    "#b45309",
    "#7c3aed",
    "#be123c",
    "#0f766e",
    "#0369a1",
    "#4338ca",
    "#15803d",
    "#c2410c",
    "#b91c1c",
    "#4f46e5",
]


st.set_page_config(
    page_title="Lab Timetable Dashboard",
    page_icon="Calendar",
    layout="wide",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 2rem;
        }
        .filter-card {
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            border: 1px solid #d9e2ec;
            border-radius: 18px;
            padding: 1rem 1.1rem 0.25rem;
            margin-bottom: 1rem;
        }
        .calendar-shell {
            border: 1px solid #d9e2ec;
            border-radius: 18px;
            overflow: hidden;
            background: #ffffff;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        }
        .calendar-shell.focus-mode {
            box-shadow: 0 20px 48px rgba(15, 23, 42, 0.12);
        }
        .calendar-header {
            display: grid;
            background: linear-gradient(180deg, #f8fafc 0%, #eef4fb 100%);
            border-bottom: 1px solid #d9e2ec;
        }
        .calendar-corner {
            padding: 0.85rem 0.75rem;
            font-size: 0.8rem;
            font-weight: 700;
            color: #52606d;
            border-right: 1px solid #d9e2ec;
        }
        .calendar-day-header {
            padding: 0.8rem 0.55rem 0.75rem;
            border-right: 1px solid #d9e2ec;
            min-width: 170px;
        }
        .calendar-day-header:last-child {
            border-right: none;
        }
        .calendar-day-name {
            font-size: 0.95rem;
            font-weight: 700;
            color: #102a43;
        }
        .calendar-day-count {
            font-size: 0.76rem;
            color: #627d98;
            margin-top: 0.15rem;
        }
        .calendar-scroll {
            overflow-x: auto;
            overflow-y: auto;
            max-height: 980px;
        }
        .calendar-shell.focus-mode .calendar-scroll {
            max-height: calc(100vh - 180px);
        }
        .calendar-shell.focus-mode .calendar-day-header,
        .calendar-shell.focus-mode .calendar-day-column {
            min-width: 210px;
        }
        .calendar-body {
            display: grid;
            background: #ffffff;
        }
        .calendar-times {
            position: relative;
            border-right: 1px solid #d9e2ec;
            background:
                linear-gradient(180deg, rgba(247, 250, 252, 0.96) 0%, rgba(255, 255, 255, 0.98) 100%);
        }
        .calendar-time-label {
            position: absolute;
            right: 0.75rem;
            transform: translateY(-50%);
            font-size: 0.76rem;
            font-weight: 600;
            color: #627d98;
            white-space: nowrap;
        }
        .calendar-day-column {
            position: relative;
            min-width: 170px;
            border-right: 1px solid #e8eef5;
            background: #ffffff;
        }
        .calendar-day-column:last-child {
            border-right: none;
        }
        .calendar-line {
            position: absolute;
            left: 0;
            right: 0;
            border-top: 1px solid #edf2f7;
        }
        .calendar-line.major {
            border-top-color: #d9e2ec;
        }
        .calendar-event {
            position: absolute;
            border-radius: 12px;
            border: 1px solid rgba(15, 23, 42, 0.14);
            color: #ffffff;
            padding: 0.35rem 0.45rem;
            overflow: hidden;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.12);
        }
        .calendar-event-title {
            font-size: 0.76rem;
            font-weight: 700;
            line-height: 1.15;
            margin-bottom: 0.1rem;
        }
        .calendar-event-meta {
            font-size: 0.68rem;
            line-height: 1.2;
            opacity: 0.96;
        }
        .calendar-empty {
            border: 1px dashed #bcccdc;
            border-radius: 16px;
            padding: 1.2rem 1rem;
            background: #f8fbff;
            color: #486581;
            text-align: center;
        }
        .legend-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 0.8rem;
        }
        .legend-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: #f8fafc;
            border: 1px solid #d9e2ec;
            border-radius: 999px;
            padding: 0.28rem 0.6rem;
            font-size: 0.76rem;
            color: #334e68;
        }
        .legend-swatch {
            width: 0.8rem;
            height: 0.8rem;
            border-radius: 999px;
            display: inline-block;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_minutes(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    suffix = "AM" if hours < 12 else "PM"
    display_hour = hours % 12 or 12
    return f"{display_hour}:{mins:02d} {suffix}"


def split_day_codes(day_value: str) -> list[str]:
    clean_value = "".join(ch for ch in str(day_value).strip().upper() if ch.isalpha())
    expanded_days = []

    for code in clean_value:
        if code in DAY_CODE_MAP and DAY_CODE_MAP[code] not in expanded_days:
            expanded_days.append(DAY_CODE_MAP[code])

    return expanded_days


def build_search_text(frame: pd.DataFrame) -> pd.Series:
    columns = [
        "Course",
        "Subject",
        "Number",
        "Section",
        "Room_ID",
        "Room",
        "Bldg",
        "Instructor",
        "Email",
        "Day_Full",
    ]
    searchable = frame[columns].astype(str).replace({"nan": "", "None": ""})
    return searchable.agg(" ".join, axis=1).str.casefold()


@st.cache_data
def load_data(file) -> pd.DataFrame:
    source = file if file is not None else "22-5-7-23-Labs.xlsx"
    df = pd.read_excel(source)

    df["Start"] = pd.to_numeric(df["Start"], errors="coerce")
    df["End"] = pd.to_numeric(df["End"], errors="coerce")
    df = df.dropna(subset=["Start", "End"]).copy()

    text_columns = ["Bldg", "Room", "Days", "Subject", "Number", "Section", "Name", "Email"]
    for column in text_columns:
        if column in df.columns:
            df[column] = df[column].fillna("").astype(str).str.strip()

    df["Start"] = df["Start"].astype(int)
    df["End"] = df["End"].astype(int)
    df["Start_Minutes"] = (df["Start"] // 100) * 60 + (df["Start"] % 100)
    df["End_Minutes"] = (df["End"] // 100) * 60 + (df["End"] % 100)
    df = df[df["End_Minutes"] > df["Start_Minutes"]].copy()

    df["Start_Time"] = df["Start_Minutes"].apply(format_minutes)
    df["End_Time"] = df["End_Minutes"].apply(format_minutes)
    df["Start_Hour"] = df["Start_Minutes"] // 60
    df["Duration_Hours"] = (df["End_Minutes"] - df["Start_Minutes"]) / 60.0
    df["Duration_Label"] = (
        ((df["End_Minutes"] - df["Start_Minutes"]) // 60).astype(int).astype(str)
        + "h "
        + ((df["End_Minutes"] - df["Start_Minutes"]) % 60).astype(int).astype(str).str.zfill(2)
        + "m"
    )

    df["Course"] = (df["Subject"] + " " + df["Number"]).str.strip()
    df["Instructor"] = df["Name"].replace("", pd.NA).fillna("Unassigned")
    df["Email"] = df["Email"].replace("nan", "")
    df["Room_ID"] = "Bldg " + df["Bldg"] + " - Room " + df["Room"]
    df["Day_List"] = df["Days"].apply(split_day_codes)
    df = df[df["Day_List"].str.len() > 0].explode("Day_List").rename(columns={"Day_List": "Day_Full"})
    df["Day_Full"] = pd.Categorical(df["Day_Full"], categories=DAY_ORDER, ordered=True)

    searchable = build_search_text(df)
    df["Search_Text"] = searchable
    return df


def apply_filters(data: pd.DataFrame, filters: dict, skip_key: str | None = None) -> pd.DataFrame:
    filtered = data

    mapping = {
        "days": "Day_Full",
        "buildings": "Bldg",
        "rooms": "Room_ID",
        "subjects": "Subject",
        "courses": "Course",
        "instructors": "Instructor",
    }

    for filter_key, column in mapping.items():
        if filter_key == skip_key:
            continue
        values = filters.get(filter_key, [])
        if values:
            filtered = filtered[filtered[column].isin(values)]

    if skip_key != "search":
        search_value = filters.get("search", "").strip().casefold()
        if search_value:
            filtered = filtered[filtered["Search_Text"].str.contains(search_value, na=False)]

    return filtered


def available_options(data: pd.DataFrame, filters: dict, key: str) -> list[str]:
    filtered = apply_filters(data, filters, skip_key=key)
    column = {
        "days": "Day_Full",
        "buildings": "Bldg",
        "rooms": "Room_ID",
        "subjects": "Subject",
        "courses": "Course",
        "instructors": "Instructor",
    }[key]

    values = filtered[column].dropna().astype(str).unique().tolist()
    if key == "days":
        values = [day for day in DAY_ORDER if day in values]
    else:
        values = sorted(values)
    return values


def sanitize_selection(options: list[str], session_key: str) -> None:
    st.session_state.setdefault(session_key, [])
    st.session_state[session_key] = [
        value for value in st.session_state[session_key] if value in options
    ]


def assign_day_layout(day_frame: pd.DataFrame) -> pd.DataFrame:
    if day_frame.empty:
        return day_frame.copy()

    working = day_frame.sort_values(
        ["Display_Start", "Display_End", "Course", "Room_ID", "Section"]
    ).copy()

    cluster_data: list[list[int]] = []
    current_cluster: list[int] = []
    current_cluster_end = -1

    for idx, row in working.iterrows():
        if current_cluster and row["Display_Start"] >= current_cluster_end:
            cluster_data.append(current_cluster)
            current_cluster = [idx]
            current_cluster_end = row["Display_End"]
        else:
            current_cluster.append(idx)
            current_cluster_end = max(current_cluster_end, row["Display_End"])

    if current_cluster:
        cluster_data.append(current_cluster)

    working["Overlap_Column"] = 0
    working["Overlap_Count"] = 1

    for cluster in cluster_data:
        column_end_times: list[int] = []
        assigned_columns: dict[int, int] = {}

        for idx in cluster:
            start_value = int(working.at[idx, "Display_Start"])
            end_value = int(working.at[idx, "Display_End"])
            assigned_column = None

            for column_index, last_end in enumerate(column_end_times):
                if start_value >= last_end:
                    assigned_column = column_index
                    column_end_times[column_index] = end_value
                    break

            if assigned_column is None:
                assigned_column = len(column_end_times)
                column_end_times.append(end_value)

            assigned_columns[idx] = assigned_column

        overlap_count = max(1, len(column_end_times))
        for idx in cluster:
            working.at[idx, "Overlap_Column"] = assigned_columns[idx]
            working.at[idx, "Overlap_Count"] = overlap_count

    return working


def subject_colors(subjects: list[str]) -> dict[str, str]:
    return {
        subject: COLOR_SEQUENCE[index % len(COLOR_SEQUENCE)]
        for index, subject in enumerate(sorted(subjects))
    }


def build_legend(color_map: dict[str, str], subjects: list[str]) -> str:
    if not subjects:
        return ""

    chips = []
    for subject in subjects[:12]:
        chips.append(
            """
            <span class="legend-chip">
                <span class="legend-swatch" style="background:{color};"></span>
                {label}
            </span>
            """.format(color=color_map[subject], label=escape(subject))
        )

    if len(subjects) > 12:
        chips.append('<span class="legend-chip">+ more subjects</span>')

    return '<div class="legend-row">' + "".join(chips) + "</div>"


def build_calendar_html(data: pd.DataFrame, visible_days: list[str], focus_mode: bool = False) -> str:
    if data.empty or not visible_days:
        return '<div class="calendar-empty">No sessions match the current filters.</div>'

    schedule = data.copy()
    schedule["Display_Start"] = schedule["Start_Minutes"].clip(
        lower=CALENDAR_START_MINUTES, upper=CALENDAR_END_MINUTES
    )
    schedule["Display_End"] = schedule["End_Minutes"].clip(
        lower=CALENDAR_START_MINUTES, upper=CALENDAR_END_MINUTES
    )
    schedule = schedule[schedule["Display_End"] > schedule["Display_Start"]].copy()

    if schedule.empty:
        return (
            '<div class="calendar-empty">'
            "The filtered sessions fall outside the visible range of 6:30 AM to 11:00 PM."
            "</div>"
        )

    color_map = subject_colors(schedule["Subject"].astype(str).unique().tolist())
    header_columns = f"88px repeat({len(visible_days)}, minmax(170px, 1fr))"

    header_html = ['<div class="calendar-header" style="grid-template-columns: ' + header_columns + ';">']
    header_html.append('<div class="calendar-corner">Time</div>')

    for day in visible_days:
        count = int((schedule["Day_Full"].astype(str) == day).sum())
        header_html.append(
            """
            <div class="calendar-day-header">
                <div class="calendar-day-name">{day}</div>
                <div class="calendar-day-count">{count} session{suffix}</div>
            </div>
            """.format(
                day=escape(day),
                count=count,
                suffix="" if count == 1 else "s",
            )
        )

    header_html.append("</div>")

    time_labels = []
    for minutes in range(CALENDAR_START_MINUTES, CALENDAR_END_MINUTES + 1, 60):
        top = (minutes - CALENDAR_START_MINUTES) * PIXELS_PER_MINUTE
        time_labels.append(
            '<div class="calendar-time-label" style="top: {top}px;">{label}</div>'.format(
                top=top,
                label=escape(format_minutes(minutes)),
            )
        )

    lines = []
    for minutes in range(CALENDAR_START_MINUTES, CALENDAR_END_MINUTES + 1, 30):
        top = (minutes - CALENDAR_START_MINUTES) * PIXELS_PER_MINUTE
        major = " major" if (minutes - CALENDAR_START_MINUTES) % 60 == 0 else ""
        lines.append('<div class="calendar-line{major}" style="top: {top}px;"></div>'.format(major=major, top=top))

    day_columns_html = []
    schedule["Day_Full"] = schedule["Day_Full"].astype(str)

    for day in visible_days:
        day_frame = assign_day_layout(schedule[schedule["Day_Full"] == day])
        day_events = []

        for _, row in day_frame.iterrows():
            top = (row["Display_Start"] - CALENDAR_START_MINUTES) * PIXELS_PER_MINUTE
            height = max(24, (row["Display_End"] - row["Display_Start"]) * PIXELS_PER_MINUTE - 4)
            width_pct = 100 / max(1, int(row["Overlap_Count"]))
            gap = 1.6
            left_pct = row["Overlap_Column"] * width_pct + gap / 2
            usable_width = max(10, width_pct - gap)

            tooltip_parts = [
                str(row["Course"]).strip(),
                f"Section {row['Section']}",
                str(row["Room_ID"]).strip(),
                f"{row['Start_Time']} - {row['End_Time']}",
                str(row["Instructor"]).strip(),
            ]
            tooltip = escape(" | ".join(part for part in tooltip_parts if part and part != "Section "))
            room_label = escape(str(row["Room"]).strip())
            section_label = escape(str(row["Section"]).strip())
            title = escape(str(row["Course"]).strip())
            time_range = escape(f"{row['Start_Time']} - {row['End_Time']}")
            instructor = escape(str(row["Instructor"]).strip())
            background = color_map[str(row["Subject"]).strip()]

            day_events.append(
                """
                <div class="calendar-event" title="{tooltip}" style="top:{top}px; left:{left}%; width:{width}%; height:{height}px; background:{background};">
                    <div class="calendar-event-title">{title}</div>
                    <div class="calendar-event-meta">Sec {section} | Room {room}</div>
                    <div class="calendar-event-meta">{time_range}</div>
                    <div class="calendar-event-meta">{instructor}</div>
                </div>
                """.format(
                    tooltip=tooltip,
                    top=top,
                    left=left_pct,
                    width=usable_width,
                    height=height,
                    background=background,
                    title=title,
                    section=section_label,
                    room=room_label,
                    time_range=time_range,
                    instructor=instructor,
                )
            )

        day_columns_html.append(
            '<div class="calendar-day-column" style="height: {height}px;">{lines}{events}</div>'.format(
                height=CALENDAR_HEIGHT,
                lines="".join(lines),
                events="".join(day_events),
            )
        )

    body_html = """
        <div class="calendar-scroll">
            <div class="calendar-body" style="grid-template-columns: {columns};">
                <div class="calendar-times" style="height: {height}px;">{time_labels}</div>
                {day_columns}
            </div>
        </div>
    """.format(
        columns=header_columns,
        height=CALENDAR_HEIGHT,
        time_labels="".join(time_labels),
        day_columns="".join(day_columns_html),
    )

    subjects = sorted(schedule["Subject"].astype(str).unique().tolist())
    legend_html = build_legend(color_map, subjects)

    shell_class = "calendar-shell focus-mode" if focus_mode else "calendar-shell"

    return '<div class="{shell_class}">{legend}{header}{body}</div>'.format(
        shell_class=shell_class,
        legend=legend_html,
        header="".join(header_html),
        body=body_html,
    )


st.sidebar.header("Upload Lab Timetable File")
uploaded_file = st.sidebar.file_uploader(
    "Choose an Excel file (same structure as the default)",
    type=["xlsx"],
)

df = load_data(uploaded_file)

st.title("Lab Timetable Dashboard")
st.caption("Interactive lab schedule analytics with improved filtering and a day-grid calendar view.")
calendar_focus_mode = st.toggle(
    "Calendar focus mode",
    key="calendar_focus_mode",
    help="Hide the analytics blocks and give the calendar a larger, more full-screen layout.",
)

filter_state = {
    "days": st.session_state.get("filter_days", []),
    "buildings": st.session_state.get("filter_buildings", []),
    "rooms": st.session_state.get("filter_rooms", []),
    "subjects": st.session_state.get("filter_subjects", []),
    "courses": st.session_state.get("filter_courses", []),
    "instructors": st.session_state.get("filter_instructors", []),
    "search": st.session_state.get("filter_search", ""),
}

day_options = available_options(df, filter_state, "days")
building_options = available_options(df, filter_state, "buildings")
room_options = available_options(df, filter_state, "rooms")
subject_options = available_options(df, filter_state, "subjects")
course_options = available_options(df, filter_state, "courses")
instructor_options = available_options(df, filter_state, "instructors")

sanitize_selection(day_options, "filter_days")
sanitize_selection(building_options, "filter_buildings")
sanitize_selection(room_options, "filter_rooms")
sanitize_selection(subject_options, "filter_subjects")
sanitize_selection(course_options, "filter_courses")
sanitize_selection(instructor_options, "filter_instructors")

active_filters = {
    "days": st.session_state.get("filter_days", []),
    "buildings": st.session_state.get("filter_buildings", []),
    "rooms": st.session_state.get("filter_rooms", []),
    "subjects": st.session_state.get("filter_subjects", []),
    "courses": st.session_state.get("filter_courses", []),
    "instructors": st.session_state.get("filter_instructors", []),
    "search": st.session_state.get("filter_search", ""),
}

filtered_df = apply_filters(df, active_filters).copy()
filtered_df = filtered_df.sort_values(["Day_Full", "Start_Minutes", "Bldg", "Room", "Course"])

if filtered_df.empty:
    st.warning("No sessions match the selected filters.")
    st.stop()

if not calendar_focus_mode:
    st.subheader("Analytics Overview")
    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
    with metric_col1:
        st.metric("Sessions", len(filtered_df))
    with metric_col2:
        st.metric("Courses", filtered_df["Course"].nunique())
    with metric_col3:
        st.metric("Buildings", filtered_df["Bldg"].nunique())
    with metric_col4:
        st.metric("Rooms", filtered_df["Room_ID"].nunique())
    with metric_col5:
        st.metric("Instructors", filtered_df["Instructor"].nunique())

    chart_col1, chart_col2, chart_col3 = st.columns(3)

    with chart_col1:
        st.markdown("**Sessions by Day**")
        day_counts = (
            filtered_df["Day_Full"]
            .astype(str)
            .value_counts()
            .reindex([day for day in DAY_ORDER if day in filtered_df["Day_Full"].astype(str).values], fill_value=0)
        )
        fig_days = px.bar(
            x=day_counts.index,
            y=day_counts.values,
            color=day_counts.values,
            color_continuous_scale="Blues",
            labels={"x": "Day", "y": "Sessions"},
        )
        fig_days.update_layout(height=300, showlegend=False, coloraxis_showscale=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_days, width="stretch")

    with chart_col2:
        st.markdown("**Sessions by Start Time**")
        time_counts = filtered_df.groupby("Start_Time", observed=False).size().reset_index(name="Sessions")
        time_counts["Sort_Minutes"] = time_counts["Start_Time"].map(
            filtered_df.drop_duplicates("Start_Time").set_index("Start_Time")["Start_Minutes"]
        )
        time_counts = time_counts.sort_values("Sort_Minutes")
        fig_times = px.area(
            time_counts,
            x="Start_Time",
            y="Sessions",
            labels={"Start_Time": "Start Time", "Sessions": "Sessions"},
        )
        fig_times.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_times, width="stretch")

    with chart_col3:
        st.markdown("**Top Subjects**")
        subject_counts = filtered_df["Subject"].value_counts().head(10).sort_values(ascending=True)
        fig_subjects = px.bar(
            x=subject_counts.values,
            y=subject_counts.index,
            orientation="h",
            labels={"x": "Sessions", "y": "Subject"},
            color=subject_counts.values,
            color_continuous_scale="Teal",
        )
        fig_subjects.update_layout(height=300, showlegend=False, coloraxis_showscale=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_subjects, width="stretch")

    st.markdown("**Room Utilization Heatmap**")
    top_rooms = filtered_df["Room_ID"].value_counts().head(15).index.tolist()
    heatmap_data = (
        filtered_df[filtered_df["Room_ID"].isin(top_rooms)]
        .groupby(["Room_ID", "Day_Full"], observed=False)
        .size()
        .unstack(fill_value=0)
    )
    heatmap_columns = [day for day in DAY_ORDER if day in heatmap_data.columns.astype(str).tolist()]
    heatmap_data = heatmap_data.reindex(columns=heatmap_columns, fill_value=0)

    fig_heatmap = px.imshow(
        heatmap_data.values,
        x=heatmap_data.columns.astype(str),
        y=heatmap_data.index.astype(str),
        color_continuous_scale="YlOrRd",
        aspect="auto",
        labels={"color": "Sessions"},
    )
    fig_heatmap.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_heatmap, width="stretch")

with st.container(border=True):
    st.subheader("Calendar Filters")
    st.caption("Leave any filter empty to keep all values. Options update based on the rest of your current selections.")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        st.multiselect("Days", options=day_options, key="filter_days")
        st.multiselect("Buildings", options=building_options, key="filter_buildings")

    with filter_col2:
        st.multiselect("Rooms", options=room_options, key="filter_rooms")
        st.multiselect("Subjects", options=subject_options, key="filter_subjects")

    with filter_col3:
        st.multiselect("Courses", options=course_options, key="filter_courses")
        st.multiselect("Instructors", options=instructor_options, key="filter_instructors")

    bottom_col1, bottom_col2 = st.columns([3, 1])
    with bottom_col1:
        st.text_input(
            "Quick search",
            key="filter_search",
            placeholder="Search by course, section, room, building, instructor, or email",
        )
    with bottom_col2:
        st.write("")
        if st.button("Clear all filters", width="stretch"):
            st.session_state["filter_days"] = []
            st.session_state["filter_buildings"] = []
            st.session_state["filter_rooms"] = []
            st.session_state["filter_subjects"] = []
            st.session_state["filter_courses"] = []
            st.session_state["filter_instructors"] = []
            st.session_state["filter_search"] = ""
            st.rerun()

st.subheader("Calendar View")
visible_days = [day for day in DAY_ORDER if day in filtered_df["Day_Full"].astype(str).unique().tolist()]
st.info(f"Showing {len(filtered_df)} of {len(df)} session entries in the expanded day-by-day schedule.")
if calendar_focus_mode:
    st.caption("Focus mode is on. Analytics cards are hidden and the calendar is expanded to use more of the screen.")
else:
    st.caption("Day grid shown from 6:30 AM to 11:00 PM. Overlapping sessions are placed side by side inside each day.")
st.html(build_calendar_html(filtered_df, visible_days, focus_mode=calendar_focus_mode))

if not calendar_focus_mode:
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
    with quick_col1:
        st.metric("Visible Days", len(visible_days))
    with quick_col2:
        st.metric("Average Daily Sessions", round(len(filtered_df) / max(1, len(visible_days)), 1))
    with quick_col3:
        st.metric("Longest Session", round(float(filtered_df["Duration_Hours"].max()), 2))
    with quick_col4:
        busiest_day = filtered_df["Day_Full"].astype(str).value_counts().idxmax()
        st.metric("Busiest Day", busiest_day)

    with st.expander("View Detailed Data Table"):
        display_columns = [
            "Day_Full",
            "Start_Time",
            "End_Time",
            "Bldg",
            "Room",
            "Room_ID",
            "Subject",
            "Number",
            "Course",
            "Section",
            "Instructor",
            "Email",
            "Days",
        ]
        st.dataframe(
            filtered_df[display_columns],
            width="stretch",
            height=420,
            hide_index=True,
        )

st.caption("Lab Timetable Dashboard | Data loaded from 22-5-7-23-Labs.xlsx")
