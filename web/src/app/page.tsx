import { DatasetWorkspace } from "@/features/datasets";

export default function HomePage() {
  return (
    <main>
      <header style={{ maxWidth: "960px", margin: "2rem auto 0", padding: "0 1rem" }}>
        <h1>AI Data Analyst</h1>
        <p>
          Upload a spreadsheet and ask natural-language questions over validated, read-only SQL.
        </p>
      </header>
      <DatasetWorkspace />
    </main>
  );
}
