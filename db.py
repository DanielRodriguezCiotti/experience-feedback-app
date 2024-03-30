import os
import json
import numpy as np

import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession



# Get database URL from environment variables
DATABASE_URL = os.environ.get('DATABASE_URL', None)

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


