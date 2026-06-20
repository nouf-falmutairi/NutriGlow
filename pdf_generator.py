"""
pdf_generator.py
-----------------
Builds the downloadable PDF for the Meal Plan view, in either English
(left-to-right) or Arabic (right-to-left, reshaped) using ReportLab.
"""

from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Enforced Arabic shaping libraries
import arabic_reshaper
from bidi.algorithm import get_display

# Reshaper configuration to avoid missing glyph boxes (tofu) in standard fonts
arabic_config = {
    'delete_harakat': True,
    'support_ligatures': False, 
}
reshaper = arabic_reshaper.ArabicReshaper(arabic_config)

FONTS_DIR = Path(__file__).parent / "static" / "fonts"

# IMPORTANT: Using Amiri instead of Cairo for full ReportLab presentation form support
ARABIC_FONT_REGULAR = FONTS_DIR / "Amiri-Regular.ttf"
ARABIC_FONT_BOLD = FONTS_DIR / "Amiri-Bold.ttf"

ARABIC_VALUE_LABELS = {
    # Diet options
    "Balanced": "متوازن",
    "High Protein": "عالي البروتين",
    "Low Carb": "قليل الكربوهيدرات",
    # Lifestyle options
    "Office job": "وظيفة مكتبية",
    "Stay at Home": "في المنزل",
    "Student": "طالب/ة",
    "Work from Home": "العمل من المنزل",
    # Gender
    "Male": "ذكر",
    "Female": "أنثى",
    # Starting day
    "Sunday": "الأحد",
    "Monday": "الإثنين",
}

def _localize_value(value: str, is_arabic: bool) -> str:
    """Translate a Diet/Lifestyle/Gender/Day value for Arabic PDF display only."""
    if is_arabic and value in ARABIC_VALUE_LABELS:
        return ARABIC_VALUE_LABELS[value]
    return value

_FONT_REGULAR_NAME = "Helvetica"
_FONT_BOLD_NAME = "Helvetica-Bold"
_ARABIC_FONT_READY = False

def _ensure_fonts_registered() -> None:
    """Register the Amiri Arabic-capable font with ReportLab."""
    global _FONT_REGULAR_NAME, _FONT_BOLD_NAME, _ARABIC_FONT_READY

    if _ARABIC_FONT_READY:
        return

    fonts_ready = ARABIC_FONT_REGULAR.exists() and ARABIC_FONT_BOLD.exists()

    if fonts_ready:
        pdfmetrics.registerFont(TTFont("Amiri", str(ARABIC_FONT_REGULAR)))
        pdfmetrics.registerFont(TTFont("Amiri-Bold", str(ARABIC_FONT_BOLD)))
        _FONT_REGULAR_NAME = "Amiri"
        _FONT_BOLD_NAME = "Amiri-Bold"
        _ARABIC_FONT_READY = True
    else:
        # Stop execution and warn clearly if the fonts are missing
        raise FileNotFoundError(
            f"Arabic fonts not found in {FONTS_DIR}. Please download Amiri-Regular.ttf "
            "and Amiri-Bold.ttf and place them in the correct directory."
        )

def _shape_if_arabic(text: str, is_arabic: bool) -> str:
    """Reshape + bidi-reorder Arabic text for correct PDF rendering."""
    if not is_arabic or not text:
        return str(text)
    
    # 1. Reshape using our strict configuration
    reshaped = reshaper.reshape(str(text))
    
    # 2. Reorder for RTL drawing, forcing base direction to RTL ('R')
    return get_display(reshaped, base_dir='R')

