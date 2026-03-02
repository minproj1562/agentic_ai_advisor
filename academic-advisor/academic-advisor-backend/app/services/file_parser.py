# academic-advisor-backend/app/services/file_parser.py
"""
Robust File Parser for Project Analysis
========================================
Handles: PDF, Images (OCR), Code files, Text/Markdown, Documents
Extracts text content and identifies technical skills.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── Optional dependency imports ─────────────────────────────────
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    logger.info("pdfplumber not installed – PDF text extraction disabled")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    logger.info("pytesseract not installed – image OCR disabled")

# ── Skill keyword catalogue ────────────────────────────────────

SKILL_KEYWORDS: Dict[str, str] = {
    # Languages
    "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
    "java ": "Java", "kotlin": "Kotlin", "swift": "Swift", "golang": "Go",
    "rust": "Rust", "c++": "C++", "c#": "C#", "ruby": "Ruby", "php": "PHP",
    "scala": "Scala", "r ": "R", "dart": "Dart", "lua": "Lua",
    # ML / Data
    "tensorflow": "TensorFlow", "pytorch": "PyTorch", "keras": "Keras",
    "scikit-learn": "Scikit-learn", "sklearn": "Scikit-learn",
    "pandas": "Pandas", "numpy": "NumPy", "matplotlib": "Matplotlib",
    "seaborn": "Seaborn", "opencv": "OpenCV", "nltk": "NLTK",
    "spacy": "spaCy", "hugging face": "HuggingFace", "transformers": "Transformers",
    "langchain": "LangChain", "xgboost": "XGBoost", "lightgbm": "LightGBM",
    # Web
    "react": "React", "angular": "Angular", "vue": "Vue.js",
    "next.js": "Next.js", "nuxt": "Nuxt.js", "svelte": "Svelte",
    "express": "Express.js", "fastapi": "FastAPI", "django": "Django",
    "flask": "Flask", "spring boot": "Spring Boot", "node.js": "Node.js",
    "tailwind": "Tailwind CSS", "bootstrap": "Bootstrap",
    # Cloud / DevOps
    "docker": "Docker", "kubernetes": "Kubernetes", "aws": "AWS",
    "azure": "Azure", "gcp": "GCP", "terraform": "Terraform",
    "ansible": "Ansible", "jenkins": "Jenkins", "github actions": "GitHub Actions",
    "ci/cd": "CI/CD", "nginx": "Nginx",
    # Databases
    "mongodb": "MongoDB", "postgresql": "PostgreSQL", "mysql": "MySQL",
    "redis": "Redis", "firebase": "Firebase", "elasticsearch": "Elasticsearch",
    "graphql": "GraphQL", "prisma": "Prisma",
    # IoT / Embedded
    "arduino": "Arduino", "raspberry pi": "Raspberry Pi", "mqtt": "MQTT",
    "esp32": "ESP32", "embedded": "Embedded Systems",
    # Mobile
    "flutter": "Flutter", "react native": "React Native",
    "android": "Android", "ios": "iOS",
    # Misc
    "machine learning": "Machine Learning", "deep learning": "Deep Learning",
    "neural network": "Neural Networks", "computer vision": "Computer Vision",
    "natural language processing": "NLP", "nlp": "NLP",
    "data science": "Data Science", "data analysis": "Data Analysis",
    "blockchain": "Blockchain", "microservices": "Microservices",
    "rest api": "REST API", "websocket": "WebSocket",
    "sql": "SQL", "nosql": "NoSQL", "git": "Git",
    "linux": "Linux", "bash": "Bash",
    "jupyter": "Jupyter", "kaggle": "Kaggle",
    "iot": "IoT", "devops": "DevOps",
}

# File extensions considered as code
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".cs",
    ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".r",
    ".html", ".css", ".scss", ".sql", ".sh", ".bash", ".yaml", ".yml",
    ".json", ".xml", ".toml", ".ini", ".cfg", ".dockerfile",
    ".ipynb",  # Jupyter notebooks
}

TEXT_EXTENSIONS = {".txt", ".md", ".rst", ".csv", ".log"}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}

PDF_EXTENSIONS = {".pdf"}


class FileParser:
    """
    Parses uploaded files, extracts text, and identifies skills.

    Usage::

        from app.services.file_parser import file_parser

        results = file_parser.parse_multiple(uploaded_files)
        text = results["aggregated_text"]
        skills = results["aggregated_skills"]
    """

    # ── Public API ──────────────────────────────────────────────

    def parse_multiple(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse a list of uploaded files.

        Each item in *files* must have::

            {"path": str, "type": str (mime), "name": str, "size": int}

        Returns::

            {
                "total_files": int,
                "successfully_parsed": int,
                "aggregated_text": str,
                "aggregated_skills": [str, ...],
                "file_results": [{...}, ...],
            }
        """
        all_text_parts: List[str] = []
        all_skills: set = set()
        file_results: List[Dict[str, Any]] = []

        for f in files:
            result = self.parse_single(f)
            file_results.append(result)
            if result["parse_success"]:
                all_text_parts.append(result.get("text", ""))
                all_skills.update(result.get("skills_found", []))

        aggregated_text = "\n\n".join(t for t in all_text_parts if t)
        successfully_parsed = sum(1 for r in file_results if r["parse_success"])

        return {
            "total_files": len(files),
            "successfully_parsed": successfully_parsed,
            "aggregated_text": aggregated_text,
            "aggregated_skills": sorted(all_skills),
            "file_results": file_results,
        }

    def parse_single(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Parse one file and return extracted data."""
        path = file_info.get("path", "")
        name = file_info.get("name", os.path.basename(path))
        mime = file_info.get("type", "")
        ext = os.path.splitext(name)[1].lower()

        result: Dict[str, Any] = {
            "filename": name,
            "parse_success": False,
            "parse_method": "none",
            "text": "",
            "text_length": 0,
            "skills_found": [],
            "error": None,
        }

        try:
            text = ""

            # ── PDF ────────────────────────────────────────────
            if ext in PDF_EXTENSIONS or "pdf" in mime:
                text = self._parse_pdf(path)
                result["parse_method"] = "pdfplumber"

            # ── Image (OCR) ────────────────────────────────────
            elif ext in IMAGE_EXTENSIONS or mime.startswith("image/"):
                text = self._parse_image(path)
                result["parse_method"] = "tesseract_ocr" if HAS_TESSERACT else "image_skipped"

            # ── Code files ─────────────────────────────────────
            elif ext in CODE_EXTENSIONS:
                text = self._parse_text_file(path)
                result["parse_method"] = "code_reader"

            # ── Text / Markdown ────────────────────────────────
            elif ext in TEXT_EXTENSIONS:
                text = self._parse_text_file(path)
                result["parse_method"] = "text_reader"

            # ── Jupyter Notebook ───────────────────────────────
            elif ext == ".ipynb":
                text = self._parse_notebook(path)
                result["parse_method"] = "notebook_parser"

            # ── Unknown ────────────────────────────────────────
            else:
                result["parse_method"] = "unsupported"
                result["error"] = f"Unsupported file type: {ext}"
                return result

            if text:
                result["text"] = text
                result["text_length"] = len(text)
                result["skills_found"] = self._extract_skills(text)
                result["parse_success"] = True
            else:
                result["error"] = "No text extracted"

        except Exception as e:
            logger.warning(f"Failed to parse {name}: {e}")
            result["error"] = str(e)

        return result

    # ── Private parsers ─────────────────────────────────────────

    def _parse_pdf(self, path: str) -> str:
        if not HAS_PDFPLUMBER:
            logger.warning("pdfplumber not installed, cannot parse PDF")
            return ""
        try:
            parts: List[str] = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        parts.append(text)
                    # Also try extracting tables
                    tables = page.extract_tables()
                    for table in (tables or []):
                        for row in table:
                            if row:
                                cells = [str(c).strip() for c in row if c]
                                if cells:
                                    parts.append(" | ".join(cells))
            return "\n".join(parts)
        except Exception as e:
            logger.warning(f"PDF parse error: {e}")
            return ""

    def _parse_image(self, path: str) -> str:
        if not (HAS_PIL and HAS_TESSERACT):
            logger.info("OCR dependencies not available, skipping image")
            return ""
        try:
            img = Image.open(path)
            text = pytesseract.image_to_string(img)
            return text.strip() if text else ""
        except Exception as e:
            logger.warning(f"Image OCR error: {e}")
            return ""

    def _parse_text_file(self, path: str, max_bytes: int = 500_000) -> str:
        try:
            size = os.path.getsize(path)
            if size > max_bytes:
                logger.info(f"File too large ({size} bytes), truncating to {max_bytes}")
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read(max_bytes)
        except Exception as e:
            logger.warning(f"Text read error: {e}")
            return ""

    def _parse_notebook(self, path: str) -> str:
        """Extract code and markdown cells from Jupyter notebook."""
        try:
            import json as _json
            with open(path, "r", encoding="utf-8") as f:
                nb = _json.load(f)
            parts: List[str] = []
            for cell in nb.get("cells", []):
                cell_type = cell.get("cell_type", "")
                source = "".join(cell.get("source", []))
                if cell_type in ("code", "markdown") and source.strip():
                    parts.append(source)
            return "\n\n".join(parts)
        except Exception as e:
            logger.warning(f"Notebook parse error: {e}")
            return ""

    # ── Skill extraction ────────────────────────────────────────

    @staticmethod
    def _extract_skills(text: str) -> List[str]:
        """Find known skill keywords in text."""
        low = text.lower()
        found: set = set()
        for keyword, canonical in SKILL_KEYWORDS.items():
            # Use word-boundary-ish matching for short keywords
            if len(keyword) <= 3:
                if re.search(r"\b" + re.escape(keyword.strip()) + r"\b", low):
                    found.add(canonical)
            else:
                if keyword in low:
                    found.add(canonical)
        return sorted(found)


# ── Singleton ───────────────────────────────────────────────────
file_parser = FileParser()