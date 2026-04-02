# HubMap Founder Data Kit

This repository provides a **structured, type-safe, and easy-to-use interface** for HubMap Partners' founder profile data. Using Pydantic models, this toolkit transforms raw CSV/BigQuery exports—which often contain messy stringified JSON and mixed data types—into clean Python objects that you can interact with using standard dot notation (`profile.patents`, `profile.x.posts`, etc.).

Whether you are researching founder personas, predicting startup success, or analyzing social graph data, this kit ensures you spend less time cleaning data and more time extracting insights.

## What this Kit Offers

- **Structured Data**: No parsing raw strings or dealing with `NaN` values manually. The `FounderProfile` model automatically validates and converts fields into proper Python types (dates, lists, nested objects).
- **Type Safety**: Know exactly what data is available. IDEs will provide autocomplete for all fields (e.g., `profile.github.repositories[0].primary_language` or `profile.authorship.papers`).
- **Flexible Extraction**: Easily filter and extract only the specific slices of data relevant to your research (e.g., just X/Twitter posts, or only Patent and GitHub data).
- **Robust Parsing**: Handles common data issues like stringified Python lists, malformed JSON, and messy date formats out of the box.

## Data Model Structure

The `FounderProfile` object is a deep, nested structure. Here is a high-level overview of the key fields:

```text
FounderProfile
├── name (str)
├── created_at (datetime)
├── linkedin_profile (LinkedInProfile)
│   ├── name (str)
│   ├── first_name (str)
│   ├── last_name (str)
│   ├── headline (str)
│   ├── summary (str)
│   ├── location (str)
│   ├── num_of_connections (int)
│   ├── skills (list[str])
│   ├── languages (list[str])
│   ├── jobs (list[Job])
│   │   ├── title (str)
│   │   ├── org (Organization)
│   │   ├── started_on (date)
│   │   └── ended_on (date)
│   ├── educations (list[Education])
│   │   ├── school (str)
│   │   ├── degree (str)
│   │   ├── fields (list[str])
│   │   ├── started_on (date)
│   │   └── completed_on (date)
│   ├── certifications (list[Certification])
│   │   ├── name (str)
│   │   └── issued_on (date)
│   ├── posts (list[LinkedInPost])
│   │   ├── title (str)
│   │   ├── content (str)
│   │   ├── url (str)
│   │   ├── posted_at (datetime)
│   │   ├── shares (int)
│   │   ├── total_comments (int)
│   │   └── reactions (list[Reaction])
│   ├── comments (list[LinkedInComment])
│   │   ├── comment (str)
│   │   ├── commented_at (datetime)
│   │   └── post_url (str)
│   └── reactions (list[LinkedInReaction])
│       ├── reacted_at (datetime)
│       ├── post_title (str)
│       └── post_url (str)
├── x (XProfile)
│   ├── name (str)
│   ├── description (str)
│   ├── followers_count (int)
│   ├── following_count (int)
│   ├── is_verified (bool)
│   ├── location (str)
│   ├── profile_image (str)
│   └── posts (list[XPost])
│       ├── tweet_text (str)
│       ├── tweet_date (datetime)
│       ├── likes (int)
│       ├── retweets (int)
│       ├── views (int)
│       ├── comments (int)
│       ├── quotes (int)
│       ├── isRetweet (bool)
│       ├── media_type (str)
│       └── replying_to (list[str])
├── github (GitHubUser)
│   ├── login (str)
│   ├── bio (str)
│   ├── company (str)
│   ├── followers (int)
│   ├── following (int)
│   ├── location (str)
│   ├── blog (str)
│   ├── email (str)
│   ├── repositories (list[GitHubRepo])
│   │   ├── name_with_owner (str)
│   │   ├── description (str)
│   │   ├── primary_language (str)
│   │   ├── stargazer_count (int)
│   │   ├── fork_count (int)
│   │   ├── created_at (datetime)
│   │   ├── pushed_at (datetime)
│   │   ├── is_fork (bool)
│   │   └── license_info (str)
│   └── contributions (GitHubContributions)
│       ├── commit_contributions (int)
│       ├── issue_contributions (int)
│       ├── pr_contributions (int)
│       └── pr_review_contributions (int)
├── crunchbase (CrunchbaseProfile)
│   ├── name (str)
│   ├── location (str)
│   ├── jobs (list[Job])
│   ├── educations (list[Education])
│   └── founded_organizations (list[Organization])
├── patents (list[Patent])
│   ├── title (str)
│   ├── abstract (str)
│   ├── date_published (date)
│   ├── inventors (list[str])
│   ├── patent_status (str)
│   └── priority_claims (list[str])
├── authorship (PubAuthor)
│   ├── topics (list[str])
│   ├── h_index (int)
│   ├── affiliations (list[str])
│   ├── orcid (str)
│   └── papers (list[PubPaper])
│       ├── title (str)
│       ├── abstract (str)
│       ├── citation_count (int)
│       ├── journal (str)
│       ├── pub_date (date)
│       ├── doi (str)
│       ├── url (str)
│       └── authors_names (list[str])
├── web (list[WebData])
│   ├── source_type (str)
│   ├── title_or_headline (str)
│   ├── excerpt (str)
│   ├── source_url (str)
│   └── published_date (date)
└── founded_companies (list[Organization]) [Computed]
    ├── name (str)
    ├── founded_on (date)
    ├── funding_total_usd (int)
    ├── description (str)
    ├── location (str)
    ├── company_type (str)
    ├── website_url (str)
    ├── category_groups (list[str])
    ├── headcount (HeadcountRange)
    │   ├── min_ (int)
    │   └── max_ (int)
    ├── funding_rounds (list[FundingRound])
    │   ├── name (str)
    │   ├── amount_raised_usd (int)
    │   ├── announced_on (date)
    │   ├── investment_type (str)
    │   ├── post_money_valuation_usd (int)
    │   └── investors (list[OrgInvestor])
    │       ├── name (str)
    │       └── is_lead_investor (bool)
    ├── funds (list[Fund])
    │   ├── name (str)
    │   ├── amount_raised_usd (int)
    │   └── announced_on (date)
    ├── ipos (list[IPO])
    │   ├── went_public_on (date)
    │   ├── amount_raised_usd (int)
    │   └── valuation_usd (int)
    └── acquisitions (list[Acquisition])
        ├── price_usd (int)
        ├── acquired_on (date)
        ├── acquired_by (str)
        └── acquiree (str)
```

