# app/services/catalogue_loader.py
"""
Dynamic Catalogue Loader for the Recommendation Engine
=======================================================

Bridges MongoDB Elective documents → engine-compatible catalogue dicts.

When admin adds/updates electives via the admin portal, this service:
1. Loads all available electives from MongoDB
2. Converts them to the format expected by CumulativeRecommendationEngine
3. Auto-generates missing fields (subject_weights, keywords, etc.) using NLP heuristics
4. Caches results for 5 minutes (invalidated on CRUD operations)

Falls back to hardcoded catalogues if DB is empty.
"""

import time
import re
import logging
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# ─── Interest area definitions (shared with engine) ───────────────
INTEREST_AREAS = [
    "Artificial Intelligence & Machine Learning",
    "Mobile & IoT Development",
    "Web Development",
    "Data Science & Analytics",
    "Cloud & Distributed Systems",
    "Network & Wireless Systems",
]

# ─── Keyword → interest area mapping (for auto-inference) ─────────
_INTEREST_KEYWORD_MAP: Dict[str, List[str]] = {
    "Artificial Intelligence & Machine Learning": [
        "ai", "ml", "machine learning", "deep learning", "nlp", "neural",
        "tensorflow", "pytorch", "prediction", "classification", "regression",
        "computer vision", "reinforcement", "generative", "transformers",
    ],
    "Mobile & IoT Development": [
        "mobile", "iot", "android", "ios", "flutter", "embedded", "arduino",
        "raspberry", "sensor", "mqtt", "bluetooth", "zigbee", "wearable",
    ],
    "Web Development": [
        "web", "frontend", "backend", "fullstack", "react", "angular",
        "node", "express", "django", "flask", "html", "css", "javascript",
        "api", "rest", "graphql", "responsive",
    ],
    "Data Science & Analytics": [
        "data", "analytics", "statistics", "visualization", "bi", "tableau",
        "power bi", "sql", "etl", "warehouse", "mining", "olap", "dashboard",
        "pandas", "numpy", "report", "insight",
    ],
    "Cloud & Distributed Systems": [
        "cloud", "aws", "azure", "distributed", "devops", "docker",
        "kubernetes", "serverless", "microservices", "ci/cd", "terraform",
        "container", "orchestration", "scalab", "deploy",
    ],
    "Network & Wireless Systems": [
        "network", "wireless", "security", "cyber", "routing", "protocol",
        "firewall", "encryption", "5g", "cellular", "vpn", "intrusion",
        "penetration", "forensics", "compliance",
    ],
}

# ─── Canonical subjects the engine knows about ────────────────────
CANONICAL_SUBJECTS = [
    "Engineering Mathematics-III", "Engineering Mathematics-IV",
    "Data Structures and Algorithms", "Database Management Systems",
    "Digital Logic & Design", "Operating Systems", "Computer Networks",
    "Microcontroller & Embedded Systems", "Software Engineering",
    "Python", "C++", "Java", "Automata Theory", "Design & Analysis of Algorithms",
    "Artificial Intelligence", "Cryptography & Network Security",
    "Full Stack Development", "IoT",
]

# Subject keyword mapping for auto-weight generation
_SUBJECT_KEYWORDS: Dict[str, List[str]] = {
    "Engineering Mathematics-III": ["math", "calculus", "differential", "fourier", "laplace", "probability", "statistics"],
    "Engineering Mathematics-IV": ["math", "linear algebra", "optimization", "numerical", "complex", "statistics"],
    "Data Structures and Algorithms": ["dsa", "algorithm", "data structure", "sorting", "searching", "tree", "graph", "stack", "queue", "linked list"],
    "Database Management Systems": ["database", "sql", "dbms", "relational", "normalization", "query", "er model", "nosql", "mongodb"],
    "Digital Logic & Design": ["digital", "logic", "circuit", "gate", "flip flop", "counter", "register", "boolean"],
    "Operating Systems": ["os", "operating system", "process", "thread", "memory", "scheduling", "deadlock", "file system", "kernel"],
    "Computer Networks": ["network", "tcp", "ip", "routing", "protocol", "osi", "http", "dns", "socket", "lan", "wan"],
    "Microcontroller & Embedded Systems": ["microcontroller", "embedded", "arduino", "arm", "gpio", "interrupt", "timer", "uart", "spi", "i2c"],
    "Software Engineering": ["software engineering", "sdlc", "agile", "scrum", "testing", "requirements", "uml", "design pattern"],
    "Python": ["python", "pandas", "numpy", "flask", "django", "scripting", "automation"],
    "C++": ["c++", "cpp", "stl", "oop", "object oriented", "pointer", "template"],
    "Java": ["java", "jvm", "spring", "servlet", "jdbc", "multithreading"],
    "Automata Theory": ["automata", "finite", "grammar", "turing", "regular expression", "context free", "pushdown"],
    "Design & Analysis of Algorithms": ["algorithm", "complexity", "greedy", "dynamic programming", "divide and conquer", "np hard", "backtracking"],
    "Artificial Intelligence": ["ai", "artificial intelligence", "search", "heuristic", "knowledge", "expert system", "reasoning"],
    "Cryptography & Network Security": ["crypto", "encryption", "decryption", "cipher", "hash", "rsa", "aes", "digital signature", "certificate"],
    "Full Stack Development": ["fullstack", "full stack", "mern", "mean", "frontend", "backend", "react", "node", "express", "api"],
    "IoT": ["iot", "internet of things", "smart", "sensor", "mqtt", "edge", "gateway"],
}


