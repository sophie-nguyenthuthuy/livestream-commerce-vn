'use client';

import { useMemo } from 'react';
import {
  Area,
  AreaChart,
  Bar,
  ComposedChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { StreamMinute } from '@/lib/types';
import { formatTime, formatVND } from '@/lib/format';

interface Props {
  minutes: StreamMinute[];
}

export function ViewersChart({ minutes }: Props) {
  const data = useMemo(
    () =>
      minutes.map((m) => ({
        t: formatTime(m.bucket_ts),
        viewers: m.concurrent_viewers,
        new: m.new_viewers,
      })),
    [minutes],
  );

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
        <XAxis dataKey="t" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area
          type="monotone"
          dataKey="viewers"
          name="Người xem đồng thời"
          stroke="#ff2d55"
          fill="#ff2d5520"
        />
        <Area
          type="monotone"
          dataKey="new"
          name="Người xem mới"
          stroke="#5b8def"
          fill="#5b8def20"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function ConversionChart({ minutes }: Props) {
  const data = useMemo(
    () =>
      minutes.map((m) => ({
        t: formatTime(m.bucket_ts),
        clicks: m.product_clicks,
        carts: m.add_to_carts,
        orders: m.orders,
        gmv: Number(m.gmv_vnd),
      })),
    [minutes],
  );

  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={data} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
        <XAxis dataKey="t" tick={{ fontSize: 11 }} />
        <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fontSize: 11 }}
          tickFormatter={(v) => formatVND(v)}
        />
        <Tooltip formatter={(v: number, n) => (n === 'GMV' ? formatVND(v) : v)} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar yAxisId="left" dataKey="clicks" name="Bấm sản phẩm" fill="#94a3b8" />
        <Bar yAxisId="left" dataKey="carts" name="Vào giỏ" fill="#5b8def" />
        <Bar yAxisId="left" dataKey="orders" name="Đơn hàng" fill="#ff2d55" />
        <Area
          yAxisId="right"
          type="monotone"
          dataKey="gmv"
          name="GMV"
          stroke="#10b981"
          fill="#10b98120"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
