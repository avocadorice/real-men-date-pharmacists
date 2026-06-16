# 🎯 Goals — Real Men Date Pharmacists

## The Problem

Wife is a pharmacist currently working as a **Walmart floater (part-time)**, commuting from **San Jose (95120)** to locations spread across a huge area — Salinas, Mountain View, Fremont, Los Banos. The commute is brutal and unpredictable since floaters get assigned wherever there's a gap.

**Current rate**: $75–80/hr (part-time, Walmart floater)

## The Goal

**Cast a wide net. Make applying not a dread.**

She's already tried the obvious paths (Costco, Safeway) — the market is saturated and she's not hearing back. The tool should:
1. **Monitor** — catch new postings fast so she's first in line, not 200th
2. **Simplify** — make applications painless instead of a 45-min chore each time
3. **Optimize** — get her resume past ATS filters so a human actually sees it

## Strategy

- **Cast a wide net** — open to anything: retail, managed care, PBM, insurance, clinical, remote
- **Proximity still matters** but not a dealbreaker for the right role (especially remote/hybrid)
- **Speed > perfection** — applying within hours of a posting beats a perfect application 3 days late
- **Per diem foot-in-the-door** — per diem at Costco/Kaiser is the proven path, keep trying

## Preferences (flexible)

1. **Close to home** (San Jose / 95120 area) — ideal but not required
2. **Pay ≥ $75–80/hr** — baseline, but open to lower for remote/managed care roles
3. **Retail pharmacy** — Costco, Safeway, etc. (she knows the work, it pays well)
4. **Managed care / PBM / insurance** — open to it (OptumRx, Express Scripts, Anthem, etc.)
5. **Hospital / health-system** — Kaiser, Stanford, Sutter (if she can get in)
6. **Part-time or full-time** — open to either
7. **Remote / hybrid** — would be a game changer even at lower pay

## What We're Building

### Phase 1: Tailored Resumes (high leverage, do first)
- [x] Costco/retail-optimized resume (ATS keywords, bilingual prominent, volume metrics)
- [x] Kaiser/clinical-optimized resume (MTM, chronic disease, provider collaboration)
- [x] Managed care/PBM-optimized resume (prior auth, insurance, formulary, utilization review)

### Phase 2: Job Monitor (catch postings early)
- [x] SerpAPI (Google Jobs) integration — pharmacist jobs near 95120
- [ ] Alert system — text/email when new posting appears (Future)
- [x] Track Costco, Kaiser, Safeway career pages specifically
- [x] De-duplicate and track what she's already seen/applied to

### Phase 3: Application Accelerator (reduce dread)
- [x] Profile template — all her info in one copy-paste-ready doc (license#, DEA#, NPI#, education, work history, references)
- [ ] ATS keyword matcher — paste a job description, get a tailored resume back (Future)
- [x] Application tracker — what she applied to, when, status

## Data Sources (from research)

### Primary
- **Google Jobs via SerpAPI** — meta-aggregator, structured JSON, free tier (250 queries/mo)

### Supplementary
- **Adzuna API** — free tier, structured data
- **ZipRecruiter** — high volume, salary transparency
- **APhA/HealthShifts** — pharmacy-specific listings

### Dead / Skip
- ~~PharmacyWeek~~ — defunct
- ~~HireRx~~ — defunct/spam
- ~~Rite Aid~~ — closed nationwide
- Indeed / LinkedIn / Glassdoor — too hard to scrape, already captured by Google Jobs

## Tech Stack

Keep it lean:
- Python scripts for job fetching / resume tailoring
- SerpAPI for job data
- SQLite for tracking
- Simple HTML/JS frontend
- Twilio or email for alerts