def generate_meal_plan_pdf(plan_data: dict, language: str) -> BytesIO:
    """Build the Meal Plan PDF and return it as an in-memory BytesIO buffer."""
    _ensure_fonts_registered()
    is_arabic = language == "ar"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
    )

    align = TA_RIGHT if is_arabic else TA_LEFT
    font_regular = _FONT_REGULAR_NAME if is_arabic else "Helvetica"
    font_bold = _FONT_BOLD_NAME if is_arabic else "Helvetica-Bold"

    brand_color = colors.HexColor("#2F5233")
    accent_color = colors.HexColor("#E8744C")
    muted_color = colors.HexColor("#6B6F6A")

    title_style = ParagraphStyle(
        "Title",
        fontName=font_bold,
        fontSize=22,
        leading=26,
        textColor=brand_color,
        alignment=align,
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontName=font_regular,
        fontSize=11,
        leading=15,
        textColor=muted_color,
        alignment=align,
        spaceAfter=14,
    )
    day_heading_style = ParagraphStyle(
        "DayHeading",
        fontName=font_bold,
        fontSize=14,
        leading=18,
        textColor=colors.white,
        alignment=align,
    )
    meal_type_style = ParagraphStyle(
        "MealType",
        fontName=font_bold,
        fontSize=10.5,
        leading=14,
        textColor=accent_color,
        alignment=align,
    )
    meal_name_style = ParagraphStyle(
        "MealName",
        fontName=font_bold,
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#1F2421"),
        alignment=align,
    )
    meal_meta_style = ParagraphStyle(
        "MealMeta",
        fontName=font_regular,
        fontSize=9,
        leading=13,
        textColor=muted_color,
        alignment=align,
    )

    def T(text: str) -> str:
        return _shape_if_arabic(text, is_arabic)

    labels = {
        "en": {
            "app_name": "NutriGlow",
            "subtitle": "Your personalized 5-day meal plan",
            "diet": "Diet",
            "lifestyle": "Lifestyle",
            "gender": "Gender",
            "starting": "Starting",
        },
        "ar": {
            "app_name": "نوتري جلو",
            "subtitle": "خطة وجباتك الأسبوعية المخصصة لمدة 5 أيام",
            "diet": "النظام الغذائي",
            "lifestyle": "نمط الحياة",
            "gender": "الجنس",
            "starting": "بداية الأسبوع",
        },
    }
    lbl = labels["ar" if is_arabic else "en"]

    story = []
    story.append(Paragraph(T(lbl["app_name"]), title_style))
    story.append(Paragraph(T(lbl["subtitle"]), subtitle_style))

    meta_line = (
        f"{lbl['diet']}: {_localize_value(plan_data.get('diet',''), is_arabic)}  |  "
        f"{lbl['lifestyle']}: {_localize_value(plan_data.get('lifestyle',''), is_arabic)}  |  "
        f"{lbl['gender']}: {_localize_value(plan_data.get('gender',''), is_arabic)}  |  "
        f"{lbl['starting']}: {_localize_value(plan_data.get('starting_day',''), is_arabic)}"
    )
    story.append(Paragraph(T(meta_line), meal_meta_style))
    story.append(Spacer(1, 10))
    story.append(
        HRFlowable(width="100%", color=colors.HexColor("#E8E4DC"), thickness=1)
    )
    story.append(Spacer(1, 10))

    for day in plan_data.get("days", []):
        day_label = day.get("day_label", day.get("day_name", ""))
        heading_table = Table(
            [[Paragraph(T(day_label), day_heading_style)]], colWidths=[doc.width]
        )
        heading_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), brand_color),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    (
                        "LEFTPADDING" if not is_arabic else "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        12,
                    ),
                    ("ROUNDEDCORNERS", (0, 0), (-1, -1), [6, 6, 6, 6]),
                ]
            )
        )
        story.append(heading_table)
        story.append(Spacer(1, 6))

        meals = day.get("meals", {})
        ordered_types = [
            mt for mt in ["Breakfast", "Lunch", "Dinner"] if mt in meals
        ]
        rows = []
        for meal_type in ordered_types:
            meal = meals[meal_type]
            type_label = meal.get("meal_type_label", meal_type)
            name = meal.get("Name", "")
            calories = meal.get("Calories", "")
            macros = meal.get("Macros", "").replace("\n", "  |  ")

            cell = [
                Paragraph(T(type_label), meal_type_style),
                Paragraph(T(name), meal_name_style),
                Paragraph(T(f"{calories}    {macros}"), meal_meta_style),
            ]
            rows.append([cell])

        meals_table = Table(rows, colWidths=[doc.width])
        meals_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF9F6")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E8E4DC")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E8E4DC")),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story.append(meals_table)
        story.append(Spacer(1, 14))

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_shopping_list_pdf(shopping_list: list[dict], language: str) -> BytesIO:
    """Build the Shopping List PDF as an in-memory BytesIO buffer."""
    _ensure_fonts_registered()
    is_arabic = language == "ar"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
    )

    align = TA_RIGHT if is_arabic else TA_LEFT
    font_regular = _FONT_REGULAR_NAME if is_arabic else "Helvetica"
    font_bold = _FONT_BOLD_NAME if is_arabic else "Helvetica-Bold"
    brand_color = colors.HexColor("#2F5233")
    muted_color = colors.HexColor("#6B6F6A")

    def T(text: str) -> str:
        return _shape_if_arabic(text, is_arabic)

    title_style = ParagraphStyle(
        "Title",
        fontName=font_bold,
        fontSize=22,
        leading=26,
        textColor=brand_color,
        alignment=align,
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontName=font_regular,
        fontSize=11,
        leading=15,
        textColor=muted_color,
        alignment=align,
        spaceAfter=16,
    )
    item_style = ParagraphStyle(
        "Item",
        fontName=font_regular,
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#1F2421"),
        alignment=align,
    )
    qty_style = ParagraphStyle(
        "Qty",
        fontName=font_bold,
        fontSize=11,
        leading=16,
        textColor=brand_color,
        alignment=TA_CENTER,
    )

    titles = {
        "en": ("NutriGlow", "Your consolidated shopping list"),
        "ar": ("نوتري جلو", "قائمة التسوق المجمعة لأسبوعك"),
    }
    title_text, subtitle_text = titles["ar" if is_arabic else "en"]

    story = [
        Paragraph(T(title_text), title_style),
        Paragraph(T(subtitle_text), subtitle_style),
    ]

    rows = []
    for entry in shopping_list:
        display_item = entry.get("item_ar") if is_arabic and entry.get("item_ar") else entry["item"]
        item_cell = Paragraph(T(display_item.capitalize()), item_style)
        qty_cell = Paragraph(T(str(entry["quantity"])), qty_style)
        
        if is_arabic:
            rows.append([item_cell, qty_cell])
        else:
            rows.append([qty_cell, item_cell])

    col_widths = [25 * mm, doc.width - 25 * mm]
    if is_arabic:
        col_widths = [doc.width - 25 * mm, 25 * mm]

    table = Table(rows, colWidths=col_widths)
    style_commands = [
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E8E4DC")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#F1EEE7")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#FBF9F6")]),
    ]
    table.setStyle(TableStyle(style_commands))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer