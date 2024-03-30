
import streamlit as st
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base

# Get database URL from environment variables
DATABASE_URL = st.secrets["DATABASE_URL"]

# Ensure the database URL is set
if not DATABASE_URL:
    raise ValueError(
        'Could not find DATABASE_URL in environment variables')

# Connect to the database
connection = create_engine(
    DATABASE_URL, echo=False)


# Reflect the database schema
schema = automap_base()
schema.prepare(autoload_with=connection, engine=connection)
session = Session(connection)


