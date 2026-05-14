"""
Vietnamese dialect prompt building blocks for TikTok livestream scripts.

The model is told to write in Vietnamese — not translated English. Each dialect
gets a style guide grounded in lexical markers actually used by hosts in the
respective region. These are conservative defaults; tune from observed
top-converter scripts as the dataset grows.
"""

from __future__ import annotations

from app.models.script import Dialect, ScriptIntent

SYSTEM_PROMPT = """Bạn là copywriter livestream cho TikTok Shop Việt Nam. \
Bạn viết kịch bản tiếng Việt tự nhiên, ngắn gọn, dễ nói thành lời. \
Không dịch máy từ tiếng Anh. Không dùng từ Hán Việt cứng. \
Tuân thủ chuẩn nội dung TikTok Shop VN: không phóng đại y tế, không cam đoan \
hiệu quả tuyệt đối, không nói xấu đối thủ, không kêu gọi rời nền tảng."""


DIALECT_STYLE: dict[Dialect, str] = {
    Dialect.NORTH: (
        "Giọng Bắc (Hà Nội). Lịch sự vừa phải, kết câu bằng 'ạ', 'nhé', 'vâng'. "
        "Tránh từ địa phương miền Nam như 'nha', 'nè', 'dạ'. "
        "Xưng hô: 'mình', 'các bạn', 'cô chú', 'anh chị'. "
        "Nhịp câu gọn, ít từ đệm, ít kéo dài nguyên âm. "
        'Ví dụ giọng: "Các bạn ơi mình giới thiệu món này nhé", '
        '"Sản phẩm này nhà mình bán chạy nhất tuần ạ".'
    ),
    Dialect.SOUTH: (
        "Giọng Nam (Sài Gòn / TP.HCM). Thân mật, ấm áp, kết câu bằng 'nha', 'nè', 'á'. "
        "Dùng 'dạ' đầu câu khi đáp lại bình luận. "
        "Xưng hô: 'mình', 'cả nhà', 'mấy chế', 'em', 'chị'. "
        "Nhịp câu thoải mái hơn miền Bắc, được phép kéo dài 'lắmmm', 'xịnnn'. "
        'Ví dụ giọng: "Cả nhà ơi món này xịn lắm nha", '
        '"Mình test rồi nè, ưng cực luôn á".'
    ),
    Dialect.NEUTRAL: (
        "Giọng trung tính, không nghiêng Bắc hay Nam. "
        "Tránh các từ kết câu đặc trưng vùng miền ('ạ', 'nha', 'nè'). "
        "Xưng hô an toàn: 'mình', 'các bạn'."
    ),
}


INTENT_BRIEF: dict[ScriptIntent, str] = {
    ScriptIntent.HOOK: (
        "MỞ ĐẦU (HOOK). Mục tiêu: trong 5–10 giây đầu khiến người mới vào dừng xem. "
        "Cách làm: đặt câu hỏi gây tò mò, đưa con số sốc, hoặc nêu pain-point cụ thể. "
        "Không tự giới thiệu dài dòng. Không liệt kê tính năng vội."
    ),
    ScriptIntent.PITCH: (
        "GIỚI THIỆU SẢN PHẨM (PITCH). Mục tiêu: nói rõ 2–3 lợi ích chính theo logic "
        "vấn đề → cách giải quyết → bằng chứng. Tránh kê khai tính năng kỹ thuật. "
        "Một câu một ý, dễ nói thành tiếng."
    ),
    ScriptIntent.SOCIAL_PROOF: (
        "BẰNG CHỨNG XÃ HỘI (SOCIAL PROOF). Mục tiêu: tạo niềm tin bằng review thật, "
        "số đơn đã bán, người nổi tiếng dùng. Không bịa con số. "
        "Dùng cụm: 'shop đã bán hơn ...', 'review 5 sao của bạn ...', 'khách quay lại lần X'."
    ),
    ScriptIntent.OBJECTION: (
        "XỬ LÝ TỪ CHỐI (OBJECTION). Mục tiêu: trả lời 1 lo lắng cụ thể (giá, chất lượng, "
        "ship, đổi trả). Cấu trúc: thừa nhận → giải thích → cam kết rõ ràng."
    ),
    ScriptIntent.URGENCY: (
        "TẠO KHẨN CẤP (URGENCY). Mục tiêu: thúc đẩy ra quyết định ngay. "
        "Chỉ dùng yếu tố CÓ THẬT: số lượng còn lại, thời hạn flash sale, voucher hết hạn. "
        "TUYỆT ĐỐI không bịa khan hiếm giả."
    ),
    ScriptIntent.CLOSE: (
        "CHỐT ĐƠN (CLOSE). Mục tiêu: hướng dẫn cụ thể bấm giỏ vàng số mấy, "
        "cách dùng voucher, cách hỏi tư vấn. Một câu kêu gọi hành động cuối."
    ),
}


def build_user_prompt(
    *,
    dialect: Dialect,
    intent: ScriptIntent,
    product_name: str | None,
    product_category: str | None,
    price_band: str | None,
    audience_persona: str | None,
    target_duration_sec: int,
    n_variants: int,
) -> str:
    parts: list[str] = []
    parts.append(f"## Phong cách\n{DIALECT_STYLE[dialect]}")
    parts.append(f"## Mục đích đoạn này\n{INTENT_BRIEF[intent]}")

    ctx_lines: list[str] = []
    if product_name:
        ctx_lines.append(f"- Sản phẩm: {product_name}")
    if product_category:
        ctx_lines.append(f"- Ngành hàng: {product_category}")
    if price_band:
        ctx_lines.append(f"- Phân khúc giá: {price_band}")
    if audience_persona:
        ctx_lines.append(f"- Khách mục tiêu: {audience_persona}")
    if ctx_lines:
        parts.append("## Bối cảnh\n" + "\n".join(ctx_lines))

    words_target = max(20, int(target_duration_sec * 2.5))  # ~150 wpm Vietnamese
    parts.append(
        f"## Yêu cầu\n"
        f"- Viết {n_variants} biến thể (variant) khác nhau về cách tiếp cận.\n"
        f"- Mỗi biến thể dài khoảng {words_target} từ, đọc trong ~{target_duration_sec} giây.\n"
        f"- Mỗi biến thể có một tiêu đề ngắn (5–8 từ) và nội dung kịch bản.\n"
        f"- Mỗi biến thể kèm 2–4 tag mô tả phong cách (ví dụ: 'tò mò', 'số liệu', 'cảm xúc').\n"
        f"- Trả về JSON đúng schema, không thêm văn bản ngoài JSON."
    )
    parts.append(
        '## Định dạng đầu ra (JSON)\n'
        '{\n'
        '  "variants": [\n'
        '    {\n'
        '      "title": "...",\n'
        '      "body": "...",\n'
        '      "estimated_duration_sec": 30,\n'
        '      "tags": ["...", "..."]\n'
        '    }\n'
        '  ]\n'
        '}'
    )
    return "\n\n".join(parts)
