import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(
    page_title="EduGuide AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------
# Demo data
# ----------------------------
DEMO_STUDENT = {
    "student_id": "STU1001",
    "name": "Aarav Sharma",
    "degree": "MCA (Data Science)",
    "semester": "3rd Semester",
    "cgpa": 8.2,
    "attendance": 86,
    "study_hours": 5.5,
    "previous_score": 78,
    "assignment_score": 84,
    "exam_score": 81,
    "participation": 73,
    "interests": ["Data Science", "AI", "Analytics"],
    "career_goal": "Data Scientist",
    "skills": {
        "Python": 82,
        "SQL": 72,
        "Statistics": 61,
        "Machine Learning": 45,
        "Communication": 75,
        "Problem Solving": 80,
        "Power BI": 52,
        "Excel": 68,
    },
}

CAREERS = {
    "Data Analyst": {
        "category": "Analytics",
        "description": "Turns data into business insights using SQL, Excel, Power BI and statistics.",
        "skills": {
            "SQL": 85,
            "Python": 75,
            "Statistics": 80,
            "Power BI": 80,
            "Excel": 85,
            "Communication": 70,
        },
    },
    "Data Scientist": {
        "category": "AI / Data Science",
        "description": "Builds predictive models and uses statistics, Python and ML to solve problems.",
        "skills": {
            "Python": 90,
            "SQL": 80,
            "Statistics": 85,
            "Machine Learning": 90,
            "Problem Solving": 80,
            "Communication": 70,
        },
    },
    "Machine Learning Engineer": {
        "category": "AI / Engineering",
        "description": "Deploys ML systems and works with data pipelines, models and production services.",
        "skills": {
            "Python": 90,
            "Machine Learning": 92,
            "SQL": 75,
            "Problem Solving": 85,
            "Communication": 65,
            "Statistics": 78,
        },
    },
    "Business Analyst": {
        "category": "Business Intelligence",
        "description": "Connects business goals with data analysis, reporting and stakeholder communication.",
        "skills": {
            "Excel": 88,
            "SQL": 78,
            "Communication": 85,
            "Power BI": 80,
            "Problem Solving": 80,
            "Statistics": 72,
        },
    },
}

# ----------------------------
# Helper functions
# ----------------------------
def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))

def academic_score(s):
    score = (
        s["attendance"] * 0.25
        + s["study_hours"] * 10 * 0.15
        + s["previous_score"] * 0.20
        + s["assignment_score"] * 0.20
        + s["exam_score"] * 0.15
        + s["participation"] * 0.05
    )
    return clamp(score)

def academic_risk(score):
    if score >= 80:
        return "Low"
    if score >= 65:
        return "Medium"
    return "High"

def skill_gap(student_skills, career_skills):
    rows = []
    for skill, req in career_skills.items():
        cur = student_skills.get(skill, 0)
        rows.append({
            "Skill": skill,
            "Current": cur,
            "Required": req,
            "Gap": max(0, req - cur)
        })
    return pd.DataFrame(rows).sort_values("Gap", ascending=False)

def career_match_score(student, career_name):
    req = CAREERS[career_name]["skills"]
    ratios = []
    for skill, required in req.items():
        current = student["skills"].get(skill, 0)
        ratios.append(min(current / required, 1.0))
    skill_match = np.mean(ratios) * 100 if ratios else 0

    interests_text = " ".join(student["interests"]).lower()
    goal_text = student["career_goal"].lower()
    profile_alignment = 0

    if career_name.lower() in goal_text:
        profile_alignment += 15
    if "data" in interests_text and "data" in career_name.lower():
        profile_alignment += 10
    if "ai" in interests_text and ("machine" in career_name.lower() or "science" in career_name.lower()):
        profile_alignment += 10
    if "analytics" in interests_text and ("analyst" in career_name.lower() or "business" in career_name.lower()):
        profile_alignment += 10

    acad = academic_score(student)
    academic_factor = (acad / 100) * 15

    return clamp(skill_match * 0.75 + profile_alignment + academic_factor)

def top_careers(student, top_n=3):
    rows = []
    for career_name in CAREERS:
        score = career_match_score(student, career_name)
        rows.append({
            "Career": career_name,
            "Match %": round(score, 1),
            "Category": CAREERS[career_name]["category"],
            "Description": CAREERS[career_name]["description"],
        })
    return pd.DataFrame(rows).sort_values("Match %", ascending=False).head(top_n)

def roadmap(student, career_name):
    gaps = skill_gap(student["skills"], CAREERS[career_name]["skills"])
    plan = []
    month = 1
    for _, row in gaps[gaps["Gap"] > 0].head(5).iterrows():
        priority = "High" if row["Gap"] >= 25 else "Medium" if row["Gap"] >= 10 else "Low"
        plan.append({
            "Month": f"Month {month}",
            "Focus": row["Skill"],
            "Priority": priority,
            "Gap": int(row["Gap"]),
            "Action": f"Learn {row['Skill']} and build 1 mini project."
        })
        month += 1

    if not plan:
        plan.append({
            "Month": "Month 1",
            "Focus": "Advanced Projects",
            "Priority": "Low",
            "Gap": 0,
            "Action": "Build portfolio projects and prepare resume."
        })

    return pd.DataFrame(plan)

