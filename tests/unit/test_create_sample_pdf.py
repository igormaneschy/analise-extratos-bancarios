import sys
import os
import importlib


def make_fake_reportlab(tmp_dir):
    # Create fake submodules and objects used by scripts/create_sample_pdf.py
    pkg_names = [
        "reportlab",
        "reportlab.lib",
        "reportlab.lib.pagesizes",
        "reportlab.lib.colors",
        "reportlab.lib.units",
        "reportlab.platypus",
        "reportlab.lib.styles",
        "reportlab.lib.enums",
    ]

    for name in pkg_names:
        if name not in sys.modules:
            sys.modules[name] = type(sys)(name)

    # pagesizes.A4
    sys.modules["reportlab.lib.pagesizes"].A4 = (595.27, 841.89)

    # colors.HexColor -> return a simple string or tuple
    class Colors:
        @staticmethod
        def HexColor(val):
            return val
    sys.modules["reportlab.lib.colors"] = Colors()

    # units.mm
    sys.modules["reportlab.lib.units"].mm = 2.834645

    # platypus elements
    class SimpleDocTemplate:
        def __init__(self, filename, pagesize=None):
            self.filename = filename
            self.pagesize = pagesize

        def build(self, story):
            # write a minimal PDF-like file so existence checks pass
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            with open(self.filename, "wb") as f:
                f.write(b"%PDF-1.4\n%Fake PDF\n%%EOF")

    class Table:
        def __init__(self, data, colWidths=None):
            self.data = data
            self.colWidths = colWidths

        def setStyle(self, style):
            pass

    class TableStyle:
        def __init__(self, styles):
            self.styles = styles

    class Paragraph:
        def __init__(self, text, style=None):
            self.text = text
            self.style = style

    class Spacer:
        def __init__(self, a, b):
            pass

    platypus = sys.modules["reportlab.platypus"]
    platypus.SimpleDocTemplate = SimpleDocTemplate
    platypus.Table = Table
    platypus.TableStyle = TableStyle
    platypus.Paragraph = Paragraph
    platypus.Spacer = Spacer

    # styles
    def getSampleStyleSheet():
        return {
            'Heading1': {},
            'Heading2': {},
            'Heading3': {},
            'Normal': {}
        }

    class ParagraphStyle:
        def __init__(self, name, parent=None, fontSize=None, textColor=None, alignment=None):
            self.name = name
            self.parent = parent
            self.fontSize = fontSize
            self.textColor = textColor
            self.alignment = alignment

    styles_mod = sys.modules["reportlab.lib.styles"]
    styles_mod.getSampleStyleSheet = getSampleStyleSheet
    styles_mod.ParagraphStyle = ParagraphStyle

    # enums
    enums = sys.modules["reportlab.lib.enums"]
    enums.TA_CENTER = 1
    enums.TA_RIGHT = 2


def test_create_sample_statement_creates_file(tmp_path, monkeypatch):
    # Ensure our fake reportlab is in place before importing the script
    make_fake_reportlab(tmp_path)

    # Import the module after faking dependencies
    import importlib
    create_sample_pdf = importlib.import_module("scripts.create_sample_pdf")

    # change cwd to a temporary directory to isolate file creation
    monkeypatch.chdir(tmp_path)

    filename = create_sample_pdf.create_sample_statement()

    assert os.path.exists(filename)
    assert filename.endswith("extrato_exemplo.pdf")

    # cleanup
    os.remove(filename)
