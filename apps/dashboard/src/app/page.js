import DashboardShell from "../components/dashboard-shell";

export default function DashboardPage() {
  const apiBaseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.PUBLIC_API_BASE_URL ||
    "http://localhost:8000";

  return <DashboardShell apiBaseUrl={apiBaseUrl} />;
}
