"""Seed a demo livestream with 60 minutes of synthetic per-minute data."""

from __future__ import annotations

import asyncio
import random
import unicodedata
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.product import Product
from app.models.stream import (
    Platform,
    Stream,
    StreamMinute,
    StreamProduct,
    StreamStatus,
)


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


DEMO_PRODUCTS = [
    {"sku": "SKN-001", "name": "Serum Vitamin C 30ml", "category": "skincare", "price_vnd": Decimal("189000")},
    {"sku": "SKN-002", "name": "Kem Chống Nắng SPF50+", "category": "skincare", "price_vnd": Decimal("249000")},
    {"sku": "FSH-001", "name": "Áo Sơ Mi Linen Nữ", "category": "fashion", "price_vnd": Decimal("329000")},
    {"sku": "HM-001", "name": "Bình Giữ Nhiệt 500ml", "category": "home", "price_vnd": Decimal("159000")},
]


async def main() -> None:
    rng = random.Random(20260514)
    async with SessionLocal() as db:
        # idempotent
        await db.execute(delete(StreamMinute))
        await db.execute(delete(StreamProduct))
        await db.execute(delete(Stream))
        await db.execute(delete(Product))
        await db.commit()

        products = [
            Product(id=uuid4(), name_normalized=_normalize(str(p["name"])), **p)
            for p in DEMO_PRODUCTS
        ]
        db.add_all(products)

        start = datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(hours=1)
        stream = Stream(
            id=uuid4(),
            platform=Platform.TIKTOK_SHOP,
            platform_stream_id="demo-12345",
            host_handle="@demohost.vn",
            title="Flash sale skincare cuối tuần",
            status=StreamStatus.LIVE,
            started_at=start,
        )
        db.add(stream)
        await db.flush()

        db.add_all(
            [StreamProduct(stream_id=stream.id, product_id=p.id, display_order=i) for i, p in enumerate(products)]
        )

        # 60 minutes of plausible curve: ramp up viewers, periodic GMV spikes when featuring
        for m in range(60):
            bucket = start + timedelta(minutes=m)
            viewers = int(200 + 800 * (1 - abs(m - 30) / 30) + rng.gauss(0, 30))
            featured = products[m // 15 % len(products)]
            click_rate = 0.03 + rng.uniform(-0.01, 0.02)
            order_rate = 0.10 + rng.uniform(-0.03, 0.05)
            clicks = max(0, int(viewers * click_rate))
            carts = int(clicks * 0.45)
            orders = max(0, int(carts * order_rate * 4))
            db.add(
                StreamMinute(
                    stream_id=stream.id,
                    bucket_ts=bucket,
                    concurrent_viewers=viewers,
                    new_viewers=int(viewers * 0.15),
                    comments=int(viewers * 0.04),
                    likes=int(viewers * 0.20),
                    product_clicks=clicks,
                    add_to_carts=carts,
                    orders=orders,
                    gmv_vnd=Decimal(orders) * featured.price_vnd,
                    featured_product_id=featured.id,
                )
            )
        await db.commit()
        print(f"Seeded stream {stream.id} with 60 minutes and {len(products)} products.")


if __name__ == "__main__":
    asyncio.run(main())
