from src.file_management import GUIDE_TEXT_FILE, load_markdown_from_file
from src.util_streamlit import render_enriched_markdown

GUIDE_TEXT = load_markdown_from_file(GUIDE_TEXT_FILE)

render_enriched_markdown(GUIDE_TEXT)
