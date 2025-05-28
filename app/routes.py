import tempfile
import re
from urllib.parse import urlparse

import gradio as gr

from . import api, utils


def process_query(topic, temp, context, count):
    topic = topic.strip()
    if not topic:
        return "❗ Please enter a research topic.", "", "", ""

    # 1) Fetch report
    res = api.get_structured_report(topic, temp, context)
    if "report" not in res:
        return f"**Error:** {res.get('error', 'Unknown')}", "", "", ""

    report, refs, chain = res["report"], res["references"], res["chain"]

    # 2) Link inline citations
    def link_cite(m):
        n = m.group(1)
        for num, url in refs:
            if str(num) == n:
                return f"[{n}]({url})"
        return f"[{n}]"
    report_md = re.sub(r"\[(\d+)\]", link_cite, report)

    # 3) Further Reading (list of tuples)
    sources = api.get_search_sources(topic, count)
    if sources:
        report_md += "\n\n### 📚 Further Reading\n"
        for title, url in sources:
            report_md += f"- [{title}]({url})\n"

    # 4) References panel
    refs_md = "### 🔗 References\n"
    for num, url in refs:
        domain = urlparse(url).netloc.replace("www.", "")
        refs_md += f"{num}. [{domain}]({url})\n"

    # 5) Chain-of-Thought
    chain_md = chain or "_No reasoning available._"

    # 6) Avg. rating
    avg = utils.get_average_rating(topic)
    avg_md = f"**Average Rating:** {avg}★" if avg else "No ratings yet."

    return report_md, refs_md, chain_md, avg_md

def export_md(report_md, refs_md):
    combined = report_md + "\n\n" + refs_md
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".md", mode="w", encoding="utf-8")
    tmp.write(combined)
    tmp.close()
    return tmp.name


def submit_feedback(topic, rating, comment):
    if topic.strip() and rating:
        utils.save_feedback(topic, rating, comment)
        avg = utils.get_average_rating(topic)
        return f"✅ Thanks! New avg. rating: {avg}★"
    return "⚠️ Cannot save feedback."


def create_interface():
    theme = gr.themes.Soft(primary_hue="purple")
    css = """
    .gradio-container { max-width: 1200px; margin: auto; }
    .input-column { padding: 1rem; border: 1px solid #444; border-radius: 8px; }
    .output-column { padding: 1rem; border: 1px solid #444; border-radius: 8px; }
    """

    with gr.Blocks(theme=theme, css=css) as demo:
        # Header
        gr.Markdown("<h1 style='margin-bottom:0.5rem;'>🔍 DeepDive Scholar</h1>", elem_id="header")

        # Main area
        with gr.Row():
            with gr.Column(scale=3, min_width=300, elem_classes="input-column"):
                gr.Markdown("### ⚙️ Inputs")
                topic = gr.Textbox(label="Research Topic", placeholder="e.g. CRISPR ethics", lines=1)
                temp = gr.Slider(0.0, 1.0, value=0.2, step=0.1, label="Creativity (temperature)")
                context = gr.Textbox(label="Additional Context (optional)", lines=4, placeholder="Paste notes…")
                count = gr.Slider(1, 5, value=3, step=1, label="# Further Reading Links")
                dive = gr.Button("🚀 Deep Dive", variant="primary")

            with gr.Column(scale=7, min_width=700, elem_classes="output-column"):
                gr.Markdown("### 📝 Research Report")
                report_md = gr.Markdown("⏳ Waiting for input...")
                with gr.Accordion("Show Reasoning", open=False):
                    chain_md = gr.Markdown()
                refs_md = gr.Markdown(label="References")
                avg_md = gr.Markdown()

        # Export & Feedback
        with gr.Row():
            export_btn = gr.Button("📥 Download Markdown", variant="secondary")
            rating = gr.Slider(1, 5, value=5, step=1, label="Rate this Report")
            comment = gr.Textbox(label="Your Feedback (optional)", lines=2)
            feedback_btn = gr.Button("⭐ Submit Feedback", variant="secondary")
            feedback_out = gr.Markdown()

        # **Chained callbacks** for loading placeholder + real call
        loading = dive.click(
            fn=lambda: ("⏳ Generating answer…", "", "", ""),
            inputs=[],
            outputs=[report_md, refs_md, chain_md, avg_md]
        )
        loading.then(
            fn=process_query,
            inputs=[topic, temp, context, count],
            outputs=[report_md, refs_md, chain_md, avg_md]
        )

        export_btn.click(fn=export_md, inputs=[report_md, refs_md], outputs=gr.File())
        feedback_btn.click(fn=submit_feedback, inputs=[topic, rating, comment], outputs=feedback_out)

    return demo
