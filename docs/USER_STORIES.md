# User Stories

Format: *As a [persona], I want [goal], so that [benefit].* Each story has acceptance criteria (AC).

## Epic A: Session and privacy

- **US-01 Anonymous start.** As a visitor, I want to use the app without signing up, so that I can try it immediately.
  - **AC:** First visit creates a session; cookie is `Secure` and `HttpOnly`; no token appears in any URL or response body.
- **US-02 Automatic deletion.** As a user, I want my data deleted after 24 hours, so that my files are not kept.
  - **AC:** Expired sessions are rejected on access and purged by the scheduled cleanup; schemas and metadata rows are both removed.
- **US-03 Delete now.** As a user, I want to delete my data immediately, so that I control my privacy.
  - **AC:** One action removes all datasets and history for my session and confirms completion.

## Epic B: Upload and schema

- **US-04 Upload a file.** As a user, I want to upload CSV or Excel, so that I can analyse my data.
  - **AC:** Files over the limit, wrong types, and corrupt files give specific, friendly errors; each sheet becomes a table.
- **US-05 Review the schema.** As a user, I want to see column names and inferred types, so that I can confirm the data loaded correctly.
  - **AC:** Preview shows the first rows; I can rename a column or override a type before querying.
- **US-06 Try sample data.** As a reviewer, I want sample datasets, so that I can evaluate the app without my own file.
  - **AC:** One click loads a sample into my session.

## Epic C: Ask and answer

- **US-07 Ask a question.** As a user, I want to ask in plain English, so that I get an answer without writing SQL.
  - **AC:** The answer shows the plan summary (when used), the SQL, and the result table.
- **US-08 Clarification.** As a user, I want to be asked when my question is ambiguous, so that I do not get a wrong answer.
  - **AC:** Ambiguous questions produce one targeted clarifying question with selectable options.
- **US-09 Safe execution.** As a user, I want queries to never change or leak data, so that I can trust the tool.
  - **AC:** Any mutation, multi-statement, locking, unknown-table, or disallowed-function query is rejected with an explanation. Execution uses the read-only role and respects time and row limits.
- **US-10 Follow-up questions.** As a user, I want to refer to my previous answer, so that I can drill down naturally.
  - **AC:** The plan stage receives the last few questions and their plans as context.

## Epic D: Visualise and explain

- **US-11 Charts.** As a user, I want a suitable chart, so that I can see patterns quickly.
  - **AC:** The chart spec only references columns that exist in the result. Invalid specs fall back to the table with a note.
- **US-12 Insights.** As a user, I want a short written explanation and suggested next steps, so that I understand what the numbers mean.
  - **AC:** Insights cite figures from the result and never claim facts outside it.

## Epic E: Reports

- **US-13 Build a report.** As a user, I want to pin answers into a report and download it, so that I can share findings.
  - **AC:** Report includes question, SQL, table, chart, and insights per item; export to PDF and HTML.

## Epic F: Quality

- **US-14 See accuracy.** As a reviewer, I want to run the evaluation, so that I can judge how reliable the system is.
  - **AC:** The eval page runs a chosen golden set and shows accuracy, rejection rate, latency, token cost, and failure categories.
- **US-15 Fair usage.** As the operator, I want rate limits and quota guards, so that the free tiers survive public traffic.
  - **AC:** Exceeding limits returns a clear message with a retry time.
