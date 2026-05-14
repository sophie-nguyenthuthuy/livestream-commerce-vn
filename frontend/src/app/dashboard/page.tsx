import Link from 'next/link';
import { Metric } from '@/components/ui/card';
import { api } from '@/lib/api';
import type { Stream } from '@/lib/types';
import { formatNumber, formatVND } from '@/lib/format';

async function getRecentStreams(): Promise<Stream[]> {
  try {
    // Endpoint not implemented yet — returns empty when API up but no list endpoint.
    // Kept here so the dashboard shell is usable from day one.
    return await api<Stream[]>('/streams/recent').catch(() => []);
  } catch {
    return [];
  }
}

export default async function DashboardPage() {
  const streams = await getRecentStreams();
  const liveCount = streams.filter((s) => s.status === 'LIVE').length;
  const todaysGmv = streams.reduce((acc, s) => acc + Number(s.gmv_vnd), 0);
  const totalOrders = streams.reduce((acc, s) => acc + s.total_orders, 0);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Tổng quan</h1>
        <p className="mt-1 text-sm opacity-70">
          Dữ liệu livestream TikTok Shop hôm nay. Cập nhật theo phút.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Đang live" value={String(liveCount)} hint="livestream đang phát" />
        <Metric label="GMV hôm nay" value={formatVND(todaysGmv)} />
        <Metric label="Đơn hàng" value={formatNumber(totalOrders)} />
        <Metric label="Phiên hôm nay" value={String(streams.length)} />
      </div>

      <section className="rounded-lg border border-[rgb(var(--border))] bg-white dark:bg-neutral-900">
        <div className="border-b border-[rgb(var(--border))] px-5 py-3 text-sm font-medium">
          Livestream gần đây
        </div>
        {streams.length === 0 ? (
          <div className="px-5 py-10 text-center text-sm opacity-60">
            Chưa có livestream nào. Chạy <code>make seed</code> để tạo dữ liệu demo.
          </div>
        ) : (
          <ul className="divide-y divide-[rgb(var(--border))]">
            {streams.map((s) => (
              <li key={s.id} className="px-5 py-3">
                <Link href={`/streams/${s.id}`} className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{s.title}</div>
                    <div className="text-xs opacity-60">
                      {s.host_handle} · {s.status}
                    </div>
                  </div>
                  <div className="text-sm tabular-nums">{formatVND(s.gmv_vnd)}</div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
