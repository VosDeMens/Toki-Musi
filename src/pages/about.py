from src.file_management import ABOUT_TEXT_FILE, load_markdown_from_file
from src.util_streamlit import render_enriched_markdown

ABOUT_TEXT = load_markdown_from_file(ABOUT_TEXT_FILE)

render_enriched_markdown(ABOUT_TEXT)