class CatalogueLoader:
    """
    Loads elective catalogues from MongoDB and converts them
    to the dict format expected by CumulativeRecommendationEngine.
    """

    _cache: Optional[Dict[str, Any]] = None
    _cache_timestamp: float = 0
    CACHE_TTL: int = 300  # 5 minutes

    # ─── Public API ───────────────────────────────────────────

    @classmethod
    async def load_program_electives(cls, force_refresh: bool = False) -> Dict[str, Any]:
        """Load program elective catalogues (Sem 5-6 pairs)."""
        return await cls._load_by_category("Program Elective", force_refresh)

    @classmethod
    async def load_open_electives(cls, force_refresh: bool = False) -> Dict[str, Any]:
        """Load open elective catalogues (Sem 7)."""
        return await cls._load_by_category("Open Elective", force_refresh)

    @classmethod
    async def load_all_catalogues(cls, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Load ALL elective catalogues from MongoDB.
        
        Returns dict with keys:
        - program_elective_meta, program_subject_weights, program_interest_map,
          program_project_skill_map, program_concept_map
        - open_elective_meta, open_subject_weights, open_interest_map,
          open_project_skill_map, open_concept_map
        - honours_programs
        - elective_labels (list of engine keys)
        - db_elective_count (total found in DB)
        """
        if (
            not force_refresh
            and cls._cache is not None
            and (time.time() - cls._cache_timestamp) < cls.CACHE_TTL
        ):
            return cls._cache

        try:
            from app.models.elective import Elective, ElectiveCategory

            all_electives = await Elective.find({"is_available": True}).to_list()
            logger.info(f"📦 CatalogueLoader: Found {len(all_electives)} electives in DB")

            if not all_electives:
                logger.warning("⚠ No electives in DB — engine will use hardcoded fallback")
                cls._cache = {"db_elective_count": 0}
                cls._cache_timestamp = time.time()
                return cls._cache

            # Split by category
            program = [e for e in all_electives if e.category == ElectiveCategory.PROGRAM_ELECTIVE]
            open_elec = [e for e in all_electives if e.category == ElectiveCategory.OPEN_ELECTIVE]
            honours = [e for e in all_electives if e.category in (
                ElectiveCategory.HONOURS_MINOR, ElectiveCategory.MULTIDISCIPLINARY_MINOR
            )]

            result = {
                "db_elective_count": len(all_electives),
                # Program Electives
                **cls._build_catalogue(program, prefix="program"),
                # Open Electives
                **cls._build_catalogue(open_elec, prefix="open"),
                # Honours programs
                "honours_programs": cls._build_honours(honours),
            }

            cls._cache = result
            cls._cache_timestamp = time.time()

            logger.info(
                f"✅ Catalogues loaded: "
                f"{len(program)} program, {len(open_elec)} open, {len(honours)} honours"
            )
            return result

        except Exception as e:
            logger.error(f"❌ CatalogueLoader error: {e}", exc_info=True)
            return {"db_elective_count": 0}

    @classmethod
    def invalidate_cache(cls):
        """Call this after any elective CRUD operation."""
        cls._cache = None
        cls._cache_timestamp = 0
        logger.info("🔄 Catalogue cache invalidated")

    # ─── Internal builders ────────────────────────────────────

    @classmethod
    def _build_catalogue(cls, electives: list, prefix: str) -> Dict[str, Any]:
        """Convert a list of Elective docs to engine-compatible dicts."""
        meta: Dict[str, Any] = {}
        subject_weights: Dict[str, Dict[str, float]] = {}
        interest_map: Dict[str, List[Tuple[str, float]]] = {}
        project_skill_map: Dict[str, List[str]] = {}
        concept_map: Dict[str, List[Tuple[str, float]]] = {}
        labels: List[str] = []

        for elective in electives:
            key = elective.engine_key or elective.code
            labels.append(key)

            # ── Meta ──
            meta[key] = {
                "code": elective.code,
                "name": elective.name,
                "credits": elective.credits,
                "career_paths": elective.career_paths or [],
                "skills": elective.skills_covered or [],
                "description": elective.description or "",
                "semester": elective.semester,
                "category": elective.category.value if hasattr(elective.category, 'value') else str(elective.category),
                "modules": getattr(elective, 'modules', []) or [],
            }

            # ── Subject weights ──
            if elective.subject_weights:
                subject_weights[key] = elective.subject_weights
            else:
                subject_weights[key] = cls._auto_generate_subject_weights(elective)

            # ── Interest mappings ──
            if elective.interest_mappings:
                interest_map[key] = [
                    (m.get("area", ""), m.get("weight", 1.0))
                    for m in elective.interest_mappings
                ]
            else:
                interest_map[key] = cls._auto_generate_interest_map(elective)

            # ── Project keywords ──
            if elective.project_keywords:
                project_skill_map[key] = elective.project_keywords
            else:
                project_skill_map[key] = cls._auto_extract_keywords(elective)

            # ── Concept prefixes ──
            if elective.concept_prefixes:
                concept_map[key] = [
                    (c.get("prefix", ""), c.get("weight", 0.4))
                    for c in elective.concept_prefixes
                ]
            else:
                concept_map[key] = cls._auto_generate_concepts(elective)

        return {
            f"{prefix}_elective_meta": meta,
            f"{prefix}_subject_weights": subject_weights,
            f"{prefix}_interest_map": interest_map,
            f"{prefix}_project_skill_map": project_skill_map,
            f"{prefix}_concept_map": concept_map,
            f"{prefix}_labels": labels,
        }

    @classmethod
    def _build_honours(cls, electives: list) -> List[Dict[str, Any]]:
        """Convert honours/minor electives to engine-compatible format."""
        programs = []
        for e in electives:
            programs.append({
                "program": e.name,
                "type": "honours" if "honours" in (e.category.value or "").lower() else "minor",
                "required_cgpa": e.min_cgpa_required or 7.0,
                "relevant_subjects": e.prerequisites or [],
                "relevant_interests": [
                    m.get("area", "") for m in (e.interest_mappings or [])
                ],
                "project_keywords": e.project_keywords or cls._auto_extract_keywords(e),
                "career_paths": e.career_paths or [],
                "skills_gained": e.skills_covered or [],
            })
        return programs

    # ─── Auto-generation heuristics ───────────────────────────

    @classmethod
    def _auto_generate_subject_weights(cls, elective) -> Dict[str, float]:
        """
        Auto-generate prerequisite subject weights by matching elective
        description/topics/skills against known canonical subjects.
        """
        blob = " ".join([
            elective.description or "",
            " ".join(elective.topics or []),
            " ".join(elective.skills_covered or []),
            " ".join(getattr(elective, 'modules', []) or []),
            getattr(elective, 'syllabus_text', "") or "",
        ]).lower()

        weights: Dict[str, float] = {}

        for subject, keywords in _SUBJECT_KEYWORDS.items():
            score = 0.0
            for kw in keywords:
                if kw in blob:
                    score += 1.0
            if score > 0:
                # Normalize: max weight = 3.5 for strong matches
                weight = min(score * 0.7, 3.5)
                weights[subject] = round(weight, 1)

        # If prerequisites are specified, give them high weight
        for prereq in (elective.prerequisites or []):
            prereq_lower = prereq.lower().strip()
            for subject in CANONICAL_SUBJECTS:
                if prereq_lower in subject.lower() or subject.lower() in prereq_lower:
                    weights[subject] = max(weights.get(subject, 0), 3.0)

        if not weights:
            # Fallback: give small weight to general subjects
            weights["Software Engineering"] = 1.0
            weights["Data Structures and Algorithms"] = 1.0

        return weights

    @classmethod
    def _auto_generate_interest_map(cls, elective) -> List[Tuple[str, float]]:
        """
        Auto-map elective to interest areas based on its description,
        topics, skills, and career paths.
        """
        blob = " ".join([
            elective.description or "",
            " ".join(elective.topics or []),
            " ".join(elective.skills_covered or []),
            " ".join(elective.career_paths or []),
        ]).lower()

        scores: Dict[str, float] = defaultdict(float)

        for area, keywords in _INTEREST_KEYWORD_MAP.items():
            for kw in keywords:
                if kw in blob:
                    scores[area] += 0.5

        # Return top-3 interest areas with normalized weights
        sorted_areas = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        result = []
        for area, score in sorted_areas[:3]:
            if score > 0:
                weight = min(score, 2.5)
                result.append((area, round(weight, 1)))

        return result if result else [("Web Development", 1.0)]

    @classmethod
    def _auto_extract_keywords(cls, elective) -> List[str]:
        """
        Auto-extract project-matching keywords from elective fields.
        """
        keywords = set()

        # From skills
        for skill in (elective.skills_covered or []):
            keywords.add(skill.lower().strip())
            # Also add individual words > 3 chars
            for word in skill.lower().split():
                if len(word) > 3 and word not in {"with", "from", "this", "that", "have", "will"}:
                    keywords.add(word)

        # From topics
        for topic in (elective.topics or []):
            for word in topic.lower().split():
                cleaned = re.sub(r'[^a-z0-9+#]', '', word)
                if len(cleaned) > 2 and cleaned not in {"and", "the", "for", "are"}:
                    keywords.add(cleaned)

        # From career paths
        for career in (elective.career_paths or []):
            for word in career.lower().split():
                if len(word) > 3 and word not in {"with", "from", "this", "that"}:
                    keywords.add(word)

        # From description (important words)
        desc = (elective.description or "").lower()
        for word in desc.split():
            cleaned = re.sub(r'[^a-z0-9+#]', '', word)
            if len(cleaned) > 4 and cleaned not in {
                "covers", "includes", "introduction", "which", "about",
                "course", "students", "learn", "study", "based",
            }:
                keywords.add(cleaned)

        # From modules
        for module in (getattr(elective, 'modules', []) or []):
            for word in module.lower().split():
                cleaned = re.sub(r'[^a-z0-9+#]', '', word)
                if len(cleaned) > 3:
                    keywords.add(cleaned)

        return sorted(keywords)

    @classmethod
    def _auto_generate_concepts(cls, elective) -> List[Tuple[str, float]]:
        """
        Auto-generate concept prefixes for fuzzy matching.
        Takes important words from description/topics and creates
        prefix stems for partial matching.
        """
        blob = " ".join([
            elective.description or "",
            " ".join(elective.topics or []),
            " ".join(elective.skills_covered or []),
        ]).lower()

        concepts = []
        seen_prefixes = set()

        # Extract meaningful words and create stem prefixes
        words = re.findall(r'[a-z]{4,}', blob)
        word_freq: Dict[str, int] = defaultdict(int)
        for w in words:
            if w not in {"with", "from", "this", "that", "have", "will",
                         "covers", "includes", "introduction", "which",
                         "about", "course", "students", "learn", "based"}:
                word_freq[w] += 1

        # Top words by frequency → concept prefixes
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        for word, freq in sorted_words[:15]:
            prefix = word[:min(len(word), 6)]  # Take first 6 chars as prefix
            if prefix not in seen_prefixes and len(prefix) >= 4:
                seen_prefixes.add(prefix)
                weight = min(0.3 + (freq * 0.1), 0.6)
                concepts.append((prefix, round(weight, 1)))

        return concepts

    # ─── Category-specific loader ─────────────────────────────

    @classmethod
    async def _load_by_category(cls, category_value: str, force_refresh: bool) -> Dict[str, Any]:
        """Load catalogues filtered by category."""
        all_cats = await cls.load_all_catalogues(force_refresh)
        prefix = "program" if "Program" in category_value else "open"
        return {
            "elective_meta": all_cats.get(f"{prefix}_elective_meta", {}),
            "subject_weights": all_cats.get(f"{prefix}_subject_weights", {}),
            "interest_map": all_cats.get(f"{prefix}_interest_map", {}),
            "project_skill_map": all_cats.get(f"{prefix}_project_skill_map", {}),
            "concept_map": all_cats.get(f"{prefix}_concept_map", {}),
            "labels": all_cats.get(f"{prefix}_labels", []),
        }
