import os
import re
import json

from pathlib import Path
from pypdf import PdfReader
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Connect to the database
try:
    engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@0.0.0.0:5432/{DB_NAME}", echo=True)
except Exception as e:
    # Exit on fail
    print("Error connecting to the database")
    exit(1)

# Create db schema if not existing
    # Didn't get to writing the actual db. I generally agree with the db tables presented in the take home assignment

    # Schema Design:
        # Table: companies
            # Columns: id, name
                # int id: Primary Key
                # varchar name: Company Name
        # Table: reports
            # Columns: id, company_id, date, filename
                # int id: Primary Key
                # int company_id: Foreign Key to companies
                # datetime date: Date of report (extracted from pdf)
                # varchar filename: Filename of the pdf
        # Table: deficiencies
            # Columns: id, company_id, report_id, issuer, description, audit_area, pcaob_standards
                # int id: Primary Key
                # int company_id: Foreign Key to companies (possibly unnecessary as reports links to companies)
                # int report_id: Foreign Key to reports
                # char issuer: Issuer (A,B,C,D,...)
                # varchar description: Description of deficiency
                # varchar audit_area: Audit Area of deficiency (possibly refactor to audit_area_id and add audit_area table)
                # varchar pcaob_standards: PCAOB Standards of deficiency (possibly refactor to pcaob_standards_id and add pcaob_standards table)


# Import pdfs
paths = list(Path("pdfs/").glob("*.pdf"))

for path in paths:
    # This is rather inefficient in the large scale with multiple regex searches
    pdf = path.open("rb")
    reader = PdfReader(pdf)

    # Extract text from pdfs
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if i == 0:
            # Things guaranteed to be found on first page // Company and Date
            pattern = r"\d{4} Inspection\s*\n(.+)\s*\(Headquartered"
            match = re.search(pattern, text, re.DOTALL)
            company = match.group(1)
            company = company.replace("\n", ' ')

            # extract date with regex
            # I don't like hardcoding the months but it's a start
            date_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2},\s\d{4}"
            date_match = re.search(date_pattern, text)
            date = date_match.group(0)
            # depending on how SQLalchemy handles dates might need to convert to datetime object

        # Problematic section because if "contents" is present in the executive summary or any place before the table of contents
        # we will end up searching the wrong page.All caps limits potential collisions though
        pattern = r"TABLE OF CONTENTS|CONTENTS"
        tc_match = re.search(pattern, text)
        if tc_match:
            page_nums = []
            # extract beginning of audits section and beginning of next section after audits (i.e. the end of audits)
            pattern = r"UNSUPPORTED OPINIONS\s*\.*\s*(\d+)"
            match = re.search(pattern, text, re.IGNORECASE)
            page_nums.append(int(match.group(1)))

            pattern = r"STANDARDS OR RULES\s\.*\s*(\d+)"
            match = re.search(pattern, text, re.IGNORECASE)
            page_nums.append(int(match.group(1)))

    # skip to relevant section to save compute
    text = ""
    for i in range(page_nums[0], page_nums[1]):
        page = reader.pages[i]
        text += page.extract_text()

        # below outputs the results of the first pdf to a text file just as an example of the text we're extracting
        Path('out.txt').write_text(text, encoding='utf-8')
    break

    # Feed to OpenAI for Text Extraction of the issues

    # I didn't get to this, even though it's one of the most crucial parts of the project.

    # As for how I'd tackle it, ideally we'd hand craft a proper json regarding the extraction
    # of a handful of pdfs and use that as an example for a pre-trained model or as part of a prompt
    # for a base model if it works well enough. Then we simply call the api here to perform the same
    # extraction on the text we've extracted from the pdfs.


    # Store results in the db
    # Also not implemented due to time constraints
