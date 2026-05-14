import { notFound } from 'next/navigation';
import { Card, CardHeader, Metric } from '@/components/ui/card';
import { ConversionChart, ViewersChart } from '@/components/charts/MinuteChart';
import { api, ApiError } from '@/lib/api';
import { formatNumber, formatPct, formatVND } from '@/lib/format';
import type { ConversionFunnel, Stream, StreamMinute } from '@/lib/types';

interface PageProps {
  params: { id: string };
}

async function load(id: string) {
  try {
    const [stream, minutes, funnel] = await Promise.all([
      api<Stream>(`/streams/${id}`),
      api<StreamMinute[]>(`/streams/${id}/minutes?limit=240`),
      api<ConversionFunnel>(`/streams/${id}/conversion`),
    ]);
    return { stream, minutes, funnel };
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }
}

export default async function StreamDetailPage({ params }: PageProps) {
  const { stream, minutes, funnel } = await load(params.id);

  return (
    <div className="space-y-6">
      <header>
        <div className="flex items-center gap-2">
          <span
            className={
              stream.status === 'LIVE'
                ? 'inline-flex items-center gap-1 rounded-full bg-brand-100 px-2 py-0.5 text-xs text-brand-700'
                : 'rounded-full border border-[rgb(var(--border))] px-2 py-0.5 text-xs opacity-70'
            }
          >
            {stream.status === 'LIVE' && (
              <span className="size-1.5 animate-pulse rounded-full bg-brand-500" />
            )}
            {stream.status}
          </span>
          <span className="text-xs opacity-60">{stream.host_handle}</span>
        </div>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">{stream.title}</h1>
      </header>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Metric label="GMV" value={formatVND(funnel.gmv_vnd)} />
        <Metric label="Đơn hàng" value={formatNumber(funnel.orders)} />
        <Metric label="AOV" value={formatVND(funnel.aov_vnd)} />
        <Metric label="CVR tổng" value={formatPct(funnel.order_rate * funnel.cart_rate * funnel.click_through_rate)} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>Người xem theo phút</CardHeader>
          <ViewersChart minutes={minutes} />
        </Card>
        <Card>
          <CardHeader>Phễu chuyển đổi theo phút</CardHeader>
          <ConversionChart minutes={minutes} />
        </Card>
      </div>

      <Card>
        <CardHeader>Phễu cộng dồn</CardHeader>
        <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <FunnelStep label="Người xem mới" value={funnel.viewers} />
          <FunnelStep
            label="Bấm sản phẩm"
            value={funnel.product_clicks}
            rate={funnel.click_through_rate}
          />
          <FunnelStep label="Vào giỏ" value={funnel.add_to_carts} rate={funnel.cart_rate} />
          <FunnelStep label="Đơn hàng" value={funnel.orders} rate={funnel.order_rate} />
        </div>
      </Card>
    </div>
  );
}

function FunnelStep({ label, value, rate }: { label: string; value: number; rate?: number }) {
  return (
    <div className="rounded-md border border-[rgb(var(--border))] p-3">
      <div className="text-xs opacity-60">{label}</div>
      <div className="mt-1 text-lg font-semibold tabular-nums">{formatNumber(value)}</div>
      {rate !== undefined && (
        <div className="mt-1 text-xs opacity-70">{formatPct(rate)} từ bước trước</div>
      )}
    </div>
  );
}
