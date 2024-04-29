import db
import pandas as pd
import streamlit as st
from sqlalchemy.dialects.postgresql import insert
import datetime

seniority_level_1 = ["Junior", "Intern", "Trainee", "Assistant", "Apprentice", "Entry-level", "Graduate", "Clerk", "Aide", "Technician"]
seniority_level_2 = ["PhD","Associate", "Coordinator", "Specialist", "Analyst", "Assistant Manager", "Junior Developer", "Junior Designer", "Junior Engineer", "Sales Representative"]
seniority_level_3 = ["Senior Associate", "Supervisor", "Team Leader", "Project Coordinator", "Senior Analyst", "Senior Technician", "Senior Developer", "Senior Designer", "Senior Engineer", "Account Manager"]
seniority_level_4 = ["Manager", "Senior Manager", "Project Manager", "Department Manager", "Team Manager", "Senior Developer", "Senior Designer", "Senior Engineer", "Senior Consultant", "Lead", "Chief Specialist"]
seniority_level_5 = ["Director", "Senior Director", "Vice President", "Executive Director", "Chief Officer (CEO, CTO, CFO, COO)", "Chief Executive Officer", "Chief Technology Officer", "Chief Financial Officer", "Chief Operating Officer", "President"]

if "nb_feedbacks" not in st.session_state:
    st.session_state["nb_feedbacks"] = 0

def load_keywords(experience_id,people_uuid):
    # Load keywords
    uuid = str(people_uuid)
    raw_sql = f"""
    SELECT
        experience_id,
        keyword,
        type
    FROM linkedin_people_experience_keywords
    WHERE people_uuid = '{uuid}';
    """
    keywords_df = pd.read_sql(raw_sql, db.connection)
    keywords_df = keywords_df[keywords_df["experience_id"] == experience_id].copy()
    return keywords_df


def load_experience():
    # Load experiences
    raw_sql = """
    SELECT 
        people.uuid, 
        people.full_name, 
        people.linkedin, 
        people.strongest_connection_user, 
        linkedin_people_experience.experience_id,
        linkedin_people_experience.start_date,
        linkedin_people_experience.end_date,
        linkedin_people_experience.duration,
        linkedin_people_experience.seniority_level,
        linkedin_people_experience.how_long_ago,
        linkedin_people_experience.title,
        linkedin_people_experience.description,
        linkedin_people_experience.company,
        linkedin_people_experience.industry,
        linkedin_people_experience.role,
        linkedin_people_experience.nb_employee_range,
        linkedin_people_experience.importance
    FROM people INNER JOIN linkedin_people_experience
    ON people.uuid = linkedin_people_experience.people_uuid
    WHERE linkedin_people_experience.experience_id NOT IN (SELECT experience_id FROM linkedin_people_experience_feedback)
    ORDER BY RANDOM()
    LIMIT 1;
    """

    experiences = pd.read_sql(raw_sql, db.connection)
    experience_record = experiences.to_dict(orient="records")[0]
    keywords_df = load_keywords(experience_record["experience_id"],experience_record["uuid"])
    return experience_record , keywords_df

def insert_data(data: list, table, index_elements):
    """
    Here we will insert/update the given data in the table

    __INPUTS__:
        data : list(dict) , list of records
        table : table name
        fields_to_update : list of fields to update 
    """

    # We will insert the list of records, all in one query
    insert_data = insert(table).values(data)
    # If the record already exists, we will update the fields_to_update
    insert_data = insert_data.on_conflict_do_nothing(index_elements=index_elements)
    db.session.execute(insert_data)
    try:
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        raise e

