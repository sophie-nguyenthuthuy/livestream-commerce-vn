import './globals.css';
import type { Metadata } from 'next';
import Link from 'next/link';
import { Radio, BarChart3, FileText, FlaskConical } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Livestream Commerce VN',
  description: 'Analytics & AI co-pilot for TikTok Shop livestream sellers in Vietnam',
};

const nav = [
  { href: '/dashboard', label: 'Tổng quan', icon: BarChart3 },
  { href: '/streams', label: 'Livestream', icon: Radio },
  { href: '/scripts', label: 'Kịch bản AI', icon: FileText },
  { href: '/ab-tests', label: 'A/B thumbnail', icon: FlaskConical },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="min-h-screen">
        <div className="flex min-h-screen">
          <aside className="w-60 shrink-0 border-r border-[rgb(var(--border))] px-4 py-6">
            <Link href="/dashboard" className="flex items-center gap-2 px-2 mb-6">
              <span className="size-2.5 rounded-full bg-brand-500" />
              <span className="font-semibold tracking-tight">Livestream VN</span>
            </Link>
            <nav className="space-y-1">
              {nav.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-black/5 dark:hover:bg-white/5"
                >
                  <Icon className="size-4 opacity-70" />
                  <span>{label}</span>
                </Link>
              ))}
            </nav>
          </aside>
          <main className="flex-1 p-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
