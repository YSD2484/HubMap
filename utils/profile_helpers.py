"""
Shared helpers for extracting structured data from founder_data profiles.

Consolidates the job/education extraction logic previously duplicated
across ingest_data.py, build_graph.py, assemble_features.py, etc.
"""


def extract_jobs(profile):
    """Return a list of job objects from a profile, preferring LinkedIn over Crunchbase."""
    if getattr(profile, "linkedin_profile", None) and getattr(profile.linkedin_profile, "jobs", None):
        return list(profile.linkedin_profile.jobs)
    if getattr(profile, "crunchbase", None) and getattr(profile.crunchbase, "jobs", None):
        return list(profile.crunchbase.jobs)
    return []


def extract_educations(profile):
    """Return a list of education objects from a profile, preferring LinkedIn over Crunchbase."""
    if getattr(profile, "linkedin_profile", None) and getattr(profile.linkedin_profile, "educations", None):
        return list(profile.linkedin_profile.educations)
    if getattr(profile, "crunchbase", None) and getattr(profile.crunchbase, "educations", None):
        return list(profile.crunchbase.educations)
    return []


def extract_company_name(job):
    """Extract the company name from a job object, checking all known attribute patterns."""
    name = getattr(job, "company_name", None)
    if name:
        return name
    org = getattr(job, "org", None)
    if org and getattr(org, "name", None):
        return org.name
    name = getattr(job, "organization_name", None)
    if name:
        return name
    return getattr(job, "name", None)


def extract_school_name(edu):
    """Extract the school name from an education object."""
    return getattr(edu, "school", None) or getattr(edu, "school_name", None)


def extract_founded_orgs(profile):
    """Return a list of founded organization objects from a profile's Crunchbase data."""
    return getattr(getattr(profile, "crunchbase", None), "founded_organizations", []) or []