def insight(student):
    score = academic_score(student)
    risk = academic_risk(score)
    if risk == "Low":
        return "Your academic performance is strong. Focus on career-specific skills to improve job readiness."
    if risk == "Medium":
        return "Your performance is steady, but you should improve study consistency and assignment completion."
    return "You need immediate academic support. Improve attendance, study consistency and assignment performance."

def radar_fig(student_skills, career_name):
    career_skills = CAREERS[career_name]["skills"]
    all_skills = list(dict.fromkeys(list(career_skills.keys()) + list(student_skills.keys())))
    current = [student_skills.get(s, 0) for s in all_skills]
    required = [career_skills.get(s, 0) for s in all_skills]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=current, theta=all_skills, fill="toself", name="Current"))
    fig.add_trace(go.Scatterpolar(r=required, theta=all_skills, fill="toself", name="Required"))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        margin=dict(l=20, r=20, t=20, b=20),
        height=430,
    )
    return fig

def report_text(student):
    acad = academic_score(student)
    risk = academic_risk(acad)
    recs = top_careers(student, 3)
    top = recs.iloc[0]["Career"]
    plan = roadmap(student, top)

    out = [
        f"Student Report - {student['name']} ({student['student_id']})",
        f"Degree: {student['degree']}",
        f"Semester: {student['semester']}",
        f"CGPA: {student['cgpa']}",
        f"Academic Score: {acad:.1f}",
        f"Academic Risk: {risk}",
        f"Top Career Match: {top}",
        "",
        "Top Career Recommendations:"
    ]
    for _, row in recs.iterrows():
        out.append(f"- {row['Career']} ({row['Match %']}%)")
    out.append("")
    out.append("Learning Roadmap:")
    for _, row in plan.iterrows():
        out.append(f"- {row['Month']}: {row['Focus']} [{row['Priority']}] - {row['Action']}")
    return "\n".join(out)

# ----------------------------
# Sidebar
# ----------------------------
st.sidebar.title("🎓 EduGuide AI")
st.sidebar.caption("SIH 2026 | PS 26207")
page = st.sidebar.radio(
    "Navigate",
    ["Home", "Dashboard", "Student Profile", "Academic Intelligence", "Skill Gap Analysis", "Career Recommendations", "Learning Roadmap", "Report"]
)

student = DEMO_STUDENT.copy()

st.sidebar.markdown("---")
st.sidebar.subheader("Demo Student")
st.sidebar.write(student["name"])
st.sidebar.write(student["degree"])
st.sidebar.write(f"Goal: {student['career_goal']}")

# ----------------------------
# Pages
# ----------------------------
if page == "Home":
    st.title("EduGuide AI")
    st.subheader("AI-powered Academic Success & Career Intelligence Platform")
    st.write("This prototype analyzes student performance, profile details, skills and career requirements to generate personalized academic insights, career recommendations and a learning roadmap.")

    acad = academic_score(student)
    top = top_careers(student, 1).iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Academic Score", f"{acad:.1f}/100")
    c2.metric("Academic Risk", academic_risk(acad))
    c3.metric("Top Career Match", top["Career"])
    c4.metric("Match %", f"{top['Match %']:.1f}%")

    st.info("Flow: Student Profile → Academic Intelligence → Skill Gap → Career Recommendations → Learning Roadmap")

