import { notFound } from 'next/navigation';
import { Card, CardHeader, Metric } from '@/components/ui/card';
import { api, ApiError } from '@/lib/api';
import { formatNumber, formatPct } from '@/lib/format';
import type { ABTest, ABTestResults } from '@/lib/types';

async function load(id: string) {
  try {
    const [test, results] = await Promise.all([
      api<ABTest>(`/ab-tests/${id}`),
      api<ABTestResults>(`/ab-tests/${id}/results`),
    ]);
    return { test, results };
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }
}

export default async function ABTestDetail({ params }: { params: { id: string } }) {
  const { test, results } = await load(params.id);
  const winner = results.recommended_winner
    ? test.variants.find((v) => v.id === results.recommended_winner)
    : null;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">{test.name}</h1>
        <p className="mt-1 text-sm opacity-70">{test.hypothesis ?? 'Chưa nêu giả thuyết.'}</p>
      </header>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Metric label="Trạng thái" value={test.status} />
        <Metric
          label="Đủ dữ liệu?"
          value={results.has_enough_data ? 'Đã đủ' : 'Chưa đủ'}
          hint={`Tối thiểu ${formatNumber(test.min_impressions_per_variant)} impression/variant`}
        />
        <Metric label="Độ tin cậy" value={formatPct(results.decision_confidence)} />
        <Metric
          label="Người thắng"
          value={winner ? `Biến thể ${winner.label}` : '—'}
          hint={results.has_enough_data ? 'Theo Bayesian P(best)' : 'Đang chờ thêm dữ liệu'}
        />
      </div>

      <Card>
        <CardHeader>Giải thích</CardHeader>
        <p className="text-sm leading-relaxed">{results.explain}</p>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {results.variants.map((r) => {
          const v = test.variants.find((x) => x.id === r.variant_id);
          const isWinner = r.variant_id === results.recommended_winner;
          return (
            <Card key={r.variant_id} className={isWinner ? 'ring-2 ring-brand-500' : undefined}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <span>Biến thể {r.label}</span>
                  {isWinner && (
                    <span className="rounded-full bg-brand-500 px-2 py-0.5 text-xs text-white">
                      Winner
                    </span>
                  )}
                </div>
              </CardHeader>
              {v?.thumbnail_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={v.thumbnail_url}
                  alt={r.label}
                  className="mb-3 aspect-video w-full rounded-md object-cover"
                />
              )}
              <dl className="grid grid-cols-2 gap-y-2 text-sm">
                <dt className="opacity-70">Impressions</dt>
                <dd className="text-right tabular-nums">{formatNumber(r.impressions)}</dd>
                <dt className="opacity-70">Clicks</dt>
                <dd className="text-right tabular-nums">{formatNumber(r.clicks)}</dd>
                <dt className="opacity-70">CTR</dt>
                <dd className="text-right tabular-nums">{formatPct(r.ctr, 2)}</dd>
                <dt className="opacity-70">95% CI</dt>
                <dd className="text-right tabular-nums">
                  [{formatPct(r.ctr_ci_low, 2)}, {formatPct(r.ctr_ci_high, 2)}]
                </dd>
                <dt className="opacity-70">P(best)</dt>
                <dd className="text-right tabular-nums">{formatPct(r.prob_best, 1)}</dd>
              </dl>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
