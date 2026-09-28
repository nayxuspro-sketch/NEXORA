import base64
import io
from PIL import Image as PILImage
from reportlab.platypus import Image as RLImage, Paragraph, Table, TableStyle
from reportlab.lib import colors


def get_store_logo_flowable(logo_str, max_width=70, max_height=45):
    """
    Parses a base64 encoded image string or data URL, validates it via PIL,
    and returns a ReportLab Flowable RLImage object with preserved aspect ratio.
    Returns None if no logo is provided or if parsing fails.
    """
    if not logo_str or not isinstance(logo_str, str) or len(logo_str.strip()) < 20:
        return None

    raw_str = logo_str.strip()
    if 'base64,' in raw_str:
        raw_str = raw_str.split('base64,')[1]

    try:
        image_bytes = base64.b64decode(raw_str)
        pil_img = PILImage.open(io.BytesIO(image_bytes))
        orig_w, orig_h = pil_img.size

        if orig_w <= 0 or orig_h <= 0:
            return None

        # Calculate scaled dimensions preserving aspect ratio
        ratio = min(max_width / orig_w, max_height / orig_h)
        target_w = orig_w * ratio
        target_h = orig_h * ratio

        byte_stream = io.BytesIO(image_bytes)
        return RLImage(byte_stream, width=target_w, height=target_h)
    except Exception:
        return None


def create_header_with_logo(title_p, subtitle_p, logo_flowable, total_width=520):
    """
    Creates a clean header table embedding the Store Logo on the right or left
    and the title / subtitle paragraphs alongside it.
    """
    if not logo_flowable:
        return [title_p, subtitle_p]

    text_content = [title_p, subtitle_p]
    logo_col_w = logo_flowable.drawWidth + 15
    text_col_w = total_width - logo_col_w

    header_table = Table(
        [[text_content, logo_flowable]],
        colWidths=[text_col_w, logo_col_w]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return [header_table]