## Installation

**Note:** This kit requires **Python 3.13** or above.

### Option A: Install from a private GitHub repo (recommended)

You must have **GitHub read access** to this private repository.

- **Using `uv` + SSH** (recommended):

```bash
uv pip install "founder-data @ git+ssh://git@github.com/HubMap-Research/founder-data.git"
```

- **Using `pip` + SSH**:

```bash
pip install "founder-data @ git+ssh://git@github.com/HubMap-Research/founder-data.git"
```

- **Using `uv`/`pip` + GitHub token (PAT)** (useful for CI):

```bash
uv pip install "founder-data @ git+https://<GITHUB_TOKEN>@github.com/HubMap-Research/founder-data.git"
```

### Option B: Install locally (contributors)

```bash
uv sync
```

Or:

```bash
pip install -e .
```

## Usage

### 1. Loading the Data

The kit provides a helper function `load_founder_profiles` that **prefers a local cache**, and if it’s missing (or you request a refresh), it will **download from BigQuery** and write the cache locally.

#### Required access (BigQuery)

To download the data, you need a **GCP service account JSON key** that has read access to the BigQuery table.

- **You need the JSON key file** (e.g., `vela-founder-data-reader.json`)
- **IAM roles** (typical minimum):
  - `roles/bigquery.dataViewer` on the dataset (or table)
  - `roles/bigquery.jobUser` on the project (so queries can run)

Optional (recommended for speed):

- Install the BigQuery Storage client (faster downloads, especially for large tables):

```bash
uv pip install "founder-data[storage] @ git+ssh://git@github.com/HubMap-Research/founder-data.git"
```

To authenticate, provide a **BigQuery service account JSON key** via:

- **Env var (recommended)**: `FOUNDER_DATA_BQ_CREDENTIALS=/path/to/key.json`
- **Or**: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`

By default, the kit reads from HubMap’s canonical table:

- `zihni-255523.Founder_Data.founders`

You can override the table if needed:

- **Env var**: `FOUNDER_DATA_BQ_TABLE=project.dataset.table`
- **Or**: pass `bq_table="project.dataset.table"` to `load_founder_profiles(...)`

Optional:

- **Project override**: `FOUNDER_DATA_BQ_PROJECT=my-gcp-project` (usually not needed if the table is fully-qualified)

#### Getting started

```python
from founder_data import load_founder_profiles

profiles_gen = load_founder_profiles(
    n=1000,  # set None to load all
    credentials_path="/path/to/your/service-account-key.json",
)

# Note: the BigQuery download + local cache write happens when you first *consume*
# the generator (e.g., `next(profiles_gen)` or `list(profiles_gen)`), not at function call time.
founder = next(profiles_gen)
print(founder.name)
```

```python
from founder_data import load_founder_profiles

