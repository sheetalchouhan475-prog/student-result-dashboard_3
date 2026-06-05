import streamlit as st
import pdfplumber
import pandas as pd
import re
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Result Analysis Dashboard", layout="wide")

st.title("📊 Result Analysis Dashboard")

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

        # Student Details
        roll_match = re.search(r'Roll No\.\s*([A-Z0-9]+)', text)

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

        roll = roll_match.group(1) if roll_match else "N/A"
        course = course_match.group(1).strip() if course_match else "N/A"
        branch = branch_match.group(1).strip() if branch_match else "N/A"
        semester = semester_match.group(1) if semester_match else "N/A"

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
                r'([A-Z]{2,4}\d{2,4})\s*-\s*\[(T|P)\].*?\b(A\+|A|B\+|B|C\+|C|D|F)\b',
                line
            )

            if match:

                subject_code = match.group(1)
                paper_type = match.group(2)
                grade = match.group(3)

                subject_name = f"{subject_code}-[{paper_type}]"

                row[subject_name] = grade

                if paper_type == "T":
                    theory_count += 1
                else:
                    practical_count += 1

        row["No of Theory Papers"] = theory_count
        row["No of Practical Papers"] = practical_count

        student_rows.append(row)

    # Final DataFrame
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

    # Dashboard Summary
    total_students = len(final_df)

    course = final_df["Course"].iloc[0]
    branch = final_df["Branch"].iloc[0]
    semester = final_df["Semester"].iloc[0]

    theory_subjects = [
        s for s in subject_cols if "[T]" in s
    ]

    practical_subjects = [
        s for s in subject_cols if "[P]" in s
    ]

    total_theory = len(theory_subjects)
    total_practical = len(practical_subjects)

    st.divider()

    col1, col2 = st.columns([1, 2])

    with col1:

        st.subheader("Course Information")

        st.write(f"**Course:** {course}")
        st.write(f"**Branch:** {branch}")
        st.write(f"**Semester:** {semester}")

        st.metric("No. of Students", total_students)
        st.metric("Theory Papers", total_theory)
        st.metric("Practical Papers", total_practical)

    with col2:

        st.subheader("Overall Theory Papers Grade Distribution")

        all_theory_grades = []

        for sub in theory_subjects:
            all_theory_grades.extend(
                final_df[sub].dropna().tolist()
            )

        if all_theory_grades:

            grade_counts = pd.Series(
                all_theory_grades
            ).value_counts()

            fig, ax = plt.subplots(figsize=(6, 6))

            ax.pie(
                grade_counts.values,
                labels=grade_counts.index,
                autopct="%1.1f%%"
            )

            ax.set_title("All Theory Papers")

            st.pyplot(fig)

    st.divider()

    # Individual Theory Subject
    st.subheader("Individual Theory Paper Analysis")

    selected_theory = st.selectbox(
        "Select Theory Subject",
        theory_subjects
    )

    grades = final_df[selected_theory].dropna()

    if len(grades) > 0:

        fig, ax = plt.subplots(figsize=(6, 6))

        grade_counts = grades.value_counts()

        ax.pie(
            grade_counts.values,
            labels=grade_counts.index,
            autopct="%1.1f%%"
        )

        ax.set_title(selected_theory)

        st.pyplot(fig)

    st.divider()

    # Individual Practical Subject
    st.subheader("Individual Practical Paper Analysis")

    selected_practical = st.selectbox(
        "Select Practical Subject",
        practical_subjects
    )

    grades = final_df[selected_practical].dropna()

    if len(grades) > 0:

        fig, ax = plt.subplots(figsize=(6, 6))

        grade_counts = grades.value_counts()

        ax.pie(
            grade_counts.values,
            labels=grade_counts.index,
            autopct="%1.1f%%"
        )

        ax.set_title(selected_practical)

        st.pyplot(fig)

    st.divider()

    st.subheader("Student Result Table")

    st.dataframe(
        final_df,
        use_container_width=True
    )

    # Excel Download
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
        "Download Excel File",
        excel_buffer.getvalue(),
        file_name="RGPV_Final_Result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
