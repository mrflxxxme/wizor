// P1 health-страница: подтверждает, что frontend собирается и рендерится.
// Продуктовый UI (Tier 0 Instant Audit) — P7.
export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-2 p-8">
      <h1 className="text-2xl font-semibold">WIZOR</h1>
      <p className="text-sm text-gray-500">AI Readiness Platform · foundation OK</p>
      <span data-testid="health-status" className="text-xs text-green-600">
        status: ok
      </span>
    </main>
  );
}