elif page == "Dashboard":
    st.title("Student Dashboard")
    acad = academic_score(student)
    recs = top_careers(student, 3)
    top_career = recs.iloc[0]["Career"]
    readiness = (acad * 0.35) + (recs.iloc[0]["Match %"] * 0.65)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CGPA", student["cgpa"])
    c2.metric("Attendance", f"{student['attendance']}%")
    c3.metric("Academic Score", f"{acad:.1f}")
    c4.metric("Career Readiness", f"{readiness:.1f}")

    col1, col2 = st.columns(2)

    with col1:
        df = pd.DataFrame({
            "Metric": ["Attendance", "Study Hours", "Previous Score", "Assignment", "Exam", "Participation"],
            "Value": [student["attendance"], student["study_hours"] * 10, student["previous_score"], student["assignment_score"], student["exam_score"], student["participation"]]
        })
        fig = px.bar(df, x="Metric", y="Value", title="Academic Indicators", text="Value")
        fig.update_layout(height=420, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.plotly_chart(radar_fig(student["skills"], top_career), use_container_width=True)

    st.success(f"Recommended Career: {top_career}")
    st.dataframe(recs, use_container_width=True, hide_index=True)

elif page == "Student Profile":
    st.title("Student Profile")
    st.write("Edit the demo profile to test different results.")

    c1, c2 = st.columns(2)
    with c1:
        student["name"] = st.text_input("Name", student["name"])
        student["student_id"] = st.text_input("Student ID", student["student_id"])
        student["degree"] = st.text_input("Degree", student["degree"])
        student["semester"] = st.text_input("Semester", student["semester"])
        student["cgpa"] = st.number_input("CGPA", 0.0, 10.0, float(student["cgpa"]), 0.01)

    with c2:
        student["attendance"] = st.slider("Attendance (%)", 0, 100, int(student["attendance"]))
        student["study_hours"] = st.slider("Study Hours per Day", 0.0, 12.0, float(student["study_hours"]), 0.1)
        student["career_goal"] = st.text_input("Career Goal", student["career_goal"])
        interests = st.text_input("Interests (comma separated)", ", ".join(student["interests"]))
        student["interests"] = [x.strip() for x in interests.split(",") if x.strip()]

    st.markdown("### Skills")
    skill_df = pd.DataFrame(list(student["skills"].items()), columns=["Skill", "Level"])
    edited = st.data_editor(skill_df, use_container_width=True, hide_index=True)
    student["skills"] = dict(zip(edited["Skill"], edited["Level"]))

elif page == "Academic Intelligence":
    st.title("Academic Intelligence")
    acad = academic_score(student)
    risk = academic_risk(acad)

    c1, c2, c3 = st.columns(3)
    c1.metric("Academic Score", f"{acad:.1f}/100")
    c2.metric("Risk Level", risk)
    c3.metric("Study Hours", student["study_hours"])

    if risk == "Low":
        st.success(insight(student))
    elif risk == "Medium":
        st.warning(insight(student))
    else:
        st.error(insight(student))

    df = pd.DataFrame({
        "Indicator": ["Attendance", "Study Hours x10", "Previous Score", "Assignment", "Exam", "Participation"],
        "Score": [student["attendance"], student["study_hours"] * 10, student["previous_score"], student["assignment_score"], student["exam_score"], student["participation"]]
    })
    fig = px.bar(df, x="Indicator", y="Score", title="Academic Breakdown", text="Score")
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

elif page == "Skill Gap Analysis":
    st.title("Skill Gap Analysis")
    top_career = top_careers(student, 1).iloc[0]["Career"]
    st.write(f"Compared against **{top_career}** requirements")

    gaps = skill_gap(student["skills"], CAREERS[top_career]["skills"])
    st.dataframe(gaps, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(radar_fig(student["skills"], top_career), use_container_width=True)
    with c2:
        fig = px.bar(gaps, x="Skill", y="Gap", title="Skill Gaps", text="Gap")
        fig.update_layout(height=430, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

elif page == "Career Recommendations":
    st.title("Career Recommendations")
    recs = top_careers(student, 3)

    for _, row in recs.iterrows():
        with st.container(border=True):
            st.subheader(f"{row['Career']} — {row['Match %']}% Match")
            st.caption(row["Category"])
            st.write(row["Description"])

            req = CAREERS[row["Career"]]["skills"]
            cols = st.columns(min(3, len(req)))
            for i, (skill, required) in enumerate(req.items()):
                with cols[i % len(cols)]:
                    current = student["skills"].get(skill, 0)
                    st.write(f"**{skill}**")
                    st.progress(int(min(100, current)))
                    st.caption(f"Current {current} / Required {required}")

    fig = px.bar(recs, x="Match %", y="Career", orientation="h", text="Match %", title="Top Career Match Scores")
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

elif page == "Learning Roadmap":
    st.title("Personalized Learning Roadmap")
    top_career = top_careers(student, 1).iloc[0]["Career"]
    plan = roadmap(student, top_career)

    st.write(f"Roadmap for **{top_career}**")
    st.dataframe(plan, use_container_width=True, hide_index=True)

    for _, row in plan.iterrows():
        with st.expander(f"{row['Month']} — {row['Focus']} ({row['Priority']})"):
            st.write(row["Action"])
            st.progress(0)

elif page == "Report":
    st.title("Student Report")
    acad = academic_score(student)
    risk = academic_risk(acad)
    recs = top_careers(student, 3)
    top = recs.iloc[0]["Career"]
    plan = roadmap(student, top)

    summary = pd.DataFrame([
        ["Name", student["name"]],
        ["Student ID", student["student_id"]],
        ["Degree", student["degree"]],
        ["Semester", student["semester"]],
        ["CGPA", student["cgpa"]],
        ["Academic Score", f"{acad:.1f}"],
        ["Academic Risk", risk],
        ["Top Career", top],
        ["Top Career Match", f"{recs.iloc[0]['Match %']}%"],
    ], columns=["Field", "Value"])

    st.dataframe(summary, use_container_width=True, hide_index=True)

    txt = report_text(student)
    st.download_button(
        "Download Report as TXT",
        data=txt,
        file_name=f"{student['student_id']}_report.txt",
        mime="text/plain"
    )
    st.text_area("Report Preview", txt, height=380)

st.sidebar.markdown("---")
st.sidebar.caption("Prototype scoring can later be replaced by .pkl ML models from Google Colab.")