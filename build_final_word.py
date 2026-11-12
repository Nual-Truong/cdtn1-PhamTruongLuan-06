from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

# ==================================================
# 1. CAU HINH FILE
# ==================================================

source = Path("BT3_2374802010296_PhamTruongLuan_FINAL.docx")
output = Path("BT3_2374802010296_PhamTruongLuan.docx")
image_dir = Path("docs/screenshots")

if not source.exists():
    raise FileNotFoundError(f"Khong tim thay file: {source}")

# Chi lay bo anh verified_PASS
images = sorted(image_dir.glob("verified_PASS_*.png"))

if len(images) != 17:
    raise RuntimeError(
        f"Can dung 17 anh verified_PASS_*.png, "
        f"nhung tim thay {len(images)} anh."
    )

tc_images = [p for p in images if "_TC-" in p.name]
other_images = [p for p in images if "_TC-" not in p.name]

if len(tc_images) != 12 or len(other_images) != 5:
    raise RuntimeError(
        f"Bo anh khong dung cau truc: "
        f"{len(other_images)} anh tong hop, {len(tc_images)} anh TC."
    )

doc = Document(str(source))

if len(doc.tables) != 12:
    raise RuntimeError(
        f"So bang khong dung: {len(doc.tables)}, mong doi 12."
    )

print("PASS: Da mo ban FINAL")
print("PASS: 12 bang duoc giu nguyen")
print("PASS: Tim thay 17 anh verified_PASS")

# ==================================================
# 2. CHUAN HOA FONT
# ==================================================

def set_run_font(run, size=None, bold=None):
    run.font.name = "Times New Roman"

    if size is not None:
        run.font.size = Pt(size)

    if bold is not None:
        run.bold = bold

    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.rFonts

    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)

    rfonts.set(qn("w:ascii"), "Times New Roman")
    rfonts.set(qn("w:hAnsi"), "Times New Roman")
    rfonts.set(qn("w:eastAsia"), "Times New Roman")
    rfonts.set(qn("w:cs"), "Times New Roman")


normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(11)

heading_settings = {
    "Heading 1": 14,
    "Heading 2": 12,
    "Heading 3": 11,
}

for name, size in heading_settings.items():
    style = doc.styles[name]
    style.font.name = "Times New Roman"
    style.font.size = Pt(size)
    style.font.bold = True

    rpr = style._element.get_or_add_rPr()
    rfonts = rpr.rFonts

    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)

    for attr in ["ascii", "hAnsi", "eastAsia", "cs"]:
        rfonts.set(qn(f"w:{attr}"), "Times New Roman")

# Chuan hoa cac run trong paragraph va table
for paragraph in doc.paragraphs:
    for run in paragraph.runs:
        set_run_font(run)

for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    set_run_font(run)

# ==================================================
# 3. CAN LE TRANG
# ==================================================

for section in doc.sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.8)

# ==================================================
# 4. FOOTER DANH SO TRANG
# ==================================================

def add_field(run, instruction):
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    begin.set(qn("w:dirty"), "true")

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {instruction} "

    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")

    result = OxmlElement("w:t")
    result.text = "1"

    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")

    run._r.append(begin)
    run._r.append(instr)
    run._r.append(separate)
    run._r.append(result)
    run._r.append(end)


for section in doc.sections:
    footer = section.footer

    # Xoa noi dung footer cu
    for p in list(footer.paragraphs):
        p._element.getparent().remove(p._element)

    fp = footer.add_paragraph()
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    r = fp.add_run(
        "Báo cáo Bài tập 3 – Smart CRM Mekong Mobile | Trang "
    )
    set_run_font(r, 9.5)

    page_run = fp.add_run()
    set_run_font(page_run, 9.5)
    add_field(page_run, "PAGE")

# ==================================================
# 5. HAM CHEN PARAGRAPH TRUOC MOT VI TRI
# ==================================================

def insert_paragraph_before(anchor, text="", style=None):
    # Tao paragraph bang Document de giu lien ket voi document.part
    paragraph = doc.add_paragraph()

    # Di chuyen paragraph den truoc vi tri can chen
    anchor.addprevious(paragraph._p)

    if style:
        paragraph.style = style

    if text:
        run = paragraph.add_run(text)
        set_run_font(run)

    return paragraph


# ==================================================
# 6. CHEN MUC LUC TU DONG
# ==================================================

# Tim heading MUC 0
first_heading = None

for p in doc.paragraphs:
    if p.text.strip().startswith("MỤC 0."):
        first_heading = p
        break

if first_heading is None:
    raise RuntimeError("Khong tim thay Heading MUC 0.")

# Khong chen trung neu da co TOC
if "TOC" not in doc._element.body.xml:

    toc_title = insert_paragraph_before(
        first_heading._p,
        "MỤC LỤC"
    )
    for run in toc_title.runs:
        set_run_font(run, 16, True)

    toc_title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    toc_p = insert_paragraph_before(first_heading._p)
    toc_run = toc_p.add_run()
    set_run_font(toc_run, 11)

    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    begin.set(qn("w:dirty"), "true")

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = ' TOC \\o "1-3" \\h \\z \\u '

    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")

    placeholder = OxmlElement("w:t")
    placeholder.text = (
        "Mục lục sẽ được cập nhật khi mở file bằng Microsoft Word."
    )

    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")

    for element in [begin, instr, separate, placeholder, end]:
        toc_run._r.append(element)

    # Ngat trang truoc MUC 0
    page_break_p = insert_paragraph_before(first_heading._p)
    page_break_p.add_run().add_break()

    print("PASS: Da chen truong Muc luc tu dong")
