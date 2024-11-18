import pytest

from src.ai_hawk.job_manager import AIHawkJobManager
from src.regex_utils import generate_regex_patterns_for_blacklisting

apply_component = AIHawkJobManager(None)  # For this test we don't need the web driver

# Test title, company, and location blacklist definition
title_blacklist = [
    "Data Engineer", "Software Engineer", "AWS", "java", "Back End", "DevOps", "scientist", "WaveAccess", "SAP",
    "Full Stack", "FullStack", "Android", "Backend", "MS Dynamics", "Data Centre", "iOS", "React", "Calypso",
    "SharePoint", "C++", "C#", ".NET", "Unity", "Linux", "Frontend", "Node.js", "Mobile", "PHP", "ML", "GIS"
]
company_blacklist = ["ABC Corp", "XYZ Inc"]
location_blacklist = ["Brazil"]
seen_jobs = set()

# Creating regex patterns
apply_component.title_blacklist_patterns = generate_regex_patterns_for_blacklisting(title_blacklist)
apply_component.company_blacklist_patterns = generate_regex_patterns_for_blacklisting(company_blacklist)
apply_component.location_blacklist_patterns = generate_regex_patterns_for_blacklisting(location_blacklist)

apply_component.seen_jobs = seen_jobs
apply_component.seen_jobs.add("link14")  # Added link for 'seen link' test

test_cases = [
    # Blacklist matches for "Data Engineer" in various forms
    ("Data Engineer", "Tech Corp", "link1", "USA", True),  # Exact match (blacklist)
    ("Data Engineer (Gen AI)", "Tech Corp", "link2", "USA", True),  # Partial match with parentheses (blacklist)
    ("Senior Data Engineer", "Tech Corp", "link3", "USA", True),  # Partial match with prefix (blacklist)
    ("Engineer, Data", "Tech Corp", "link4", "USA", True),  # Words reordered (blacklist)
    ("Data-Engineer", "Tech Corp", "link5", "USA", True),  # Hyphenated (blacklist)
    ("Data & Engineer", "Tech Corp", "link6", "USA", True),  # Ampersand separator (blacklist)

    # Blacklist matches for "Brazil" in location in various forms
    ("Project Manager", "Tech Corp", "link7", "Brazil", True),  # Exact match (blacklist)
    ("Project Manager", "Tech Corp", "link8", "Rio de Janeiro, Brazil", True),  # Location with city and country (blacklist)
    ("Project Manager", "Tech Corp", "link9", "São Paulo - Brazil", True),  # Location with hyphen separator (blacklist)
    ("Project Manager", "Tech Corp", "link10", "Brazil, South America", True),  # Location with continent (blacklist)

    # Blacklist matches for "ABC Corp" in various forms
    ("Marketing Specialist", "ABC Corp", "link11", "USA", True),  # Exact match (blacklist)
    ("Marketing Specialist", "ABC Corporation", "link12", "USA", False),  # Variants on corporation, part of a different word
    ("Marketing Specialist", "ABC CORP", "link13", "USA", True),  # Uppercase variant (blacklist)

    # Seen job link test
    ("Marketing Specialist", "DEF Corp", "link14", "USA", True),  # Link has been seen (blacklist)
    
    # Cases that should NOT be blacklisted (expected to pass)
    ("Software Developer", "Tech Corp", "link15", "USA", False),  # Title not blacklisted
    ("Product Engineer", "XYZ Ltd", "link16", "Canada", False),  # Title and location not blacklisted
    ("Data Science Specialist", "DEF Corp", "link17", "USA", False),  # Title similar but not matching blacklist
    ("Project Manager", "GHI Inc", "link18", "Argentina", False),  # Location close to blacklist but distinct
    ("Operations Manager", "ABC Technology", "link19", "USA", False),  # Company name similar but not matching

    # Complex blacklist matches
    ("AWS Developer", "Tech Corp", "link20", "USA", True),  # Exact AWS
    ("Java Engineer", "Tech Corp", "link21", "USA", True),  # Exact Java
    ("Backend Developer", "Tech Corp", "link22", "USA", True),  # Backend match
    ("Full Stack Engineer", "Tech Corp", "link23", "USA", True),  # Full Stack
    ("iOS Developer", "Tech Corp", "link24", "USA", True),  # iOS exact
    ("Linux Admin", "Tech Corp", "link25", "USA", True),  # Linux exact match
    ("C++ Engineer", "Tech Corp", "link26", "USA", True),  # Exact C++
    ("C# Developer", "Tech Corp", "link27", "USA", True),  # Exact C#
    (".NET Developer", "Tech Corp", "link28", "USA", True),  # Exact .NET
    ("Calypso Engineer", "Tech Corp", "link29", "USA", True),  # Calypso exact
    ("Mobile App Developer", "Tech Corp", "link30", "USA", True),  # Mobile exact

    # Cases that should NOT be blacklisted (complex cases)
    ("Python Developer", "Tech Corp", "link31", "USA", False),  # Not in blacklist
    ("Web Developer", "Tech Corp", "link32", "USA", False),  # Not in blacklist
    ("ReactJS Developer", "Tech Corp", "link33", "USA", False),  # React is substring but not exact
    ("Node Developer", "Tech Corp", "link34", "USA", False),  # Node without .js is not blacklisted
    ("GIS Consultant", "Tech Corp", "link35", "USA", True),  # GIS exact match
]

@pytest.mark.parametrize("job_title, company, link, job_location, expected_output", test_cases)
def test_is_blacklisted(job_title, company, link, job_location, expected_output):
    actual_output = apply_component.is_blacklisted(job_title, company, link, job_location)

    assert actual_output == expected_output, f"Failed for case: {job_title} at {company} in {job_location} (link: {link})"
