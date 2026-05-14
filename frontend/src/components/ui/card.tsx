import clsx from 'clsx';

export function Card({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={clsx(
        'rounded-lg border border-[rgb(var(--border))] bg-white dark:bg-neutral-900 p-5',
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children }: { children: React.ReactNode }) {
  return <div className="mb-3 text-sm font-medium opacity-70">{children}</div>;
}

export function Metric({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardHeader>{label}</CardHeader>
      <div className="text-2xl font-semibold tabular-nums">{value}</div>
      {hint && <div className="mt-1 text-xs opacity-60">{hint}</div>}
    </Card>
  );
}
