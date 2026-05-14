export type Platform = 'TIKTOK_SHOP' | 'SHOPEE_LIVE' | 'LAZADA_LIVE';
export type StreamStatus = 'SCHEDULED' | 'LIVE' | 'ENDED';
export type Dialect = 'NORTH' | 'SOUTH' | 'NEUTRAL';
export type ScriptIntent =
  | 'HOOK'
  | 'PITCH'
  | 'SOCIAL_PROOF'
  | 'OBJECTION'
  | 'URGENCY'
  | 'CLOSE';

export interface Stream {
  id: string;
  platform: Platform;
  platform_stream_id: string;
  host_handle: string;
  title: string;
  status: StreamStatus;
  started_at: string | null;
  ended_at: string | null;
  total_viewers: number;
  peak_concurrent_viewers: number;
  total_orders: number;
  gmv_vnd: string;
}

export interface StreamMinute {
  bucket_ts: string;
  concurrent_viewers: number;
  new_viewers: number;
  comments: number;
  likes: number;
  product_clicks: number;
  add_to_carts: number;
  orders: number;
  gmv_vnd: string;
  featured_product_id: string | null;
}

export interface ConversionFunnel {
  viewers: number;
  product_clicks: number;
  add_to_carts: number;
  orders: number;
  click_through_rate: number;
  cart_rate: number;
  order_rate: number;
  gmv_vnd: string;
  aov_vnd: string;
}

export interface ScriptVariant {
  title: string;
  body: string;
  estimated_duration_sec: number;
  tags: string[];
}

export interface ScriptGenerateResponse {
  dialect: Dialect;
  intent: ScriptIntent;
  model: string;
  variants: ScriptVariant[];
}

export interface ABTestVariant {
  id: string;
  label: string;
  thumbnail_url: string;
  weight: number;
}

export interface ABTest {
  id: string;
  name: string;
  hypothesis: string | null;
  product_id: string | null;
  status: 'DRAFT' | 'RUNNING' | 'PAUSED' | 'DECIDED' | 'ARCHIVED';
  started_at: string | null;
  decided_at: string | null;
  min_impressions_per_variant: number;
  confidence_target: number;
  winner_variant_id: string | null;
  variants: ABTestVariant[];
}

export interface ABVariantResult {
  variant_id: string;
  label: string;
  impressions: number;
  clicks: number;
  ctr: number;
  ctr_ci_low: number;
  ctr_ci_high: number;
  prob_best: number;
}

export interface ABTestResults {
  test_id: string;
  status: ABTest['status'];
  variants: ABVariantResult[];
  has_enough_data: boolean;
  recommended_winner: string | null;
  decision_confidence: number;
  explain: string;
}
