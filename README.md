# AI Book Generator

An interactive web application that generates complete, professional-quality stories and books using a multi-agent AI system.

![image](https://github.com/user-attachments/assets/8626ab51-f7e0-44e3-90fb-cd25f1d9b1ce) 

## Overview

The AI Book Generator uses OpenAI's language models and a multi-agent architecture to create compelling stories with:

- Plot outlines
- Chapter development
- Consistent character arcs
- Professional formatting
- Downloadable PDF and DOCX outputs

The application leverages specialized "agent" roles, each responsible for different aspects of storytelling, to ensure cohesive and engaging narratives.

## Features

- **Multi-Agent Story Creation**: Uses specialized AI agents for plot architecture, narrative development, dialogue enhancement, and continuity management
- **Dynamic Story Generation**: Creates complete stories with customizable length and complexity
- **Professional Formatting**: Generates publication-ready documents with proper typesetting, headers, and layout
- **Multiple Export Formats**: Download your story as PDF or DOCX
- **Interactive Web Interface**: Simple, user-friendly interface for story generation

## Installation

### Prerequisites

- Python 3.8+
- Flask
- OpenAI API key
- Other dependencies listed in requirements.txt

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Saifulislamsayem19/AI-Book-Generator.git
cd AI-Book-Generator
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

5. Run the application:
```bash
python app.py
```

6. Open your browser and navigate to `http://127.0.0.1:5000`

## Usage

1. Enter a title for your story
2. Provide a brief description or premise
3. Select the number of chapters (1-10)
4. Click "Generate Story"
5. Review the generated story
6. Download in your preferred format (PDF or DOCX)

## Project Structure

```
AI-Book-Generator/
├── app.py                # Main Flask application
├── templates/            # HTML templates
│   └── index.html        # Main application interface
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

## How It Works

The AI Book Generator uses a multi-agent approach to storytelling:

1. **Input Parameters**: The user provides a title, description, and the number of chapters for the story.
2. **Story Generation**: The backend uses OpenAI's GPT-3.5-turbo to generate the plot outline, character arcs, and chapter details.
3. **Download Options**: Once the story is generated, the user can download it in PDF or DOCX format.
4. **PDF/Docx Styling**: The generated document includes:
    - Cover page
    - Table of contents
    - Chapter headings
    - Professional formatting for a polished look

## Screenshots

### Take title, description, and the number of chapters for the story
![Screenshot_9-4-2025_1660_127 0 0 1](https://github.com/user-attachments/assets/1b743776-99fe-4600-8e42-24cd253123b5)

### Creates a comprehensive plot outline and narrative structure
![Screenshot_9-4-2025_16644_127 0 0 1](https://github.com/user-attachments/assets/b60e020e-8c9f-45e3-871c-3314f88f7a7a)

### Generates chapter content with character development and plot progression
![image](https://github.com/user-attachments/assets/1107e10e-5403-41e1-99f8-47e8f18bd14a)

### Downloadable in PDF and DOCX format
![image](https://github.com/user-attachments/assets/b721b8b0-9819-40ef-a250-63529f8e6865)

Each chapter is generated with awareness of previous content, maintaining narrative coherence throughout the entire story.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the AI models
- Flask for the web framework
- The Python document processing libraries (python-docx, fpdf)

