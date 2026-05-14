'use client';

import { useState } from 'react';
import { Card, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api, ApiError } from '@/lib/api';
import type { Dialect, ScriptGenerateResponse, ScriptIntent } from '@/lib/types';

const DIALECTS: { value: Dialect; label: string }[] = [
  { value: 'NORTH', label: 'Giọng Bắc (Hà Nội)' },
  { value: 'SOUTH', label: 'Giọng Nam (Sài Gòn)' },
  { value: 'NEUTRAL', label: 'Trung tính' },
];

const INTENTS: { value: ScriptIntent; label: string }[] = [
  { value: 'HOOK', label: 'Mở đầu (Hook)' },
  { value: 'PITCH', label: 'Giới thiệu sản phẩm' },
  { value: 'SOCIAL_PROOF', label: 'Bằng chứng xã hội' },
  { value: 'OBJECTION', label: 'Xử lý từ chối' },
  { value: 'URGENCY', label: 'Tạo khẩn cấp' },
  { value: 'CLOSE', label: 'Chốt đơn' },
];

export default function ScriptsPage() {
  const [dialect, setDialect] = useState<Dialect>('SOUTH');
  const [intent, setIntent] = useState<ScriptIntent>('HOOK');
  const [productName, setProductName] = useState('');
  const [category, setCategory] = useState('');
  const [persona, setPersona] = useState('');
  const [duration, setDuration] = useState(30);
  const [n, setN] = useState(3);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScriptGenerateResponse | null>(null);

  async function onGenerate() {
    setLoading(true);
    setError(null);
    try {
      const out = await api<ScriptGenerateResponse>('/scripts/generate', {
        method: 'POST',
        body: JSON.stringify({
          dialect,
          intent,
          product_name: productName || null,
          product_category: category || null,
          audience_persona: persona || null,
          target_duration_sec: duration,
          n_variants: n,
        }),
      });
      setResult(out);
    } catch (e) {
      setError(
        e instanceof ApiError ? `${e.status}: ${e.message}` : (e as Error).message,
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Kịch bản AI</h1>
        <p className="mt-1 text-sm opacity-70">
          Gợi ý lời thoại livestream bằng tiếng Việt, giọng Bắc hoặc Nam.
        </p>
      </header>

      <Card>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Field label="Giọng vùng miền">
            <select
              className="input"
              value={dialect}
              onChange={(e) => setDialect(e.target.value as Dialect)}
            >
              {DIALECTS.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Mục đích đoạn">
            <select
              className="input"
              value={intent}
              onChange={(e) => setIntent(e.target.value as ScriptIntent)}
            >
              {INTENTS.map((i) => (
                <option key={i.value} value={i.value}>
                  {i.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Sản phẩm">
            <input
              className="input"
              placeholder="Ví dụ: Serum Vitamin C 30ml"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
            />
          </Field>
          <Field label="Ngành hàng">
            <input
              className="input"
              placeholder="skincare, fashion, home…"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            />
          </Field>
          <Field label="Khách mục tiêu">
            <input
              className="input"
              placeholder="Nữ 25-35, da dầu, ngân sách dưới 300k"
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
            />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Độ dài (giây)">
              <input
                type="number"
                min={10}
                max={180}
                className="input"
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
              />
            </Field>
            <Field label="Số biến thể">
              <input
                type="number"
                min={1}
                max={5}
                className="input"
                value={n}
                onChange={(e) => setN(Number(e.target.value))}
              />
            </Field>
          </div>
        </div>
        <div className="mt-4 flex items-center justify-end gap-3">
          {error && <span className="text-sm text-brand-600">{error}</span>}
          <Button onClick={onGenerate} disabled={loading}>
            {loading ? 'Đang sinh…' : 'Sinh kịch bản'}
          </Button>
        </div>
      </Card>

      {result && (
        <div className="space-y-3">
          <div className="text-sm opacity-70">
            Model: <span className="font-mono">{result.model}</span> · Giọng {result.dialect} ·{' '}
            {result.intent}
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {result.variants.map((v, i) => (
              <Card key={i}>
                <CardHeader>{v.title}</CardHeader>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{v.body}</p>
                <div className="mt-3 flex flex-wrap gap-1 text-xs">
                  <span className="rounded bg-black/5 px-2 py-0.5 dark:bg-white/10">
                    ~{v.estimated_duration_sec}s
                  </span>
                  {v.tags.map((t) => (
                    <span
                      key={t}
                      className="rounded bg-black/5 px-2 py-0.5 dark:bg-white/10"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
      <style jsx>{`
        .input {
          width: 100%;
          border-radius: 6px;
          border: 1px solid rgb(var(--border));
          background: transparent;
          padding: 6px 10px;
          font-size: 14px;
        }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs opacity-70">{label}</span>
      {children}
    </label>
  );
}
