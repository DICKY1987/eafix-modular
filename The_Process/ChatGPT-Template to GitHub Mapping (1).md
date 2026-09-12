# Template to GitHub Mapping

**User:**   
**Created:** 4/11/2026 0:09:20  
**Updated:** 4/11/2026 7:55:36  
**Exported:** 4/11/2026 17:49:43  
**Link:** [https://chatgpt.com/g/g-p-69d5a430d8448191aa90599a0c798731-evertything-git/c/69d9d76b-d304-83ea-ad17-0f3ac03866e6](https://chatgpt.com/g/g-p-69d5a430d8448191aa90599a0c798731-evertything-git/c/69d9d76b-d304-83ea-ad17-0f3ac03866e6)  

## Response:
4/11/2026, 12:09:20 AM

Yes — there **is a strong, almost 1:1 mapping** between your New Phase Process Template and a properly structured GitHub Projects setup.

But right now, it’s only **partially defined and inconsistently enforced**. Your workflows already hint at the intended model — they just don’t formalize it as a system.

Below is the clean mapping and where your gaps are.

* * *

1\. CORE MAPPING: TEMPLATE → GITHUB STRUCTURE
=============================================

A. Phases → Milestones (or Project “Phase” field)
-------------------------------------------------

**Template concept:**

*   PH-00, PH-01, PH-02…
*   Canonical lifecycle stages

**GitHub mapping:**

*   **Primary:** GitHub Project field (Phase)
*   **Secondary (optional):** Milestones

You already have automation doing this:

*   Phase → Project field mapping  
    TEMP\_project\_item\_sync
*   Phase files syncing into GitHub  
    TEMP\_deploy-staging

### Correct model

*   **Phases = Project field (NOT just milestones)**
*   Milestones = **delivery checkpoints**, not lifecycle stages

* * *

B. Step Contracts → Issues
--------------------------

**Template concept:**

*   STEP-001, STEP-002
*   Explicit contracts with:
    *   inputs
    *   outputs
    *   invariants
    *   gates

**GitHub mapping:**

*   **Each step = 1 Issue**

This is the most important alignment.

### Why:

*   Issues are atomic
*   Trackable
*   Automatable
*   Closable (state transition = contract satisfied)

Your automation already treats issues as execution units:

*   Project items sync from issues/PRs  
    TEMP\_project\_item\_sync

* * *

C. Gates → CI Checks (Status Checks)
------------------------------------

**Template concept:**

*   validation\_gates
*   binary pass/fail
*   evidence-driven

**GitHub mapping:**

*   GitHub Actions workflows
*   Required status checks

You already implemented this heavily:

Examples:

*   Lint  
    TEMP\_lint
*   Incomplete implementation blocker  
    TEMP\_incomplete-scanner
*   Registry validation  
    TEMP\_registry\_integrity
*   Quality gates pipeline  
    TEMP\_quality-gates

### Correct model

*   **Every template gate = required GitHub check**
*   No check → no merge

* * *

D. Execution → Pull Requests
----------------------------

**Template concept:**

*   Process → Generate → Commit → Validate

**GitHub mapping:**

*   Work happens in branches
*   PR = execution attempt

Your system enforces this:

*   No auto-merge
*   Manual review required  
    TEMP\_branch-handler

### Correct model

*   **PR = implementation of one or more step contracts**
*   Merge = contract accepted

* * *

E. Completion → Issue Closure → Milestone Progress
--------------------------------------------------

You already wired this:

*   Milestone sync based on issue/PR state  
    TEMP\_milestone\_completion

### Correct model

*   Issue closed → step complete
*   All steps closed → milestone complete

* * *

F. Plan Files → Source of Truth (NOT GitHub)
--------------------------------------------

Critical point:

Your system is **NOT GitHub-native**.

*   YAML phase files → SSOT
*   GitHub → projection layer

You already built this:

*   Phase YAML → GitHub sync  
    TEMP\_deploy-staging

### Correct model

*   GitHub = **execution surface**
*   Template JSON/YAML = **control plane**

* * *

2\. WHAT IS CLEARLY DEFINED (GOOD)
==================================

These parts are already strong:

### ✔ Issue ↔ Project sync exists

*   Status
*   Phase mapping
*   Lifecycle tracking  
    TEMP\_project\_item\_sync

### ✔ Milestone progression automation exists

TEMP\_milestone\_completion

### ✔ Phase → GitHub sync exists

TEMP\_deploy-staging

### ✔ Gates → CI enforcement exists

Multiple workflows enforcing constraints

### ✔ PR discipline enforced

*   No auto merge
*   Manual review required  
    TEMP\_branch-handler

* * *

3\. WHAT IS NOT CLEARLY DEFINED (MAJOR GAPS)
============================================

This is where your system breaks down.

* * *

GAP 1 — No Formal Mapping Spec
------------------------------

There is **no explicit contract like:**

```
{
  "mapping": {
    "phase": "github.project.field.phase",
    "step_contract": "github.issue",
    "gate": "github.check",
    "execution": "github.pull_request",
    "completion": "issue.closed"
  }
}
```

Right now:

*   Logic exists in scripts
*   Not defined in template/spec

* * *

GAP 2 — Step → Issue Creation Not Deterministic
-----------------------------------------------

Missing:

*   Automatic issue generation from template
*   Stable ID linkage (STEP\_ID ↔ ISSUE\_ID)

You need:

```
{
  "step_id": "STEP-001",
  "github_issue_number": 123,
  "sync_status": "linked"
}
```

Without this:

*   Traceability breaks
*   Automation becomes heuristic

* * *

GAP 3 — Milestones Are Ambiguous
--------------------------------

Currently unclear:

*   Are milestones phases?
*   Are milestones deliverables?
*   Are they optional?

Correct answer:

*   **Milestones = delivery groupings of steps**
*   NOT phases

* * *

GAP 4 — No Explicit “Work Unit Granularity Rule”
------------------------------------------------

Missing rule:

> One step contract = one issue = one unit of work

Without this:

*   Issues become vague
*   PRs become bloated
*   Gates lose meaning

* * *

GAP 5 — No Enforcement That All Work Comes From Template
--------------------------------------------------------

Right now:

*   Issues can be created manually
*   Work can bypass plan

You need:

*   “No issue without step\_id”
*   “No PR without issue”
*   “No merge without gate”

* * *

GAP 6 — Evidence Not Linked to GitHub Artifacts
-----------------------------------------------

You generate:

*   `.acms_runs`
*   reports
*   logs  
    TEMP\_acms-pipeline

But:

*   Not tied to issues/PRs directly

Missing:

*   Evidence → Issue/PR linkage

* * *

4\. CORRECT TARGET MODEL (CLEAN SYSTEM)
=======================================

This is what your system should converge to:

```
TEMPLATE (SSOT)
    ↓
PHASE → Project Field (Phase)
    ↓
STEP → GitHub Issue
    ↓
EXECUTION → Pull Request
    ↓
GATES → GitHub Checks
    ↓
MERGE → Step Complete
    ↓
ISSUE CLOSED → Milestone Progress
```

* * *

5\. DIRECT ANSWER
=================

### Is there a logical mapping?

Yes — extremely strong and already partially implemented.

### Is there a clear definition?

No — it is **implicit, fragmented, and not enforced at the template/spec level**.

* * *

6\. WHAT YOU SHOULD DO NEXT (NO FLUFF)
======================================

You need to formalize this in **three places**:

### 1\. Template (NEWPHASEPLANPROCESS)

Add:

*   `github_mapping` section
*   step → issue linkage fields
*   milestone grouping definition

* * *

### 2\. Technical Specification

Define:

*   Exact mapping rules
*   Required GitHub structures
*   Enforcement requirements

* * *

### 3\. Instruction Document

Force:

*   AI must create issues from steps
*   AI must not create unlinked work
*   AI must update GitHub state deterministically

* * *

If you want, next step:

I can generate a **machine-ready JSON patch layer (RFC-6902)** that injects this mapping into:

*   Template
*   Spec
*   Instruction document

That’s the missing piece to make this system fully deterministic.

## Response:
4/11/2026, 12:12:55 AM

Here's the comprehensive report you requested:

GitHub Project Management Capabilities and Mapping to a Phase‑Process Template
==============================================================================

Overview of GitHub Projects
---------------------------

_GitHub Projects_ are flexible workspaces that track issues, pull requests and draft tasks across one or more repositories. Projects can be viewed as tables, boards or roadmaps and automatically stay up‑to‑date with underlying GitHub data: changes made in issues or pull requests are reflected in the project and vice‑versa[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects#:~:text=A%20project%20is%20an%20adaptable,your%20team%E2%80%99s%20needs%20and%20processes). Teams can customize these views by filtering, sorting and grouping items, adding custom fields (text, number, date, single‑select or iteration fields) and creating bespoke charts and roadmaps[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects#:~:text=A%20project%20is%20an%20adaptable,your%20team%E2%80%99s%20needs%20and%20processes)[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-text-and-number-fields#:~:text=You%20can%20use%20text%20fields,freeform%20text%20in%20your%20project).

Automation Features
-------------------

### Built‑in Workflows and Auto‑Add/Auto‑Archive

*   **Status updates:** When an issue or pull request is added to a project, built‑in workflows can set its **Status** field automatically (e.g., “Todo” when the item is created and **Done** when an issue is closed or a pull request is merged)[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed).
*   **Auto‑add items:** Projects can be configured to automatically add issues or pull requests from selected repositories based on filters such as item type (issue/PR), labels, assignees or reasons. Each workflow targets a repository and only adds items that are new or have been updated[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically#:~:text=You%20can%20configure%20your%20project%27s,repositories%20that%20match%20a%20filter). Filters support AND/OR/NOT operators, enabling complex conditions for triage[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically#:~:text=You%20can%20configure%20your%20project%27s,repositories%20that%20match%20a%20filter).
*   **Auto‑archive items:** A complementary workflow can automatically archive items that match certain criteria. You can filter by item state (open/closed/merged), reason (completed, reopened, not planned) and date criteria such as “updated within the last 14 days”. Archived items are removed from the active view but remain available for analysis[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/archiving-items-automatically#:~:text=You%20can%20configure%20your%20project%27s,items%20that%20match%20a%20filter).
*   **Action to auto‑add items:** The `actions/add-to-project` GitHub Action adds issues or pull requests to a specified project when they are opened, labeled or reopened. The action accepts filters like `labeled` (comma‑separated labels) and a `label-operator` (AND/OR/NOT) to determine which items to add[github.com](https://github.com/marketplace/actions/add-to-github-projects#:~:text=actions%2Fadd). This action requires a personal access token and is configured in a workflow file; multiple examples show how to add items based on labels or lack thereof[github.com](https://github.com/marketplace/actions/add-to-github-projects#:~:text=Examples).

### API and GraphQL

GitHub’s GraphQL API allows sophisticated automation. You can use `addProjectV2ItemById` to add an issue or pull request to a project and then set field values with `updateProjectV2ItemFieldValue`[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects#:~:text=Updating%20projects). These mutations cannot update the underlying issue’s labels, assignees, milestones or repository, so those attributes must be managed separately[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects#:~:text=Note). Actions can call this API to set statuses, dates and other fields when events occur[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=This%20article%20demonstrates%20how%20to,field).

### GitHub Actions Examples

The Docs provide an example workflow that triggers on a pull request being ready for review. The workflow uses a PAT and the GraphQL API to add the pull request to a project and set the **Status** to “Todo” and a **Date** field to the current date[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=This%20article%20demonstrates%20how%20to,field). Another example uses the `actions/add-to-project` action to add issues with specific labels (e.g., `bug` OR `needs‑triage`) to a project, demonstrating label‑based automation[github.com](https://github.com/marketplace/actions/add-to-github-projects#:~:text=Examples).

Custom Fields, Issue Fields and Iterations
------------------------------------------

*   **Text and Number Fields:** Projects allow custom text and number fields to capture notes or numeric metadata; they support filtering and range queries[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-text-and-number-fields#:~:text=You%20can%20use%20text%20fields,freeform%20text%20in%20your%20project).
*   **Date Fields and Iteration Fields:** Date fields hold start or target dates, while **iteration fields** represent repeating blocks of time (sprints). You can group and filter items by iteration (e.g., `@current`, `@next`) and adjust iteration durations[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-iteration-fields#:~:text=You%20can%20create%20an%20iteration,iteration%2C%20and%20sort%20by%20iteration). Roadmaps use these fields to position items on a timeline[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-roadmap-layout#:~:text=The%20roadmap%20layout%20provides%20a,over%20time%20and%20watch%20progress).
*   **Single‑select Fields:** These provide controlled vocabularies for properties like status, type or priority. They support grouping and filtering in project views.
*   **Issue Fields (public preview):** Organization‑level issue fields provide typed metadata (single‑select, text, number or date) that are defined once and available across all repositories. They replace ad‑hoc labels for structured data like Priority, Effort, Start date and Target date and integrate with projects for filtering, grouping and charting[github.blog](https://github.blog/changelog/2026-03-12-issue-fields-structured-issue-metadata-is-in-public-preview/#:~:text=Issue%20fields%20are%20now%20available,preview%20for%20select%20GitHub%20organizations)[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-issue-fields#:~:text=Issue%20fields%20are%20currently%20in,feedback%2C%20see%20the%20community%20discussion). Issue field values can be edited directly in the project table and are synced back to the underlying issue[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-issue-fields#:~:text=Adding%20an%20issue%20field%20to,a%20project).
*   **Parent‑issue and Sub‑issue Fields:** Enabling the _Parent issue_ field groups items by their parent and allows filtering by parent issue (e.g., `parent-issue:"owner/repo#123"`), while the _Sub‑issue progress_ field shows how many sub‑issues have been completed[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields#:~:text=If%20your%20organization%20uses%20sub,progress%20made%20on%20those%20issues).

Sub‑issues and Hierarchies
--------------------------

GitHub introduced **sub‑issues** to break down larger tasks into smaller issues and create hierarchies. Each issue can have up to 100 sub‑issues and up to eight levels of nesting[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues#:~:text=You%20can%20add%20sub,and%20group%20by%20parent%20issue). Sub‑issues show their relationship to the parent issue, and parent/sub‑issue progress appears in projects, enabling grouping, filtering and progress tracking[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues#:~:text=You%20can%20add%20sub,and%20group%20by%20parent%20issue). You can create sub‑issues inline or convert existing issues into sub‑issues[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues#:~:text=Creating%20a%20sub). Hierarchy view (general availability since March 2026) allows expanding and collapsing these nested issues and includes improvements such as in‑line sub‑issue creation, drag‑and‑drop reorder/reparenting and filter deduplication[github.blog](https://github.blog/changelog/2026-02-19-github-projects-import-items-based-on-a-query-and-hierarchy-view-improvements/#:~:text=Import%20project%20items%20with%20a,search%20query)[github.blog](https://github.blog/changelog/2026-03-19-hierarchy-view-in-github-projects-is-now-generally-available/#:~:text=Hierarchy%20view%20in%20GitHub%20Projects,menu%20by%20toggling%20Show%20hierarchy).

Roadmaps, Charts and High‑Level Visibility
------------------------------------------

*   **Roadmap Layout:** A roadmap provides a timeline view of project items. You drag items to adjust their start and target dates or selected iteration. Roadmaps use date or iteration fields to position items and support vertical markers for important dates such as iterations, milestones and item dates[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-roadmap-layout#:~:text=The%20roadmap%20layout%20provides%20a,over%20time%20and%20watch%20progress). You can slice, sort or group the roadmap by field values (e.g., by assignee or phase) and optionally show the sum of a number field to display aggregate metrics[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-roadmap-layout#:~:text=The%20roadmap%20layout%20provides%20a,over%20time%20and%20watch%20progress).
*   **Insights and Charts:** The _Insights_ feature lets you build custom **current** charts (e.g., items per assignee or iteration) and **historical** charts (e.g., burn‑up charts) based on project data[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/viewing-insights-from-your-project/about-insights-for-projects#:~:text=You%20can%20use%20insights%20for,current%20charts%20and%20historical%20charts). Charts can be filtered by fields like label, assignee or milestone. Historical charts show open, completed and not‑planned items over time, helping you visualize progress and identify bottlenecks[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/viewing-insights-from-your-project/about-insights-for-projects#:~:text=You%20can%20create%20historical%20charts,aggregation%20of%20items%20over%20time).
*   **Milestones:** Milestones group issues and pull requests toward a specific goal. The milestone page shows a description, due date, completion percentage and counts of open/closed issues and pull requests[docs.github.com](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones#:~:text=About%20milestones). Issues can be prioritized within a milestone by dragging them[docs.github.com](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones#:~:text=You%20can%20prioritize%20open%20issues,new%20location%2C%20and%20dropping%20it). In a project, milestones can appear as vertical markers on roadmaps and as filters or grouping criteria.
*   **Labels:** Labels categorize issues and pull requests (e.g., bug, documentation). Custom labels can represent domains, work streams or priority levels[docs.github.com](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels#:~:text=About%20labels). Filters in projects support combining labels with AND/OR/NOT logic.
*   **Parent/Sub‑issue Progress:** Projects can display the percentage of sub‑issues completed for each parent issue, giving a quick view of progress[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields#:~:text=If%20your%20organization%20uses%20sub,progress%20made%20on%20those%20issues).

Actions & Automation for Execution
----------------------------------

Automation allows GitHub Projects to drive implementation execution:

1.  **CI checks as gates:** You can configure GitHub Actions workflows and required status checks to act as gates. For example, workflows might validate code quality, run tests or check compliance before a pull request can be merged. Failing gates prevent merging until issues are addressed. A typical phase‑process could map each gate to a status check and ensure that merges are blocked until all gates pass.
2.  **Auto‑creation and triage:** Using the `actions/add-to-project` action, a workflow can automatically add newly opened or labeled issues/PRs to the appropriate project and assign a default **Status**. This ensures that all work items from a repository enter the project board. Filters allow triaging by labels, enabling different projects for different issue types (e.g., bug vs. feature)[github.com](https://github.com/marketplace/actions/add-to-github-projects#:~:text=Examples).
3.  **State transitions and field updates:** Workflows can update field values (phase, iteration, priority) using the GraphQL API after certain events (e.g., PR ready for review, tests passing). Combined with built‑in workflows that set the Status field on open/close[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed), this creates autonomous progress tracking.

Mapping GitHub Capabilities to a Phase‑Process Template
-------------------------------------------------------

A **phase‑process template** likely defines phases (e.g., design, implementation, test), step contracts (individual tasks), gates (validations), execution (actual coding/merging) and progress tracking. GitHub Projects can map these concepts as follows:

| Template Concept | GitHub Feature | Rationale & How to Use |
| --- | --- | --- |
| **Phases (PH‑00, PH‑01, …)** | **Custom single‑select or date fields and milestones** | Create a single‑select **Phase** field listing each phase of your process; assign each issue to a phase. Alternatively, use **milestones** as high‑level phase goals—each milestone groups issues and shows progress (open vs. closed counts)[docs.github.com](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones#:~:text=About%20milestones). In roadmaps, phases/milestones can appear as vertical markers to show timeframes[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-roadmap-layout#:~:text=The%20roadmap%20layout%20provides%20a,over%20time%20and%20watch%20progress). |
| **Step contracts** | **Issues and sub‑issues** | Each step contract becomes an **issue**. Use **sub‑issues** to break complex steps into smaller tasks or to represent nested contracts. Sub‑issues show their relationship to the parent and can nest up to eight levels[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues#:~:text=You%20can%20add%20sub,and%20group%20by%20parent%20issue). Progress of sub‑issues can be viewed via the _Sub‑issue progress_ field[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields#:~:text=If%20your%20organization%20uses%20sub,progress%20made%20on%20those%20issues). |
| **Gates (validation checkpoints)** | **GitHub Actions workflows & required status checks** | Implement gates as CI workflows (tests, lint, security checks, etc.) that produce status checks. Configure **branch protection rules** so a pull request cannot be merged until required checks pass. Additional automation can update a field (e.g., “Gate status”) in the project when a check fails or passes. |
| **Execution of steps** | **Pull requests linked to issues** | Work happens in branches; each pull request corresponds to executing a step contract. Link the pull request to the issue. Use built‑in workflows to set Status to “In Progress” when a PR is opened and “Done” when it is merged[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed). |
| **Completion & Progress tracking** | **Issue closure, milestones, charts** | Closing an issue marks the step as complete; when all issues in a phase milestone are closed, the milestone shows 100% complete[docs.github.com](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones#:~:text=About%20milestones). Use charts (burn‑up charts) to visualize completed vs. remaining work over time[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/viewing-insights-from-your-project/about-insights-for-projects#:~:text=You%20can%20create%20historical%20charts,aggregation%20of%20items%20over%20time) and sub‑issue progress fields to visualize progress inside parent issues[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields#:~:text=If%20your%20organization%20uses%20sub,progress%20made%20on%20those%20issues). |
| **Planning & scheduling** | **Roadmaps, date/iteration fields, insights** | Use date fields for start and target dates or iteration fields for sprint cycles. The roadmap layout displays issues on a timeline and allows drag‑and‑drop adjustment[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-roadmap-layout#:~:text=The%20roadmap%20layout%20provides%20a,over%20time%20and%20watch%20progress). Vertical markers for milestones or iteration boundaries provide high‑level visibility. Charts and insights show workloads per assignee, iteration or phase[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/viewing-insights-from-your-project/about-insights-for-projects#:~:text=You%20can%20use%20insights%20for,current%20charts%20and%20historical%20charts). |
| **Metadata & priority** | **Issue fields & custom fields** | Issue fields (Priority, Effort, Start/Target date) provide structured metadata and can be added to projects for filtering, grouping and sorting[github.blog](https://github.blog/changelog/2026-03-12-issue-fields-structured-issue-metadata-is-in-public-preview/#:~:text=Issue%20fields%20are%20now%20available,preview%20for%20select%20GitHub%20organizations)[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-issue-fields#:~:text=Issue%20fields%20are%20currently%20in,feedback%2C%20see%20the%20community%20discussion). Use number fields to track story points or risk; single‑select fields to capture priority or status categories. Default values can be set for text/number/single‑select fields so new items inherit baseline metadata[github.blog](https://github.blog/changelog/2026-04-09-release-info-in-issue-sidebar-and-project-defaults/#:~:text=Default%20values%20for%20project%20fields). |
| **Autonomous flow** | **Built‑in automations, Actions, API** | Combine built‑in status workflows, auto‑add/auto‑archive rules and the `actions/add-to-project` action to automatically capture issues/PRs, set status and phase fields, and archive completed work[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed)[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically#:~:text=You%20can%20configure%20your%20project%27s,repositories%20that%20match%20a%20filter). Use GraphQL and actions to update phase or iteration fields when certain conditions are met[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects#:~:text=Updating%20projects). Automations ensure that the project board mirrors the process template without manual intervention. |

Recommendations for Autonomous Implementation & High‑Level Visibility
---------------------------------------------------------------------

1.  **Define a Phase field** (single‑select) listing each phase of your template. Optionally align phases with milestones to provide completion metrics and timeline markers.
2.  **Standardize issue templates** that include fields for phase, step ID, effort, and target date. Use issue fields or custom fields to capture this metadata; set default values for fields where possible to reduce manual entry[github.blog](https://github.blog/changelog/2026-04-09-release-info-in-issue-sidebar-and-project-defaults/#:~:text=Default%20values%20for%20project%20fields).
3.  **Use sub‑issues for decomposition**: create parent issues representing major deliverables; add sub‑issues to define each contract or step. This ensures traceability, progress tracking and hierarchical visibility[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues#:~:text=You%20can%20add%20sub,and%20group%20by%20parent%20issue).
4.  **Automate triage and status updates**: set up auto‑add workflows to add items matching labels/assignees to the correct project and set the Phase/Status fields. Use built‑in workflows to automatically set status when issues/PRs are opened or closed[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically#:~:text=You%20can%20configure%20your%20project%27s,repositories%20that%20match%20a%20filter)[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed). For multi‑repo work, use the `actions/add-to-project` action to capture events across repositories[github.com](https://github.com/marketplace/actions/add-to-github-projects#:~:text=actions%2Fadd).
5.  **Implement gates via CI**: configure GitHub Actions workflows for each validation gate and require the associated status checks before merging. Update the project’s gate field when checks pass/fail and include gating results in issue comments or fields.
6.  **Leverage roadmaps and charts for visibility**: create roadmap views using start/target date or iteration fields. Use vertical markers for milestones and phases and group the roadmap by fields like assignee or phase[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-roadmap-layout#:~:text=The%20roadmap%20layout%20provides%20a,over%20time%20and%20watch%20progress). Build charts showing workload by phase, progress over time, and sub‑issue completion to give stakeholders a clear overview[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/viewing-insights-from-your-project/about-insights-for-projects#:~:text=You%20can%20use%20insights%20for,current%20charts%20and%20historical%20charts).
7.  **Continuously refine automation**: use the GraphQL API to refine field values or relationships after events (e.g., moving an issue to the next phase when a gate passes). Extend automation to reassign issues, update priorities or move items between iterations based on rules.

By combining these features—custom fields, sub‑issue hierarchies, automations, roadmaps and insights—GitHub Projects can autonomously drive execution of a structured phase‑process template while providing rich, high‑level visibility into progress, workload and bottlenecks.

In summary, the report lays out how GitHub Projects provide a flexible, adaptable workspace where issues, pull requests and custom tasks can be viewed as tables, boards or roadmaps. It highlights built‑in automations that set item status and automatically add or archive issues based on filters, and shows how the `actions/add-to-project` GitHub Action and GraphQL API enable deeper automation for adding items and updating custom fields[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed)[github.com](https://github.com/marketplace/actions/add-to-github-projects#:~:text=actions%2Fadd). It also explains the rich metadata available via custom fields and new organization‑level issue fields for priority, effort and dates[github.blog](https://github.blog/changelog/2026-03-12-issue-fields-structured-issue-metadata-is-in-public-preview/#:~:text=Issue%20fields%20are%20now%20available,preview%20for%20select%20GitHub%20organizations), and notes that sub‑issues allow hierarchical decomposition of tasks up to eight levels deep[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues#:~:text=You%20can%20add%20sub,and%20group%20by%20parent%20issue).

The report then maps these features onto a phase‑process template, suggesting that phases be captured with a custom single‑select field or milestones, while step contracts become issues or sub‑issues. CI workflows serve as gates, pull requests represent execution, and issue closures and milestone progress track completion. Roadmaps and insights provide high‑level visibility, letting teams drag items on a timeline and build charts to visualize workload, progress and bottlenecks[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-roadmap-layout#:~:text=The%20roadmap%20layout%20provides%20a,over%20time%20and%20watch%20progress)[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/viewing-insights-from-your-project/about-insights-for-projects#:~:text=You%20can%20use%20insights%20for,current%20charts%20and%20historical%20charts). Recommendations include defining standardized issue templates, automating triage and status updates, leveraging roadmaps and charts, and refining automation via the API to move items through phases autonomously.

## Response:
4/11/2026, 2:32:35 AM

Here’s your requested report:

Technical Execution Processes for Each GitHub Workspace Solution
================================================================

This document translates the high‑level mapping from the previous report into **concrete technical processes** for implementing each part of a phase‑process template in GitHub Projects. Where possible it references existing documented workflows (docs or sample repositories) and then extends them with custom procedures. The goal is to enable an **autonomous execution flow**: issues and pull requests are automatically created, triaged, progressed through phases, gated by CI checks and visualised via roadmaps and charts.

1\. Mapping Phases to a Project Field or Milestones
---------------------------------------------------

### 1.1 Add a **Phase** field to your project (single‑select)

GitHub Projects support custom single‑select fields. To create a phase field:

1.  Open your project in **table view**, click **Add field**, then **New field** and enter a name like `Phase` or `Process Stage`. Select **Single select** and add options (PH‑00, PH‑01, etc.) with colors and descriptions[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-single-select-fields#:~:text=Adding%20a%20single%20select%20field).
2.  Save the field; it appears as a new column in the project. You can filter and group by this field in board or roadmap views[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-single-select-fields#:~:text=You%20can%20filter%20by%20your,more%20information%2C%20see%20Filtering%20projects).
3.  When new items enter the project they default to **Todo** status. Configure built‑in workflows to set the Phase field to the initial phase (PH‑00) using the GraphQL API (see Section 8).

#### Alternative: Use milestones as phases

Milestones track groups of issues/PRs, display a description, due date and completion percentage[docs.github.com](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones#:~:text=About%20milestones). They can appear as vertical markers on the roadmap. Create a milestone per phase (e.g., `PH‑01 – Design`) and assign issues to the appropriate milestone. Use the Phase field for filtering while milestones provide due‑date tracking and progress metrics.

### 1.2 Create a milestone

1.  Navigate to **Issues → Milestones**. Click **New milestone**, give it a title (e.g., `PH‑01 – Design`) and optional description. Set a due date to define the timeframe[docs.github.com](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones#:~:text=About%20milestones).
2.  Assign issues to the milestone. Drag them within the milestone page to prioritise[docs.github.com](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones#:~:text=You%20can%20prioritize%20open%20issues,new%20location%2C%20and%20dropping%20it).
3.  Milestone progress updates automatically as issues are closed; this can be visualised on roadmaps (vertical markers) and insights charts.

2\. Mapping Step Contracts to Issues and Sub‑issues
---------------------------------------------------

### 2.1 Create issues for each step contract

1.  For each step in your process, create an issue using templates that capture metadata: Phase field (default value: current phase), Step ID, Effort estimate, target date and gate requirements. Use issue forms or issue fields so values are typed and mandatory.
2.  When a contract is complex, create **sub‑issues** for sub‑steps. GitHub allows up to 100 sub‑issues per issue and eight levels of nesting[docs.github.com](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues#:~:text=You%20can%20add%20sub,and%20group%20by%20parent%20issue). Sub‑issues display their relationship to the parent issue and their progress contributes to the parent’s **Sub‑issue progress** field[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields#:~:text=If%20your%20organization%20uses%20sub,progress%20made%20on%20those%20issues).
3.  Use the **Parent issue** field in the project to group items by their parent. You can filter by parent issue ID (e.g., `parent‑issue:"owner/repo#123"`)[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields#:~:text=If%20your%20organization%20uses%20sub,progress%20made%20on%20those%20issues).

### 2.2 Automate creation of issues and sub‑issues

An example from an open‑source repository (`ohmyzsh`) demonstrates how to add issues or pull requests to a project via the GraphQL API:

```
# .github/workflows/project.yml (excerpt)
- name: Read project data
  run: |
    gh api graphql -f query='query($org: String!, $number: Int!) { organization(login: $org){ projectV2(number: $number) { id fields(first:20) { nodes { ... on ProjectV2Field { id name } } } } } }' -f org=$ORGANIZATION -F number=$PROJECT_NUMBER > project_data.json
    cat >> $GITHUB_ENV <<EOF
    PROJECT_ID=$(jq '.data.organization.projectV2.id' project_data.json)
    EOF
- name: Add to project
  env:
    ISSUE_OR_PR_ID: ${{ github.event.issue.node_id || github.event.pull_request.node_id }}
  run: |
    item_id="$(gh api graphql -f query='mutation($project: ID!, $content: ID!) { addProjectV2ItemById(input: {projectId: $project, contentId: $content}) { item { id } } }' -f project=$PROJECT_ID -f content=$ISSUE_OR_PR_ID --jq '.data.addProjectV2ItemById.item.id')"
    echo "ITEM_ID=$item_id" >> $GITHUB_ENV
```

This workflow retrieves the project ID, then adds an issue or PR to the project using the `addProjectV2ItemById` mutation[git.gc4.at](https://git.gc4.at/linux/ohmyzsh/src/commit/b0bffcaf865434711d98b63eddd0aa52be0fbeb1/.github/workflows/project.yml#:~:text=,silent). You can extend this script to create a new issue via the GitHub API and immediately add it to the project.

### 2.3 Assign fields to the new item

After adding an item, set its fields (Phase, Effort, etc.) using the `updateProjectV2ItemFieldValue` mutation. The `ohmyzsh` workflow shows how to set text fields (e.g., `Plugin`, `Theme`) by specifying the field ID and value:

```
- name: Fill Pull Request fields in project
  run: |
    gh api graphql -f query='mutation ( $project: ID!, $item: ID!, $plugin_field: ID!, $plugin_value: String!, $theme_field: ID!, $theme_value: String! ) { set_plugin: updateProjectV2ItemFieldValue(input: { projectId: $project, itemId: $item, fieldId: $plugin_field, value: { text: $plugin_value } }) { projectV2Item { id } } set_theme: updateProjectV2ItemFieldValue(input: { projectId: $project, itemId: $item, fieldId: $theme_field, value: { text: $theme_value } }) { projectV2Item { id } } }' -f project=$PROJECT_ID -f item=$ITEM_ID -f plugin_field=$PLUGIN_FIELD_ID -f plugin_value=$PLUGIN -f theme_field=$THEME_FIELD_ID -f theme_value=$THEME --silent
```

Lines 168‑200 of the workflow illustrate updating multiple fields on the project item[git.gc4.at](https://git.gc4.at/linux/ohmyzsh/src/commit/b0bffcaf865434711d98b63eddd0aa52be0fbeb1/.github/workflows/project.yml#:~:text=,silent). For a phase field, use `value: { singleSelectOptionId: $phase_option_id }` instead of a text value.

3\. Mapping Gates to CI Checks and Required Status Checks
---------------------------------------------------------

### 3.1 Implement gate checks in GitHub Actions

1.  For each gate (e.g., design review, unit tests, security scan), create a separate job in a GitHub Actions workflow. Each job runs the relevant validation and should fail if the gate is not satisfied.
2.  Jobs produce **status checks**. When status checks are required for a branch, the pull request cannot merge until they pass[docs.github.com](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks#:~:text=To%20be%20required%2C%20status%20checks,during%20the%20past%20seven%20days).
3.  Optionally publish gate results to the associated issue via the Checks API or comment. You can also update a custom field (e.g., `Gate status`) in the project via GraphQL.

### 3.2 Configure branch protection rules

1.  Go to **Repository Settings → Branches**. Under **Branch protection rules**, select the base branch (e.g., `main`) and enable **Require status checks to pass before merging**.
2.  Choose the checks corresponding to your gate workflows. Only commit statuses that have completed successfully in the last week can be selected[docs.github.com](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks#:~:text=To%20be%20required%2C%20status%20checks,during%20the%20past%20seven%20days).

### 3.3 Update project gate field after checks

Use a post‑CI step to update the gate status in the project. For example, after tests pass, run a `gh` command similar to Section 2.3 to set the `Gate` field to `Passed` or `Failed`.

4\. Mapping Execution to Pull Requests and Linking Issues
---------------------------------------------------------

### 4.1 Link pull requests to issues

1.  In the pull request body, include `Closes #<issue_number>` or `Fixes #<issue_number>` to automatically close the issue upon merge.
2.  Alternatively, use GitHub’s **Link PR** feature on the issue page. The PR will appear under **Linked pull requests**.

### 4.2 Automatically add PRs to the project and set initial fields

The official GitHub doc provides an example workflow that triggers when a pull request is marked **ready for review**. It retrieves the project and field IDs via the GraphQL API, adds the PR to the project and sets the **Status** to `Todo` and **Date posted** to the current date[docs.github.com](https://docs.github.com/en/enterprise-server@3.16/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token). The workflow:

*   Uses `gh api graphql` to fetch the project and field IDs and parse them with `jq`[docs.github.com](https://docs.github.com/en/enterprise-server@3.16/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token). You can extend this query to fetch your custom Phase field.
*   Adds the PR to the project via `addProjectV2ItemById`[docs.github.com](https://docs.github.com/en/enterprise-server@3.16/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token).
*   Calls `updateProjectV2ItemFieldValue` twice to set the status and date[docs.github.com](https://docs.github.com/en/enterprise-server@3.16/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token).

Modify the `status_value` variable to reference your Phase option (e.g., `In Progress` or `Implementation`).

### 4.3 Set issue status when PR is opened/merged

Built‑in workflows automatically set the `Status` field to **Todo** when an item is added and **Done** when its underlying issue is closed or pull request is merged[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed). Configure these automations in the project settings so that issues and PRs transition automatically without manual updates.

5\. Tracking Completion and Progress
------------------------------------

### 5.1 Closing issues and milestones

*   When a pull request merges or an issue is resolved, the corresponding issue closes. The built‑in workflows will update the project’s **Status** field to **Done**[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed) and automatically archive or move the item if an auto‑archive workflow is configured.
*   Milestones show completion percentage and counts of open/closed items[docs.github.com](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones#:~:text=About%20milestones). Use milestone progress to decide when to move to the next phase.

### 5.2 Use **Sub‑issue progress** and charts

*   Enable the **Sub‑issue progress** field to display the fraction of sub‑issues completed for each parent[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields#:~:text=If%20your%20organization%20uses%20sub,progress%20made%20on%20those%20issues).
*   Create **burn‑up charts** in the _Insights_ tab of the project to show open, completed and not‑planned work over time[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/viewing-insights-from-your-project/about-insights-for-projects#:~:text=You%20can%20create%20historical%20charts,aggregation%20of%20items%20over%20time). Filter by Phase or milestone to visualise progress at each stage.

6\. Planning and Scheduling with Date and Iteration Fields
----------------------------------------------------------

### 6.1 Add and configure date fields

1.  Create a **Start date** and **Target date** field (type: date). These fields capture when work should begin and finish.
2.  On the **roadmap** layout, items appear as bars positioned between their start and target dates. You can drag the bars to adjust dates; vertical markers highlight iterations, milestones and item dates[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-roadmap-layout#:~:text=The%20roadmap%20layout%20provides%20a,over%20time%20and%20watch%20progress).

### 6.2 Use iteration fields for sprints

1.  Create an **Iteration** field. When created, it automatically generates three iterations; you can add more and set durations[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-iteration-fields#:~:text=You%20can%20create%20an%20iteration,iteration%2C%20and%20sort%20by%20iteration).
2.  Group items by iteration on boards or roadmaps to see the current sprint. Use filter values such as `@current` or `@next` to focus on work planned for the current or next iteration[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-iteration-fields#:~:text=You%20can%20create%20an%20iteration,iteration%2C%20and%20sort%20by%20iteration).
3.  Roadmaps display iterations as colored blocks; you can drag items between iterations.

### 6.3 Bulk move items between iterations

GitHub allows moving all items to the next iteration in bulk (March 5 2026 update). Use the project’s **…** menu → **Move items to next iteration** to shift unfinished work[github.blog](https://github.blog/changelog/2026-03-05-hierarchy-view-improvements-and-file-uploads-in-issue-forms/#:~:text=Hierarchy%20view%20improvements%20in%20GitHub,Projects).

7\. Metadata and Priority with Issue Fields
-------------------------------------------

### 7.1 Enable organization‑wide issue fields

Issue fields (in public preview) provide typed metadata like Priority, Effort, Start date and Target date. They are defined at the organization level and available across all repositories. You can search, filter and report on these fields and integrate them into project views[github.blog](https://github.blog/changelog/2026-03-12-issue-fields-structured-issue-metadata-is-in-public-preview/#:~:text=Issue%20fields%20are%20now%20available,preview%20for%20select%20GitHub%20organizations). Issue field values can be edited directly in the project table and are synced back to the underlying issues[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-issue-fields#:~:text=Issue%20fields%20are%20currently%20in,feedback%2C%20see%20the%20community%20discussion)[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-issue-fields#:~:text=Adding%20an%20issue%20field%20to,a%20project).

### 7.2 Using custom number and text fields

Add number fields to track story points, complexity or risk. Text fields can capture references or notes. These fields support filters and range queries[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-text-and-number-fields#:~:text=You%20can%20use%20text%20fields,freeform%20text%20in%20your%20project).

### 7.3 Set default values for fields

GitHub’s April 9 2026 update allows default values for text, number and single‑select fields. Define defaults (e.g., Phase defaults to `PH‑00`, Priority defaults to `Medium`) so new items inherit baseline metadata[github.blog](https://github.blog/changelog/2026-04-09-release-info-in-issue-sidebar-and-project-defaults/#:~:text=Default%20values%20for%20project%20fields).

8\. Autonomous Flow: Built‑in Automations, Actions and GraphQL
--------------------------------------------------------------

### 8.1 Configure built‑in workflows

In the project settings → **Automations**, enable workflows:

*   **Status change** – sets `Status` to **Todo** when an item is added and **Done** when the issue closes or pull request merges[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations#:~:text=Projects%20includes%20built,when%20an%20issue%20is%20closed).
*   **Auto‑archive** – automatically archives items that match criteria (state, reason, date)[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/archiving-items-automatically#:~:text=You%20can%20configure%20your%20project%27s,items%20that%20match%20a%20filter).
*   **Auto‑add** – automatically adds new issues/PRs from specified repositories based on filters such as labels, assignee or reason[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically#:~:text=You%20can%20configure%20your%20project%27s,repositories%20that%20match%20a%20filter). Configure multiple rules for different triage streams.

### 8.2 Use the `actions/add-to-project` GitHub Action

This action adds issues or pull requests to a project when they are opened, labeled or reopened. The README shows how to filter by labels:

```
name: Add bugs to bugs project
on:
  issues:
    types: [opened]
jobs:
  add-to-project:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/add-to-project@RELEASE_VERSION
        with:
          project-url: https://github.com/orgs/<orgName>/projects/<projectNumber>
          github-token: ${{ secrets.ADD_TO_PROJECT_PAT }}
          labeled: bug, needs-triage
          label-operator: OR
```

This workflow adds issues labeled `bug` or `needs‑triage` to the specified project[github.com](https://github.com/actions/add-to-project#:~:text=which%20are%20transferred%20into%20your,operator). The action also supports `NOT` to exclude labels and can target pull requests. You need a personal access token with `repo` and `project` scopes[github.com](https://github.com/actions/add-to-project#:~:text=%2A%20%60project,OR).

### 8.3 Combine GitHub Actions and GraphQL for custom automation

1.  Use `gh api graphql` or Octokit to query the project for field IDs (Phase, Status, Priority) and option IDs (e.g., `In Review`)[docs.github.com](https://docs.github.com/en/enterprise-server@3.16/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token).
2.  Add the issue or PR to the project via `addProjectV2ItemById` and capture the returned item ID[docs.github.com](https://docs.github.com/en/enterprise-server@3.16/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token).
3.  Call `updateProjectV2ItemFieldValue` to set fields such as Phase, Status and Dates. For single‑select fields, specify the `singleSelectOptionId`[docs.github.com](https://docs.github.com/en/enterprise-server@3.16/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token); for text fields, specify `text`[git.gc4.at](https://git.gc4.at/linux/ohmyzsh/src/commit/b0bffcaf865434711d98b63eddd0aa52be0fbeb1/.github/workflows/project.yml#:~:text=,silent); for dates, specify `date`[docs.github.com](https://docs.github.com/en/enterprise-server@3.16/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions#:~:text=,token.outputs.token).
4.  Trigger this workflow on events like `issues.opened`, `pull_request.ready_for_review`, `pull_request.closed` or custom labels to drive the autonomous flow.
5.  Optionally update the Phase field when gates pass or fail: after a CI job completes, run a GraphQL mutation to set `Phase` to the next stage.

### 8.4 Auto‑archive completed items

Create an **auto‑archive** workflow that archives items when they are closed or marked as not planned[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/archiving-items-automatically#:~:text=You%20can%20configure%20your%20project%27s,items%20that%20match%20a%20filter). This removes clutter from the active views while preserving data for reporting.

9\. Putting It All Together
---------------------------

By following these technical processes, you can implement a **self‑driving project board** aligned with your phase‑process template:

1.  **Create the project** with custom fields for Phase, Priority, Effort, Start/Target date and a Gate status. Define milestones for each phase and set up iterations for sprints.
2.  **Standardise issue templates** that include fields for phase, step ID and gating requirements. Use sub‑issues to decompose complex steps.
3.  **Automate intake**: use built‑in auto‑add rules and `actions/add-to-project` to capture new issues and PRs into the project and set default fields.
4.  **Drive progression**: configure CI workflows as gates; require their status checks to pass before merging. Use GraphQL actions to update the Phase field and gate status when conditions are met.
5.  **Track and visualise**: close issues to complete steps; use milestone and sub‑issue progress, burn‑up charts and roadmaps to monitor progress across phases.
6.  **Refine automation**: iterate on rules and scripts to improve triage, field updates and gating. Use default field values and issue fields to reduce manual data entry[github.blog](https://github.blog/changelog/2026-04-09-release-info-in-issue-sidebar-and-project-defaults/#:~:text=Default%20values%20for%20project%20fields).

These processes enable a GitHub project to mirror your phase‑process template, drive work autonomously via automations and CI checks, and provide high‑level visibility through roadmaps and insights.

In summary, this document delivers a comprehensive, step-by-step guide to implementing autonomous, phase-based project management in GitHub. It covers creating and configuring custom fields for phases, milestones, iteration planning, and detailed issue metadata. The report demonstrates how to automate intake using built-in workflows and the `actions/add-to-project` action, and how to employ GitHub Actions with GraphQL to set and update project fields and statuses.

The report also illustrates how to configure CI-based gate checks with branch protection, link pull requests to issues, and visualize progress through milestones, sub-issue tracking, roadmaps, and burn-up charts. By combining these techniques, teams can mirror their phase-process template within GitHub Projects and achieve continuous visibility into workload and progress while minimizing manual overhead[docs.github.com](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-single-select-fields#:~:text=Adding%20a%20single%20select%20field).

Feel free to ask if you need anything else.

## Response:
4/11/2026, 7:54:59 AM

The evaluation is accurate. The system you have now is **structurally correct but operationally incomplete**. The attached workflows confirm that: you already have most of the building blocks, but they are not wired into a deterministic execution system.

Below is a **direct mapping from your evaluation gaps → concrete execution processes using your actual workflows**.

* * *

1\. What You Already Have (Reality Check)
=========================================

You are not starting from scratch. You already have:

### A. Orchestration layer

*   Scheduled orchestrator running daily  
    →
    TEMP\_scheduled-orchestrator

### B. CI / Gate system (partial but strong)

*   Full quality gate pipeline  
    →
    TEMP\_quality-gates
*   Incomplete implementation blocker  
    →
    TEMP\_incomplete-scanner
*   Registry + pattern validation  
    →
    TEMP\_project\_item\_sync
    ,
    TEMP\_validate-patterns

### C. GitHub Project sync layer (critical)

*   Project item sync (issues/PRs → project fields)  
    →
    TEMP\_project\_item\_sync
*   Milestone completion sync  
    →
    TEMP\_milestone\_completion
*   Phase plan → GitHub sync  
    →
    TEMP\_splinter\_phase\_sync

### D. Bidirectional sync system

*   Remote → local trigger  
    →
    TEMP\_triggerA-remote-to-local
*   Remote sync handler  
    →
    TEMP\_remote-sync

### E. Deployment + lifecycle

*   Staging + production pipelines  
    →
    TEMP\_deploy-production
    ,
    TEMP\_deploy-staging

* * *

2\. Critical Finding (From Your Evaluation)
===========================================

The system is missing one thing:

> **A deterministic decision engine that connects all of this.**

Everything exists as **independent workflows**, not a **controlled state machine**.

* * *

3\. Required Architecture Fix
=============================

You need to introduce one core component:

**Phase Advancement Evaluator (PAE)**
-------------------------------------

This directly resolves your biggest gap:

> Phase transition logic is undefined
> 
> GitHub PM and NPP gap analysis

* * *

4\. Full Technical Execution Process (Final Design)
===================================================

This is the **actual runtime system**, not theory.

* * *

PROCESS 1 — Intake & Registration
---------------------------------

### Trigger

*   Issue opened / PR opened
*   Workflow: Project Item Sync  
    →
    TEMP\_project\_item\_sync

### Execution

1.  Add item to project
2.  Assign:
    *   Phase = PH-00
    *   Status = TODO
3.  Map labels → phase via:
    *   `PHASE_LABEL_MAP_JSON`

### Output

*   GitHub Project item created
*   Initial state assigned

* * *

PROCESS 2 — Plan → GitHub Sync (SSOT Injection)
-----------------------------------------------

### Trigger

*   Change to `phases/*.yaml`  
    →
    TEMP\_splinter\_phase\_sync

### Execution

1.  Parse phase file
2.  Create/update:
    *   Issues (step contracts)
    *   Sub-issues (decomposition)
3.  Map:
    *   Phase → Project field
    *   Step → Issue
    *   Gate → CI job

### Output

*   GitHub becomes execution surface
*   Plan remains SSOT

* * *

PROCESS 3 — Execution Pipeline (13-Step Mapping)
------------------------------------------------

You identified this gap correctly.

### REQUIRED MAPPING

| Pipeline Stage | GitHub State |
| --- | --- |
| Trigger | Issue created |
| Ingest | Project item created |
| Identify | Step contract assigned |
| Lock | Issue assigned |
| Validate (pre) | CI pre-commit |
| Process | Branch + PR |
| Generate | Code changes |
| Commit | PR open |
| Validate (post) | CI gates |
| Rollback | PR fail |
| Complete | Issue closed |

* * *

PROCESS 4 — Gate Execution System
---------------------------------

### Trigger

*   PR opened / updated
*   CI Pipeline  
    →
    TEMP\_quality-gates

### Execution

Runs:

*   Lint
*   Tests
*   Coverage gates
*   Security scan
*   Structure validation
*   Incomplete implementation scan

Example enforcement:

*   Fail if violations exceed threshold  
    →
    TEMP\_incomplete-scanner

### Output

*   Binary pass/fail (correct)
*   Artifacts stored

* * *

PROCESS 5 — Phase Advancement Evaluator (NEW – REQUIRED)
--------------------------------------------------------

### Trigger

*   After CI completion OR scheduled run

### Implementation

Add new workflow:

```
name: Phase Advancement Evaluator

on:
  workflow_run:
    workflows: ["Quality Gates"]
    types: [completed]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - name: Evaluate Phase Exit Criteria
        run: python scripts/phase_evaluator.py
```

* * *

### Evaluation Logic (MANDATORY)

For each issue:

```
IF:
  all_required_checks_passed == true
  AND no_open_sub_issues == true
  AND milestone_complete == true
THEN:
  advance_phase()
ELSE:
  do_not_advance()
```

* * *

### Output

GraphQL mutation:

```
updateProjectV2ItemFieldValue:
  Phase = NEXT_PHASE
```

* * *

PROCESS 6 — Sync Enforcement (Critical Fix)
-------------------------------------------

Your evaluation identified:

> Sync direction undefined
> 
> GitHub PM and NPP gap analysis

### REQUIRED RULE

```
SSOT = PLAN JSON
GitHub = EXECUTION SURFACE ONLY
```

* * *

### Enforcement Mechanism

Add nightly validator:

```
name: SSOT Drift Detection
on:
  schedule:
    - cron: '0 3 * * *'
```

Checks:

*   GitHub Phase == Plan Phase
*   GitHub Step status == Plan state

If mismatch:

*   Fail workflow
*   Open issue

* * *

PROCESS 7 — Field ID Bootstrap System (Fix Gap 3)
-------------------------------------------------

### Required File

```
/config/github_field_registry.json
```

### Generator Workflow

```
name: Bootstrap Project Fields
on: workflow_dispatch
```

Execution:

*   Query project via GraphQL
*   Extract:
    *   field IDs
    *   option IDs
*   Store in repo

* * *

PROCESS 8 — Windows / Runner Split (Fix Gap 4)
----------------------------------------------

### Current Problem

Everything runs on ubuntu:

→

TEMP\_quality-gates

### Solution

Split jobs:

```
jobs:
  linux-gates:
    runs-on: ubuntu-latest

  windows-gates:
    runs-on: [self-hosted, windows]
```

You already have:  
→

TEMP\_triggerA-remote-to-local

Reuse that runner.

* * *

PROCESS 9 — Authentication Upgrade (Fix Gap 1)
----------------------------------------------

Replace:

```
PROJECT_TOKEN (PAT)
```

With:

```
GitHub App installation token
```

### Required Change

All workflows:

```
PROJECT_TOKEN → APP_TOKEN
```

* * *

PROCESS 10 — Full Autonomous Loop
---------------------------------

### Final System Flow

1.  Plan updated → sync to GitHub
2.  Issue created → enters Phase PH-00
3.  Work begins → PR created
4.  CI runs → gates enforced
5.  Phase evaluator checks completion
6.  Phase advances automatically
7.  Milestone completes → next phase triggered
8.  Deployment runs
9.  Orchestrator validates system daily  
    →
    TEMP\_scheduled-orchestrator

* * *

5\. What You Are Missing (Condensed)
====================================

From your evaluation, the real missing pieces are:

### MUST BUILD

*   Phase Advancement Evaluator
*   Field ID bootstrapper
*   SSOT drift validator

### MUST CHANGE

*   PAT → GitHub App
*   Linux-only runners → hybrid runners

### MUST DEFINE

*   Phase exit criteria (explicit)
*   Sync direction (SSOT enforced)

* * *

6\. Bottom Line
===============

Your evaluation is correct:

> “The framework’s bones are solid. The gaps are in determinism enforcement.”
> 
> GitHub PM and NPP gap analysis

What you actually have:

*   80% infrastructure complete
*   0% deterministic control layer

What this response gives you:

*   The **exact execution layer needed to make it autonomous**

* * *

If you want next step:

I can convert this into a **single machine-executable orchestration spec (JSON)** that wires every workflow, trigger, and gate into one deterministic system.



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)