# Load profiles as a generator
# If a local cache exists, it will be used; otherwise this will download from BigQuery.
# You can also pass bq_table/credentials_path directly instead of env vars.
profiles_gen = load_founder_profiles()

# Iterate over the profiles
for profile in profiles_gen:
    print(f"Processing {profile.name}...")
    # Do your analysis here
```

If you need a list, you can simply cast the generator:

```python
profiles = list(load_founder_profiles())
```

Cache controls:

- **row limit**: `load_founder_profiles(n=100_000)` (writes/reads cache `vela_founder_profiles_n100000.feather`)
- **cache location**: `load_founder_profiles(cache_dir="...")` (default `"."`)
- **cache filename override**: env var `FOUNDER_DATA_CACHE_FILENAME`
- **force refresh**: `load_founder_profiles(refresh_cache=True)`

Notes:

- **Cache format**: local cache is stored as Arrow/Feather (`.feather`) for reliability and speed.
- **Cache selection**: if you request `n=10_000` and you already have a cache like `vela_founder_profiles_n100000.feather`, the loader will reuse it and just take the first 10,000 rows (no re-download).

```

### 2. Preparing Data for ML/Analysis (Target Variable & Data Leakage)

When using this data for predictive modeling (e.g., predicting startup success), you must handle the `founded_companies` field carefully to avoid data leakage.

#### The Target Variable (Y-Value)

The `founded_companies` field is a computed list of companies founded by the person. This typically serves as your source for target variables (e.g., `funding_total_usd`, IPO status, acquisition price).

#### Preventing Data Leakage

To ensure a fair prediction, **all feature data (X/Twitter posts, GitHub repos, Papers, etc.) must be filtered to include only events that occurred BEFORE the founding date of the company you are predicting**.

#### Leakage-safe snapshots with `strip_after(...)`

All major models support creating an "as-of" snapshot via `strip_after(after=...)`, which removes dated events that occur **on or after** the cutoff (i.e., keeps only events strictly before `after`). This is the easiest way to avoid accidental leakage.

- **Entry point**: `FounderProfile.strip_after(after: date, allow_unknowns: bool = False)`
- **Also available on nested models**: `LinkedInProfile`, `CrunchbaseProfile`, `XProfile`, `GitHubUser`, `PubAuthor`
- **What gets filtered** (examples): LinkedIn jobs/posts/reactions, Crunchbase jobs/founded orgs, X posts, GitHub repos, papers, web items, patents.

Example (build a per-company snapshot before feature extraction):

```python
from datetime import date

# Pick a cutoff date (typically the company founding date you're predicting)
cutoff = date(2020, 1, 1)

profile_asof = profile.strip_after(cutoff, allow_unknowns=True)

# Now build features from profile_asof, not profile
num_posts_pre = len(profile_asof.x.posts) if profile_asof.x and profile_asof.x.posts else 0
num_repos_pre = len(profile_asof.github.repositories) if profile_asof.github and profile_asof.github.repositories else 0
```

#### Handling Repeat Founders

A single `FounderProfile` can yield **multiple training examples** if the founder has started multiple companies.

