export default function ABTestsIndex() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">A/B thumbnail</h1>
      <p className="text-sm opacity-70">
        Tạo test 2–6 biến thể, hệ thống quyết định người thắng khi đủ dữ liệu (Bayesian, P &ge;
        95%).
      </p>
      <div className="rounded-lg border border-[rgb(var(--border))] p-6 text-sm opacity-70">
        UI tạo test sẽ thêm sau. Hiện tại dùng API <code>POST /api/v1/ab-tests</code>.
      </div>
    </div>
  );
}
