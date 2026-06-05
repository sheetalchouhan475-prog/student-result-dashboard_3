import streamlit as st
import pdfplumber
import pandas as pd
import re
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(
    page_title="RGPV Result Analysis",
    layout="wide"
)

st.markdown(
    "<h1 style='text-align:center;'>Result Analysis</h1>",
    unsafe_allow_html=True
)




uploaded_files = st.file_uploader(
    "Upload RGPV Marksheets",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:

    student_rows = []

    for pdf_file in uploaded_files:

        text = ""

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

        # -----------------------
        # Student Information
        # -----------------------

        roll_match = re.search(
            r'Roll No\.\s*([A-Z0-9]+)',
            text
        )

        course_match = re.search(
            r'Course\s+([A-Za-z\. ]+)',
            text
        )

        branch_match = re.search(
            r'Branch\s+([A-Z& ]+)',
            text
        )

        semester_match = re.search(
            r'Semester\s+(\d+)',
            text
        )

        name_match = re.search(
            r'Name\s+(.*?)\s+Roll\s+No',
            text,
            re.DOTALL
        )

        name = (
            " ".join(name_match.group(1).split())
            if name_match
            else pdf_file.name.replace(".pdf", "")
        )

        roll = roll_match.group(1).strip() if roll_match else "N/A"
        course = course_match.group(1).strip() if course_match else "N/A"
        branch = branch_match.group(1).strip() if branch_match else "N/A"
        semester = semester_match.group(1).strip() if semester_match else "N/A"

        # -----------------------
        # Subject Processing
        # -----------------------

        theory_count = 0
        practical_count = 0

        row = {
            "Name": name,
            "Roll No": roll,
            "Course": course,
            "Branch": branch,
            "Semester": semester
        }

        lines = text.split("\n")

        for line in lines:

           match = re.search(
                r'([A-Z]{2,4}\d{2,4})\s*-\s*\[(T|P)\].*?(A\s*\+|A|B\s*\+|B|C\s*\+|C|D|F)',
                line
            )

        if match:

                subject_code = match.group(1)
                paper_type = match.group(2)
                grade = match.group(3).replace(" ", "")

                subject_name = f"{subject_code}-[{paper_type}]"

                row[subject_name] = grade

                if paper_type == "T":
                    theory_count += 1
                else:
                    practical_count += 1

        row["No of Theory Papers"] = theory_count
        row["No of Practical Papers"] = practical_count

        student_rows.append(row)

    # -----------------------
    # Final DataFrame
    # -----------------------

    final_df = pd.DataFrame(student_rows)

    base_cols = [
        "Name",
        "Roll No",
        "Course",
        "Branch",
        "Semester",
        "No of Theory Papers",
        "No of Practical Papers"
    ]

    subject_cols = [
        c for c in final_df.columns
        if c not in base_cols
    ]

    final_df = final_df[
        base_cols + sorted(subject_cols)
    ]

    st.success(
        f"{len(uploaded_files)} Marksheets Processed Successfully"
    )
course_value = final_df["Course"].iloc[0]
branch_value = final_df["Branch"].iloc[0]
semester_value = final_df["Semester"].iloc[0]

st.markdown(
    f"""
    <h4 style='text-align:center;'>
    Course: {course_value} |
    Branch: {branch_value} |
    Semester: {semester_value}
    </h4>
    """,
    unsafe_allow_html=True
)
    
st.subheader("Student Result Table")

st.dataframe(
        final_df,
        use_container_width=True
    )

    # -----------------------
    # Excel Download
    # -----------------------

excel_buffer = BytesIO()

with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        final_df.to_excel(
            writer,
            sheet_name="Results",
            index=False
        )

st.download_button(
        label="Download Excel File",
        data=excel_buffer.getvalue(),
        file_name="RGPV_Final_Result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
st.divider()
grade_points = {
    "A+": 10,
    "A": 9,
    "B+": 8,
    "B": 7,
    "C+": 6,
    "C": 5,
    "D": 4,
    "F": 0
}

theory_subjects = [
    col for col in subject_cols
    if col.endswith("-[T]")
]

subject_performance = {}

for subject in theory_subjects:

    grades = final_df[subject].dropna()

    scores = []

    for grade in grades:

        grade = str(grade).strip()

        if grade in grade_points:
            scores.append(
                grade_points[grade]
            )

    if len(scores):

        subject_performance[subject] = (
            sum(scores) / len(scores)
        )

performance_df = pd.DataFrame({
    "Subject": list(subject_performance.keys()),
    "Average Score": list(subject_performance.values())
})

if len(performance_df):

    performance_df = performance_df.sort_values(
        by="Average Score",
        ascending=False
    )

    # -----------------------
    # Subject Wise Pie Chart
    # -----------------------

    

    # -----------------------
    # Theory Subject Analysis
    # -----------------------
col1, col2 = st.columns([1,2])

with col1:

    st.subheader("Summary")

    st.metric(
        "No of Students",
        len(final_df)
    )

    st.metric(
        "No of Theory Papers",
        int(final_df["No of Theory Papers"].sum())
    )

    st.metric(
        "No of Practical Papers",
        int(final_df["No of Practical Papers"].sum())
    )

    if len(performance_df):

        st.success(
            f"Best Theory Paper: {performance_df.iloc[0]['Subject']}"
        )

        st.error(
            f"Weakest Theory Paper: {performance_df.iloc[-1]['Subject']}"
        )

with col2:

    st.subheader(
        "Theory Papers Performance"
    )

    if len(performance_df):

        fig_bar, ax_bar = plt.subplots(
            figsize=(10,5)
        )

        ax_bar.bar(
            performance_df["Subject"],
            performance_df["Average Score"]
        )

        ax_bar.set_ylabel(
            "Average Score"
        )

        ax_bar.tick_params(
            axis='x',
            rotation=90
        )

        st.pyplot(fig_bar)

    #--------------------Theory Pie Chart------------
st.divider()

st.subheader(
    "Theory Subject Grade Distribution"
)
for i in range(0, len(theory_subjects), 4):

    cols = st.columns(4)

    for j, subject in enumerate(
        theory_subjects[i:i+4]
    ):

        with cols[j]:

            grades = final_df[
                subject
            ].dropna()

            if len(grades) == 0:
                continue

            grade_counts = grades.value_counts()

            fig, ax = plt.subplots(
                figsize=(4,4)
            )

            ax.pie(
                grade_counts.values,
                labels=grade_counts.index,
                autopct="%1.1f%%"
            )

            ax.set_title(subject)

            st.pyplot(fig)

            img = BytesIO()

            fig.savefig(
                img,
                format="png"
            )

            img.seek(0)

            st.download_button(
                f"Download {subject}",
                img,
                file_name=f"{subject}.png",
                mime="image/png",
                key=f"t_{subject}"
            )
for i in range(0, len(theory_subjects), 4):

    cols = st.columns(4)

    for j, subject in enumerate(
        theory_subjects[i:i+4]
    ):

        with cols[j]:

            grades = final_df[
                subject
            ].dropna()

            if len(grades) == 0:
                continue

            grade_counts = grades.value_counts()

            fig, ax = plt.subplots(
                figsize=(4,4)
            )

            ax.pie(
                grade_counts.values,
                labels=grade_counts.index,
                autopct="%1.1f%%"
            )

            ax.set_title(subject)

            st.pyplot(fig)

            img = BytesIO()

            fig.savefig(
                img,
                format="png"
            )

            img.seek(0)

            st.download_button(
                f"Download {subject}",
                img,
                file_name=f"{subject}.png",
                mime="image/png",
                key=f"t_{subject}"
            )

st.divider()

st.subheader(
    "Practical Subject Grade Distribution"
)

practical_subjects = [
    col for col in subject_cols
    if col.endswith("-[P]")
]

for i in range(
    0,
    len(practical_subjects),
    4
):

    cols = st.columns(4)

    for j, subject in enumerate(
        practical_subjects[i:i+4]
    ):

        with cols[j]:

            grades = final_df[
                subject
            ].dropna()

            if len(grades) == 0:
                continue

            grade_counts = grades.value_counts()

            fig, ax = plt.subplots(
                figsize=(4,4)
            )

            ax.pie(
                grade_counts.values,
                labels=grade_counts.index,
                autopct="%1.1f%%"
            )

            ax.set_title(subject)

            st.pyplot(fig)

            img = BytesIO()

            fig.savefig(
                img,
                format="png"
            )

            img.seek(0)

            st.download_button(
                f"Download {subject}",
                img,
                file_name=f"{subject}.png",
                mime="image/png",
                key=f"p_{subject}"
            )

    

   
    st.success(
            f"Best Subject: {performance_df.iloc[0]['Subject']}"
        )

    st.error(
            f"Weakest Subject: {performance_df.iloc[-1]['Subject']}"
        )