- **Company A (founded 2015)**: Features = all data before 2015. Target = Company A success.
- **Company B (founded 2020)**: Features = all data before 2020 (including Company A's outcome). Target = Company B success.

#### Example: Creating Training Data

#### Success Criteria (Default at HubMap)

This kit includes a convenience label on the company object: `Organization.vela_success_label`.

- **Acquisition success**: first acquisition price is **>= $500M** AND **>= total funding** (so we don’t count outcomes where the company raised far more than the exit and investors likely lost money).
- **IPO success**: first IPO **amount_raised_usd >= $100M** (filters out many low-quality/small IPOs).

This is **HubMap’s default heuristic**, but it is not the only valid definition of “success”. A particular research project may prefer a different label (e.g., funding thresholds, valuation, follow-on rounds, profitability, or domain-specific outcomes). In that case, treat `vela_success_label` as a baseline and compute your own target from the `Organization` fields (`funding_total_usd`, `funding_rounds`, `ipos`, `acquisitions`, etc.).

```python
training_examples = []

for profile in profiles:
    # Iterate through each company the founder started
    for company in profile.founded_companies:
        founding_date = company.founded_on
  
        if not founding_date:
            continue
  
        # Create an "as-of" snapshot so all dated signals are leakage-safe by construction
        profile_asof = profile.strip_after(founding_date, allow_unknowns=True)

        # 1. Define the Target (Y)
        # Example: use HubMap's default success heuristic for this *company*
        # (see `Organization.vela_success_label`).
        target_success = 1 if company.vela_success_label else 0
  
        # 2. Extract Features (X) - STRICTLY FILTERED by founding_date
  
        # Example features from the as-of snapshot
        valid_posts = profile_asof.x.posts if profile_asof.x and profile_asof.x.posts else []
  
        valid_repos = (
            profile_asof.github.repositories
            if profile_asof.github and profile_asof.github.repositories
            else []
        )
  
        valid_papers = (
            profile_asof.authorship.papers
            if profile_asof.authorship and profile_asof.authorship.papers
            else []
        )
  
        # 3. Construct the Training Point
        example = {
            "founder_name": profile.name,
            "company_name": company.name,
            "founding_date": founding_date,
            "feature_post_count": len(valid_posts),
            "feature_repo_count": len(valid_repos),
            "feature_paper_count": len(valid_papers),
            "target_success": target_success
        }
        training_examples.append(example)

df_train = pd.DataFrame(training_examples)
```

### 3. Extracting Specific Insights

Once loaded, you can easily slice the data for your specific research needs. While we recommend using as much data as possible for holistic analysis, here are examples of targeted extraction. These are just for demo, do not limit yourself to these.

#### Example A: Analyzing Social Media Presence (X/Twitter)

Extract post content and engagement metrics for sentiment analysis or topic modeling.

```python
from datetime import date

x_data = []
for profile in profiles:
    # Optional: avoid leakage by snapshotting as-of a chosen cutoff
    profile_asof = profile.strip_after(date(2020, 1, 1), allow_unknowns=True)

    if profile_asof.x and profile_asof.x.posts:
        for post in profile_asof.x.posts:
            x_data.append({
                "founder_name": profile.name,
                "post_text": post.tweet_text,
                "likes": post.likes,
                "retweets": post.retweetc,
                "posted_at": post.tweet_date
            })

# Convert to DataFrame for analysis
df_x = pd.DataFrame(x_data)
```

#### Example B: Technical Background (GitHub & Patents)

Focus on "hard tech" indicators by combining open source activity with intellectual property.

```python
from datetime import date

tech_profiles = []
for profile in profiles:
    # Optional: avoid leakage by snapshotting as-of a chosen cutoff
    profile_asof = profile.strip_after(date(2020, 1, 1), allow_unknowns=True)

    # Filter for founders with both GitHub activity and Patents
    has_github = profile_asof.github is not None
    has_patents = profile_asof.patents is not None and len(profile_asof.patents) > 0
  
    if has_github or has_patents:
        tech_data = {
            "name": profile.name,
            "github_repos": len(profile_asof.github.repositories) if has_github and profile_asof.github.repositories else 0,
            # Extract primary languages from repositories
            "languages": list({r.primary_language for r in profile_asof.github.repositories if r.primary_language}) if has_github and profile_asof.github.repositories else [],
            "patent_count": len(profile_asof.patents) if has_patents else 0,
            "patent_titles": [p.title for p in profile_asof.patents] if has_patents else []
        }
        tech_profiles.append(tech_data)
```

#### Example C: Academic & Research Impact

Analyze the correlation between academic citations and founder success.

```python
from datetime import date

academic_founders = []
for profile in profiles:
    # Optional: avoid leakage by snapshotting as-of a chosen cutoff
    profile_asof = profile.strip_after(date(2020, 1, 1), allow_unknowns=True)

    if profile_asof.authorship and profile_asof.authorship.papers:
        # Calculate total citations
        total_citations = sum(p.citation_count for p in profile_asof.authorship.papers)
  
        academic_founders.append({
            "name": profile.name,
            "h_index": profile_asof.authorship.h_index,
            "paper_count": len(profile_asof.authorship.papers),
            "total_citations": total_citations,
            "top_topics": profile_asof.authorship.topics
        })
```

## Recommendation

While you can extract specific slices, **we recommend utilizing as many fields as applicable**. Founder success is rarely defined by a single signal; it is the intersection of their network (LinkedIn), technical depth (GitHub/Patents), thought leadership (X/Twitter/Blogs), and academic background (Papers) that paints the complete picture.

The `FounderProfile` object creates a unified view of all these diverse data sources, making it the ideal starting point for multi-modal analysis.

## Project Structure

- `founder_data/`: The main Python package.
  - `schemas/`: Contains the definition for all data models.
    - `profile.py`: The root `FounderProfile` model.
    - `linkedin.py`, `github.py`, `patents.py`, `x.py`, `papers.py`: Source-specific schemas.
    - `common.py`, `web.py`: Shared and web-related schemas.
  - `utils.py`: Utilities for cleaning and normalizing text/dates.
- `lab.ipynb`: Jupyter notebook for exploration and testing.
