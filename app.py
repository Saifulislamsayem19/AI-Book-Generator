import os
import time
import openai
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn
import io
from fpdf import FPDF
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure OpenAI API client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Improved story generation function with better title handling
def generate_story(title, description, num_chapters):
    story = {"title": title, "chapters": []}
    
    # Generate a better title if the provided one is too simple
    if len(title.split()) < 3:
        title_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative book title generator."},
                {"role": "user", "content": f"Generate an engaging, professional-sounding book title based on this concept: '{title} - {description}'. Return ONLY the title, no additional text."}
            ],
            temperature=0.7,
            max_tokens=50
        )
        improved_title = title_response.choices[0].message.content.strip().strip('"')
        # Only use the improved title if it's valid and not too long
        if improved_title and len(improved_title) <= 100:
            story["original_title"] = title
            title = improved_title
    
    story["title"] = title
    
    # Generate subtitle
    subtitle_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert at creating compelling book subtitles."},
            {"role": "user", "content": f"Create a short, engaging subtitle for a book titled '{title}' with this description: '{description}'. Return ONLY the subtitle, no additional text."}
        ],
        temperature=0.7,
        max_tokens=50
    )
    
    subtitle = subtitle_response.choices[0].message.content.strip().strip('"')
    story["subtitle"] = subtitle
    
    # Generate a more detailed plot outline first
    plot_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": """You are a master storyteller with expertise in creative writing.
            Your task is to create detailed, engaging plots with well-developed characters, 
            compelling conflicts, and satisfying story arcs. Incorporate literary techniques
            and narrative structures that professional authors use."""},
            {"role": "user", "content": f"""Create a comprehensive plot outline for a story with title '{title}' 
            and description '{description}' that will span {num_chapters} chapters.
            
            For each chapter, provide:
            1. A compelling chapter title
            2. A detailed summary of key events (200-300 words)
            3. Character development points
            4. Setting details and atmosphere
            5. Any important plot revelations
            
            Ensure the story has:
            - A clear beginning, middle, and end structure
            - Rising action and proper pacing
            - A compelling central conflict
            - Character growth and development
            - Engaging dialogue opportunities
            - Thematic depth
            
            Make the story feel complete and satisfying across exactly {num_chapters} chapters."""}
        ],
        temperature=0.8,
        max_tokens=2000
    )
    
    plot_outline = plot_response.choices[0].message.content
    
    # Generate each chapter based on the enhanced plot outline
    for chapter_num in range(1, num_chapters + 1):
        chapter_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a professional novelist with expertise in creative writing.
                Create vivid, engaging chapters with rich descriptions, realistic dialogue, 
                and emotional depth. Use literary techniques like foreshadowing, metaphor, 
                and sensory details to bring your writing to life. Balance narration, description,
                and dialogue like a published author would."""},
                {"role": "user", "content": f"""Write chapter {chapter_num} of {num_chapters} for a story with title '{title}'
                and description '{description}'. 
                
                Use this plot outline as your guide: 
                
                {plot_outline}
                
                Guidelines for this chapter:
                1. Create a compelling chapter title that reflects the content
                2. Write 1000-1500 words of engaging content
                3. Include vivid sensory details and setting descriptions
                4. Write realistic, meaningful dialogue with proper formatting
                5. Show character emotions and development through actions and thoughts
                6. End the chapter in an engaging way that encourages continued reading
                
                Format the chapter with the chapter title at the top, followed by the well-formatted content.
                The chapter title should be creative and intriguing.
                Do not include "Chapter {chapter_num}" in your response as this will be added automatically."""}
            ],
            temperature=0.8,
            max_tokens=2000
        )
        
        chapter_content = chapter_response.choices[0].message.content
        
        # Extract chapter title from content (assuming it's the first line)
        chapter_lines = chapter_content.strip().split('\n')
        chapter_title = chapter_lines[0].replace('#', '').strip()
        
        # Clean up chapter title - remove any "Chapter X:" prefixes if they exist
        chapter_title = re.sub(r'^Chapter\s+\d+\s*:?\s*', '', chapter_title).strip()
        
        # If title is still empty or just punctuation, generate a new one
        if not chapter_title or not re.search(r'[a-zA-Z0-9]', chapter_title):
            title_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You create compelling chapter titles."},
                    {"role": "user", "content": f"Create an intriguing title for chapter {chapter_num} of '{title}'. The chapter is about: {chapter_lines[1:10]}. Return ONLY the title, no additional text."}
                ],
                temperature=0.7,
                max_tokens=20
            )
            chapter_title = title_response.choices[0].message.content.strip().strip('"')
        
        # Get the chapter body, skipping the title
        chapter_body = '\n'.join(chapter_lines[1:]).strip()
        
        story["chapters"].append({
            "number": chapter_num,
            "title": chapter_title,
            "content": chapter_body
        })
    
    return story