else:
    print("INFO: Da co truong TOC, khong chen lai")

# ==================================================
# 7. THAY THE RIENG NOI DUNG MUC 7
# ==================================================

paragraphs = doc.paragraphs

section_heading = next(
    (p for p in paragraphs
     if p.text.strip().startswith("MỤC 7.")),
    None
)

appendix_heading = next(
    (p for p in paragraphs
     if p.text.strip().startswith("PHỤ LỤC")),
    None
)

if section_heading is None or appendix_heading is None:
    raise RuntimeError(
        "Khong tim thay MUC 7 hoac PHU LUC AI."
    )

# Tim doan gioi thieu ngay sau Heading MUC 7
paragraphs = doc.paragraphs
heading_index = next(
    i for i, p in enumerate(paragraphs)
    if p._p is section_heading._p
)

if heading_index + 1 >= len(paragraphs):
    raise RuntimeError("Khong tim thay doan gioi thieu MUC 7.")

intro = paragraphs[heading_index + 1]

# Doi ten MUC 7 cho phu hop voi nguon minh chung
section_heading.text = (
    "MỤC 7. HÌNH ẢNH MINH CHỨNG KẾT QUẢ KIỂM THỬ "
    "VÀ KIỂM TRA BẢO MẬT"
)

intro.text = (
    "Bộ hình ảnh dưới đây tổng hợp kết quả kiểm thử gồm 12 Test Cases, "
    "các kiểm tra liên quan đến HMAC-SHA256, cấu hình môi trường, "
    "log và kết quả chạy pytest. Tên tệp được giữ nguyên để thuận tiện "
    "đối chiếu với thư mục docs/screenshots trong repository."
)

# Xoa tat ca noi dung cu giua intro va Phu luc
node = intro._p.getnext()

while node is not None and node is not appendix_heading._p:
    next_node = node.getnext()
    node.getparent().remove(node)
    node = next_node

if node is None:
    raise RuntimeError("Khong the xac dinh ranh gioi truoc Phu luc.")

# ==================================================
# 8. CHEN 17 ANH PASS MOI
# ==================================================

for img_path in images:

    caption = insert_paragraph_before(
        appendix_heading._p,
        f"Hình minh chứng: {img_path.name}"
    )

    caption.paragraph_format.space_before = Pt(8)
    caption.paragraph_format.space_after = Pt(4)

    for run in caption.runs:
        set_run_font(run, 10, True)

    image_paragraph = insert_paragraph_before(
        appendix_heading._p
    )
    image_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = image_paragraph.add_run()
    run.add_picture(str(img_path), width=Inches(6.0))

    image_paragraph.paragraph_format.space_after = Pt(8)

# Ngat trang truoc Phu luc AI
appendix_break = insert_paragraph_before(
    appendix_heading._p
)
appendix_break.add_run().add_break()

print("PASS: Da thay the 29 anh cu bang 17 anh verified_PASS")

# ==================================================
# 9. BAT WORD CAP NHAT FIELD KHI MO FILE
# ==================================================

settings = doc.settings._element

update_fields = settings.find(qn("w:updateFields"))

if update_fields is None:
    update_fields = OxmlElement("w:updateFields")
    settings.append(update_fields)

update_fields.set(qn("w:val"), "true")

# ==================================================
# 10. LUU FILE MOI
# ==================================================

doc.save(str(output))

# ==================================================
# 11. DOC LAI VA KIEM TRA
# ==================================================

check = Document(str(output))

image_count = len(check.inline_shapes)
table_count = len(check.tables)

toc_exists = "TOC" in check._element.body.xml

page_field_exists = any(
    "PAGE" in section.footer._element.xml
    for section in check.sections
)

heading_names = [
    "Normal", "Heading 1", "Heading 2", "Heading 3"
]

print("\n========== KIEM TRA FILE WORD MOI ==========")
print("File:", output.name)
print("Dung luong:", f"{output.stat().st_size:,}", "bytes")
print("Paragraph:", len(check.paragraphs))
print("Tables:", table_count)
print("Images:", image_count)
print("Sections:", len(check.sections))
print("TOC field:", toc_exists)
print("PAGE field:", page_field_exists)

print("\n========== KIEM TRA FONT ==========")
for name in heading_names:
    style = check.styles[name]
    print(
        name,
        "| Font:", style.font.name,
        "| Size:",
        style.font.size.pt if style.font.size else None
    )

print("\n========== KIEM TRA MUC 7 ==========")
for p in check.paragraphs:
    if p.text.startswith("Hình minh chứng:"):
        print(p.text)

print("\n========== KET LUAN ==========")

if (
    table_count == 12
    and image_count == 17
    and toc_exists
    and page_field_exists
):
    print("PASS: Word moi da qua kiem tra co ban.")
else:
    print("CAN KIEM TRA LAI: Mot so dieu kien chua dat.")
    raise RuntimeError("Kiem tra DOCX that bai.")

print("\nFile FINAL goc duoc giu nguyen.")