def main():
    record,keywords_df = load_experience()

    markdown_explanation = f"""
## Instructions
You will be presented with a LinkedIn experience.  
We computed 4 dimensions: :gray[**Seniority Level**], :gray[**Role**], :gray[**How Long Ago**], and :gray[**Duration**].  

**From this 4 dimensions we will compute an importance score so we need you feedback to know:**
  
### :red[How important is this experience in a person's career?] 

1. Not Important  
2. Somewhat Important  
3. Important  
4. Very Important  
  
You can also provide feedback on ths Seniority Level dimensions and the Role dimension.  
The role was computed using OpenAI's GPT-3 model. Possible roles are advisor, partner, investor, employee, cxo, founder.
The Seniority Level was computed using a seniority level mapping (1 being the junior and 5 being the most senior). 
    """
    know_more_senority_mapping = f"""
## Seniority Level Mapping
  
Level 1: {seniority_level_1}  
  
Level 2: {seniority_level_2}  
  
Level 3: {seniority_level_3}  
  
Level 4: {seniority_level_4}  
  
Level 5: {seniority_level_5} 
    """


    markdown_presentation = f"## {record['full_name']} [{record['strongest_connection_user']}] \n### {record['title']} at {record['company']}\n"
    # Add LinkedIn link as a clickable URL
    markdown_presentation += f"[See LinkedIn Profile]({record['linkedin']})  \n"
    if record['end_date']:
        markdown_presentation += f"**Duration**: {record['start_date']} to {record['end_date']} ({round(record['duration'],1)} years)  \n"
    else:
        markdown_presentation += f"**Duration**: {record['start_date']} to Present ({round(record['duration'],1)} years)  \n"
    if record['description']:
        markdown_presentation += f"**Description**: {record['description']}  \n"
    if record['industry']:
        markdown_presentation += f"**Industry**: {record['industry']}  \n"
    if record['nb_employee_range']:
        markdown_presentation += f"**Employee Count Range**: {record['nb_employee_range']}  \n"

    markdown_presentation+= "  \n  \n"
    markdown_presentation += f"**Seniority Level**: {record['seniority_level']}  \n"
    markdown_presentation += f"**Role**: {record['role']}  \n"
    markdown_presentation += f"**How Long Ago**: {record['how_long_ago']} years  \n"
    markdown_presentation += f"**Duration**: {round(record['duration'],1)} years  \n"
    markdown_presentation += f"**Importance Score**: {round(record['importance']*4)}  \n"

    keywords_presentation = ""
    if not keywords_df.empty:
        for keywords_type in keywords_df["type"].unique():
            if not (keywords_type in ["generated_industry","generated_skill"]):
                keywords_presentation += f"**{keywords_type}**:  \n"
                for keyw in keywords_df[keywords_df["type"] == keywords_type]["keyword"].values:
                    keywords_presentation += f"- {keyw}\n"
                keywords_presentation += "  \n"
    



    

    st.title("Experience Feedback")
    st.markdown(markdown_explanation)
    with st.expander("Know more about seniority level mapping"):
        st.markdown(know_more_senority_mapping)

    with st.form("Feedback Form"):
        st.markdown(markdown_presentation)
        with st.expander("Keywords"):
            st.markdown(keywords_presentation)
        st.write("\n\n## Feedback")
        current_importance = round(record['importance']*4)
        importance_score = st.select_slider("Importance Score", options=[1, 2, 3, 4],value=current_importance)
        senority_level_options = [1, 2, 3, 4, 5]
        senority_level_options.remove(record['seniority_level'])
        senority_level_options = [record['seniority_level']] + senority_level_options
        seniority_level = st.selectbox("Seniority Level", options=senority_level_options)
        role_options = ["advisor", "investor", "employee", "partner", "cxo", "founder"]
        role_options.remove(record['role'])
        role_options = [record['role']] + role_options
        role = st.selectbox("Role", options=role_options)



        # Every form must have a submit button.
        submitted = st.form_submit_button("Submit")
        if submitted:
            timestamp = datetime.datetime.now()
            new_record = {
                "feedback_id": f"{record['experience_id']}_{timestamp}",
                "experience_id": record['experience_id'],
                "duration": record['duration'],
                "seniority_level": seniority_level,
                "how_long_ago": record['how_long_ago'],
                "role": role,
                "importance": importance_score,
            }
            insert_data([new_record], db.schema.classes.linkedin_people_experience_feedback, ["feedback_id"])
            st.session_state["nb_feedbacks"] += 1
        
        new_experience = st.form_submit_button("New Experience",help="Click here to get a new experience without submitting feedback on the current one.")
        if new_experience:
            st.rerun()

    nb_feedbacks = st.session_state["nb_feedbacks"]
    if nb_feedbacks % 10 == 0 and nb_feedbacks > 0:
        st.write(f"You have submitted {nb_feedbacks} feedbacks! Thank you very much! Let's keep going!")
    else:
        st.write(f"Number of feedbacks submitted: {nb_feedbacks}")


if __name__ == "__main__":
    main()