# Completely rebuilt PDF creation function with proper encoding and error handling
def create_pdf(story):
    try:
        class StoryPDF(FPDF):
            def __init__(self):
                super().__init__()
                self.set_auto_page_break(auto=True, margin=20)
                self.set_margins(25, 25, 25)
                self.set_title(story["title"])
                self.chapter_start = False
                self.add_font('Times', '', 'times.ttf', uni=True)
                self.add_font('Times', 'B', 'timesbd.ttf', uni=True)
                self.add_font('Times', 'I', 'timesi.ttf', uni=True)
                self.add_font('Times', 'BI', 'timesbi.ttf', uni=True)
                
            def header(self):
                if self.page_no() > 3:  # Skip cover, blurb and TOC
                    # Only add header if not the first page of a chapter
                    if not self.chapter_start:
                        self.set_font('Times', 'I', 10)
                        self.set_y(10)
                        # Alternate author/title placement for odd/even pages like real books
                        if self.page_no() % 2 == 0:  # Even page
                            self.cell(0, 10, story["title"], 0, 0, 'L')
                        else:  # Odd page
                            self.cell(0, 10, "AI Story Generator", 0, 0, 'R')
                    self.chapter_start = False
            
            def footer(self):
                if self.page_no() > 3:  # Skip cover, blurb and TOC
                    self.set_y(-15)
                    self.set_font('Times', 'I', 10)
                    # Center page numbers
                    self.cell(0, 10, f'{self.page_no() - 3}', 0, 0, 'C')
            
            # Add a drop cap function for first paragraph of chapters
            def add_drop_cap(self, text, drop_letter):
                # Add the first letter as a drop cap
                self.set_font('Times', 'B', 28)
                self.cell(15, 14, drop_letter, 0, 0, 'C')
                self.set_x(40)
                
                # Add the rest of the first paragraph
                self.set_font('Times', '', 12)
                self.multi_cell(0, 6, text[1:])
        
        # Initialize PDF with better error handling for font files
        pdf = None
        try:
            pdf = StoryPDF()
        except Exception as font_error:
            # Fallback if custom fonts fail to load
            logging.warning(f"Custom font loading failed: {str(font_error)}. Using standard fonts.")
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=20)
            pdf.set_margins(25, 25, 25)
            pdf.set_title(story["title"])
        
        # Clean title function to remove markdown and prefixes
        def clean_title(title):
            # Remove markdown formatting (**, #, Title:, etc.)
            cleaned = re.sub(r'\*\*|\*|#', '', title)
            cleaned = re.sub(r'^Title:\s*', '', cleaned)
            cleaned = re.sub(r'^Chapter\s*\d+\s*:?\s*', '', cleaned)
            return cleaned.strip()
        
        # Function to sanitize text for PDF (replace unsupported characters)
        def sanitize_for_pdf(text):
            # Replace em dashes and other problematic characters
            replacements = {
                '\u2014': '-',  # em dash
                '\u2013': '-',  # en dash
                '\u2018': "'",  # left single quote
                '\u2019': "'",  # right single quote
                '\u201C': '"',  # left double quote
                '\u201D': '"',  # right double quote
                '\u2026': '...', # ellipsis
                '\u00A0': ' '   # non-breaking space
            }
            
            for char, replacement in replacements.items():
                text = text.replace(char, replacement)
                
            return text
        
        # Add cover page with professional book design
        pdf.add_page()
        
        # Set color for title background - improved shade for readability
        pdf.set_fill_color(240, 240, 245)
        pdf.rect(0, 60, 210, 100, 'F')
        
        pdf.ln(80)
        pdf.set_font('Times', 'B', 26)
        
        # Sanitize and clean the title
        clean_story_title = sanitize_for_pdf(clean_title(story["title"]))
        
        # Center title with proper spacing and line handling
        title_words = clean_story_title.split()
        if len(title_words) > 4:
            # Improved title formatting for long titles
            chunks = []
            current_chunk = []
            current_length = 0
            
            for word in title_words:
                if current_length + len(word) > 20:  # Line length threshold
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
                else:
                    current_chunk.append(word)
                    current_length += len(word) + 1  # +1 for space
            
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            
            # Print each chunk as a separate line
            for i, chunk in enumerate(chunks):
                pdf.cell(0, 16, chunk, 0, 1, 'C')
                if i < len(chunks) - 1:
                    pdf.ln(2)  # Less space between title lines
        else:
            pdf.cell(0, 20, clean_story_title, 0, 1, 'C')
        
        if "subtitle" in story:
            pdf.set_font('Times', 'I', 18)
            # Sanitize and clean the subtitle
            clean_subtitle = sanitize_for_pdf(clean_title(story["subtitle"]))
            pdf.cell(0, 15, clean_subtitle, 0, 1, 'C')
            
        pdf.ln(50)
        pdf.set_font('Times', '', 14)
        pdf.cell(0, 10, "Generated by AI Story Generator", 0, 1, 'C')
        
        # Add a blurb page (like the back of a book)
        pdf.add_page()
        pdf.set_font('Times', 'B', 16)
        pdf.cell(0, 20, "About This Book", 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font('Times', '', 12)
        
        # Add the blurb with improved paragraph spacing
        if "blurb" in story:
            sanitized_blurb = sanitize_for_pdf(story["blurb"])
            # Split blurb into paragraphs for better formatting
            blurb_paragraphs = sanitized_blurb.split('\n\n')
            for para in blurb_paragraphs:
                if para.strip():
                    pdf.multi_cell(0, 6, para.strip())
                    pdf.ln(4)  # Space between paragraphs
        
        # Add table of contents with improved book-like design
        pdf.add_page()
        pdf.set_font('Times', 'B', 18)
        pdf.cell(0, 20, "Contents", 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font('Times', '', 12)
        
        for chapter in story["chapters"]:
            # Clean and sanitize the chapter title
            clean_chapter_title = sanitize_for_pdf(clean_title(chapter['title']))
            
            # Update the chapter title in the story object
            chapter['title'] = clean_chapter_title
            
            # Add to table of contents with dot leaders
            chapter_text = f"Chapter {chapter['number']}: {clean_chapter_title}"
            
            # Calculate the width of the text and dots
            text_width = pdf.get_string_width(chapter_text)
            page_text = str(chapter['number'] + 3)  # +3 for cover, blurb, TOC
            page_width = pdf.get_string_width(page_text)
            
            # Available width for dots
            available_width = pdf.w - 50 - text_width - page_width
            
            # Add the chapter text
            pdf.cell(text_width + 5, 8, chapter_text, 0, 0)
            
            # Add dots
            dot_width = pdf.get_string_width('.')
            num_dots = int(available_width / dot_width)
            dots = '.' * num_dots
            pdf.set_font('Times', '', 10)
            pdf.cell(available_width, 8, dots, 0, 0, 'C')
            
            # Add page number
            pdf.set_font('Times', '', 12)
            pdf.cell(page_width, 8, page_text, 0, 1, 'R')
        
        # Add chapters with professional book layout
        for chapter in story["chapters"]:
            # Mark as chapter start to skip header on first page
            pdf.chapter_start = True
            
            pdf.add_page()
            
            # Chapter title with decorative elements - improved spacing
            pdf.set_font('Times', 'B', 18)
            pdf.cell(0, 15, f"Chapter {chapter['number']}", 0, 1, 'C')
            
            pdf.set_font('Times', 'B', 16)
            pdf.cell(0, 10, chapter['title'], 0, 1, 'C')
            
            # Add a decorative line with improved appearance
            pdf.line(pdf.w/4, pdf.y + 5, 3*pdf.w/4, pdf.y + 5)
            pdf.ln(15)
            
            # Sanitize chapter content
            sanitized_content = sanitize_for_pdf(chapter['content'])
            
            # Improved paragraph splitting to handle various formats
            paragraphs = re.split(r'\n\n+', sanitized_content)
            
            for i, paragraph in enumerate(paragraphs):
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                
                # First paragraph with drop cap
                if i == 0 and len(paragraph) > 2:
                    # Extract first letter for drop cap
                    first_letter = paragraph[0]
                    # Try to use drop cap method, fall back to normal paragraph if it fails
                    try:
                        pdf.add_drop_cap(paragraph, first_letter)
                    except Exception:
                        pdf.set_font('Times', '', 12)
                        pdf.multi_cell(0, 6, paragraph)
                # Handle dialogue formatting with appropriate indentation
                elif paragraph.startswith('"'):
                    pdf.set_font('Times', '', 12)
                    # Simulate hanging indent for dialogue
                    first_line_indent = 0
                    subsequent_lines_indent = 5
                    
                    # Split long dialogue into multiple lines for better appearance
                    words = paragraph.split()
                    current_line = words[0]
                    
                    # First line without indent
                    pdf.set_x(pdf.l_margin + first_line_indent)
                    
                    for word in words[1:]:
                        test_line = current_line + " " + word
                        if pdf.get_string_width(test_line) < (pdf.w - pdf.r_margin - pdf.l_margin - subsequent_lines_indent):
                            current_line = test_line
                        else:
                            pdf.cell(0, 6, current_line)
                            pdf.ln()
                            # Subsequent lines with indent
                            pdf.set_x(pdf.l_margin + subsequent_lines_indent)
                            current_line = word
                    
                    # Print the last line
                    pdf.cell(0, 6, current_line)
                    pdf.ln()
                # Scene breaks with improved styling
                elif paragraph.strip() == "* * *" or paragraph.strip() == "***":
                    pdf.ln(4)
                    pdf.set_font('Times', 'B', 12)
                    pdf.cell(0, 6, "* * *", 0, 1, 'C')
                    pdf.ln(4)
                else:
                    # Add first line indentation for regular paragraphs
                    pdf.set_font('Times', '', 12)
                    pdf.set_x(pdf.l_margin + 10)  # Add indent space
                    pdf.multi_cell(0, 6, paragraph)
                
                # Proper spacing between paragraphs
                if i < len(paragraphs) - 1:
                    # Less space between short paragraphs or dialogue
                    if len(paragraph) < 200 or paragraph.startswith('"'):
                        pdf.ln(3)
                    else:
                        pdf.ln(4)
        
        # Critical fix: proper PDF buffer handling
        buffer = io.BytesIO()
        pdf_output = pdf.output(dest='S').encode('latin-1', errors='replace')
        buffer.write(pdf_output)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        import traceback
        logging.error(f"PDF generation failed: {str(e)}")
        logging.error(traceback.format_exc())
        raise

# Improved DOCX creation with proper book styles
def create_docx(story):
    doc = Document()
    
    # Set document margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
    
    # Add cover page
    title = doc.add_heading(story["title"], 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add subtitle if available
    if "subtitle" in story and story["subtitle"]:
        subtitle_para = doc.add_paragraph()
        subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle_run = subtitle_para.add_run(story["subtitle"])
        subtitle_run.italic = True
        subtitle_run.font.size = Pt(16)
    
    # Add "Generated with AI Story Generator" text
    generator_para = doc.add_paragraph()
    generator_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    generator_para.style = 'Subtitle'
    generator_run = generator_para.add_run("Generated with AI Story Generator")
    generator_run.italic = True
    
    # Add page break after cover
    doc.add_page_break()
    
    # Add table of contents
    toc_heading = doc.add_heading("Table of Contents", 1)
    toc_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # List chapters in table of contents
    for chapter in story["chapters"]:
        toc_entry = doc.add_paragraph()
        toc_entry.add_run(f"Chapter {chapter['number']}: {chapter['title']}")
    
    # Add page break after TOC
    doc.add_page_break()
    
    # Add chapters
    for chapter in story["chapters"]:
        # Chapter title
        chapter_title = doc.add_heading(f"Chapter {chapter['number']}: {chapter['title']}", 1)
        chapter_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Chapter content with better paragraph formatting
        paragraphs = chapter["content"].split('\n\n')
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            p = doc.add_paragraph()
            
            # Check if this is dialogue
            if paragraph.startswith('"') or paragraph.startswith('"'):
                run = p.add_run(paragraph)
                run.font.color.rgb = RGBColor(0, 0, 128)  # Dark blue for dialogue
            else:
                p.add_run(paragraph)
                
            p.style.font.size = Pt(12)
            # Add space after paragraph
            p.paragraph_format.space_after = Pt(10)
        
        # Add page break between chapters except for the last one
        if chapter != story["chapters"][-1]:
            doc.add_page_break()
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    num_chapters = int(data.get('num_chapters', 3))
    
    # Validate inputs
    if not title:
        return jsonify({"status": "error", "message": "Title is required"})
    if not description:
        return jsonify({"status": "error", "message": "Description is required"})
    if num_chapters < 1 or num_chapters > 10:
        return jsonify({"status": "error", "message": "Number of chapters must be between 1 and 10"})
    
    try:
        story = generate_story(title, description, num_chapters)
        return jsonify({"status": "success", "story": story})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data received"}), 400
            
        story = data.get('story')
        format_type = data.get('format', 'pdf')
        
        if not story:
            return jsonify({"status": "error", "message": "No story data provided"}), 400
        
        if format_type == 'pdf':
            try:
                buffer = create_pdf(story)
                
                return send_file(
                    buffer,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"{story['title'].replace(' ', '_')}.pdf"
                )
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logging.error(f"PDF generation failed: {error_details}")
                return jsonify({"status": "error", "message": f"PDF generation failed: {str(e)}"}), 500
                
        elif format_type == 'docx':
            try:
                buffer = create_docx(story)
                
                return send_file(
                    buffer,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    as_attachment=True,
                    download_name=f"{story['title'].replace(' ', '_')}.docx"
                )
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logging.error(f"DOCX generation failed: {error_details}")
                return jsonify({"status": "error", "message": f"DOCX generation failed: {str(e)}"}), 500
                
        else:
            return jsonify({"status": "error", "message": "Invalid format specified"}), 400
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Download route error: {error_details}")
        return jsonify({"status": "error", "message": str(e), "details": error_details}), 500
    
if __name__ == '__main__':
    app.run(debug=True)