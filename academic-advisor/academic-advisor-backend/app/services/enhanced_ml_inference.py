# academic-advisor-backend/app/services/enhanced_ml_inference.py
"""
Enhanced ML Inference Engine
=============================
Provides FCRITAcademicInferenceEngine — the project analysis layer
that extracts skills, infers interests, and calculates complexity.

Delegates actual recommendations to recommendation_engine.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ─── Interest patterns ──────────────────────────────────────────

INTEREST_PATTERNS: Dict[str, Dict[str, Any]] = {
    "Artificial Intelligence & Machine Learning": {
        "keywords": [
            "machine learning", "deep learning", "ai", "neural network",
            "tensorflow", "pytorch", "nlp", "natural language processing",
            "computer vision", "data science", "sklearn", "scikit-learn",
            "regression", "classification", "clustering", "keras",
            "transformer", "bert", "gpt", "reinforcement learning",
            "generative ai", "llm", "langchain", "hugging face",
            "model training", "feature engineering", "random forest",
        ],
        "related_skills": ["Python", "TensorFlow", "PyTorch", "NumPy", "Pandas", "Scikit-learn"],
        "career_paths": ["ML Engineer", "Data Scientist", "AI Researcher", "NLP Engineer"],
        "industry_relevance": 0.95,
    },
    "Web Development": {
        "keywords": [
            "web", "react", "angular", "vue", "frontend", "backend",
            "fullstack", "full-stack", "html", "css", "javascript",
            "node", "express", "django", "flask", "fastapi", "next.js",
            "rest api", "graphql", "responsive", "spa", "ssr",
            "tailwind", "bootstrap", "webpack", "vite",
        ],
        "related_skills": ["JavaScript", "React", "Node.js", "HTML/CSS", "TypeScript"],
        "career_paths": ["Full Stack Developer", "Frontend Developer", "Backend Developer"],
        "industry_relevance": 0.90,
    },
    "Mobile & IoT Development": {
        "keywords": [
            "mobile", "android", "ios", "flutter", "react native",
            "swift", "kotlin", "iot", "arduino", "raspberry pi",
            "embedded", "sensor", "bluetooth", "zigbee", "mqtt",
            "esp32", "esp8266", "lora", "rfid", "microcontroller",
            "wearable", "smart home",
        ],
        "related_skills": ["Flutter", "React Native", "Arduino", "Kotlin", "Swift"],
        "career_paths": ["Mobile Developer", "IoT Engineer", "Embedded Developer"],
        "industry_relevance": 0.85,
    },
    "Cloud & Distributed Systems": {
        "keywords": [
            "cloud", "aws", "azure", "gcp", "docker", "kubernetes",
            "devops", "terraform", "serverless", "microservices",
            "ci/cd", "jenkins", "github actions", "ansible",
            "load balancing", "scalability", "distributed",
            "container", "orchestration", "lambda", "ec2",
        ],
        "related_skills": ["AWS", "Docker", "Kubernetes", "Terraform", "Linux"],
        "career_paths": ["Cloud Architect", "DevOps Engineer", "SRE", "Platform Engineer"],
        "industry_relevance": 0.92,
    },
    "Data Science & Analytics": {
        "keywords": [
            "data analysis", "analytics", "visualization", "tableau",
            "power bi", "statistics", "pandas", "bi", "dashboard",
            "data pipeline", "etl", "data warehouse", "spark",
            "hadoop", "bigquery", "redshift", "sql", "olap",
            "a/b testing", "hypothesis", "exploratory",
        ],
        "related_skills": ["Python", "SQL", "Tableau", "Pandas", "R"],
        "career_paths": ["Data Analyst", "BI Developer", "Data Engineer", "Analytics Manager"],
        "industry_relevance": 0.88,
    },
    "Network & Wireless Systems": {
        "keywords": [
            "network", "security", "wireless", "protocol", "firewall",
            "cryptography", "cyber", "penetration", "ethical hacking",
            "vpn", "routing", "switching", "tcp/ip", "dns",
            "intrusion detection", "siem", "encryption",
        ],
        "related_skills": ["Network Security", "Linux", "Wireshark", "Cryptography"],
        "career_paths": ["Security Engineer", "Network Engineer", "Penetration Tester"],
        "industry_relevance": 0.87,
    },
}

HONOURS_PROGRAMS: Dict[str, Dict[str, Any]] = {
    "Artificial Intelligence & Machine Learning": {
        "eligible_branches": ["IT", "CSE", "COMP", "ECE"],
        "type": "both",
        "courses": ["Knowledge Engineering", "Foundation ML", "Deep Learning", "Advanced AI"],
        "career_paths": ["AI Engineer", "ML Engineer", "Data Scientist", "AI Researcher"],
        "skills": ["Python", "TensorFlow", "PyTorch", "NLP", "Computer Vision"],
        "keywords": ["ai", "machine learning", "deep learning", "neural networks", "data science"],
    },
    "Data Science": {
        "eligible_branches": ["IT", "CSE", "COMP", "MECH"],
        "type": "Honours",
        "courses": ["Data Analytics", "Statistical Methods", "Big Data", "Data Visualisation"],
        "career_paths": ["Data Scientist", "Data Analyst", "BI Developer", "Analytics Manager"],
        "skills": ["Python", "R", "SQL", "Tableau", "Spark"],
        "keywords": ["data science", "analytics", "big data", "statistics", "visualization"],
    },
    "Cyber Security": {
        "eligible_branches": ["IT", "CSE", "COMP", "ECE"],
        "type": "Minor",
        "courses": ["Network Security", "Ethical Hacking", "Cryptography", "Security Management"],
        "career_paths": ["Security Analyst", "Penetration Tester", "Security Architect"],
        "skills": ["Network Security", "Linux", "Python", "Cryptography"],
        "keywords": ["cybersecurity", "security", "hacking", "network", "firewall"],
    },
    "Cloud Computing": {
        "eligible_branches": ["IT", "CSE", "COMP"],
        "type": "Minor",
        "courses": ["Cloud Architecture", "Containers", "DevOps", "Serverless Computing"],
        "career_paths": ["Cloud Architect", "DevOps Engineer", "SRE"],
        "skills": ["AWS", "Docker", "Kubernetes", "Terraform"],
        "keywords": ["cloud", "aws", "docker", "kubernetes", "devops"],
    },
    "IoT & Embedded Systems": {
        "eligible_branches": ["IT", "ECE", "EXTC", "MECH"],
        "type": "Minor",
        "courses": ["Embedded Programming", "Sensor Networks", "IoT Protocols", "Edge Computing"],
        "career_paths": ["IoT Engineer", "Embedded Developer", "Hardware Engineer"],
        "skills": ["Arduino", "Raspberry Pi", "C/C++", "MQTT"],
        "keywords": ["iot", "embedded", "arduino", "sensor", "microcontroller"],
    },
}

SEM5_ELECTIVES: Dict[str, Dict[str, List[str]]] = {
    "IT": {
        "professional": [
            "Machine Learning",
            "Wireless Technology",
            "Data Warehouse and Mining",
            "Cloud Computing Services",
        ],
        "open": [
            "Entrepreneurship Development",
            "Technical Communication",
            "Disaster Management",
        ],
    },
    "CSE": {
        "professional": [
            "Machine Learning",
            "Computer Vision",
            "Natural Language Processing",
            "Big Data Analytics",
        ],
        "open": [
            "Entrepreneurship Development",
            "Technical Communication",
        ],
    },
    "COMP": {
        "professional": [
            "Machine Learning",
            "Data Warehouse and Mining",
            "Cloud Computing Services",
            "Wireless Technology",
        ],
        "open": [
            "Entrepreneurship Development",
            "Technical Communication",
        ],
    },
}

CAREER_MAPPING: Dict[str, Dict[str, Any]] = {
    "Software Development Engineer": {
        "keywords": ["web", "api", "fullstack", "react", "node", "java", "spring"],
        "salary": "₹6-18 LPA",
        "growth": "High",
        "companies": ["Google", "Microsoft", "Amazon", "Flipkart"],
    },
    "ML Engineer": {
        "keywords": ["machine learning", "tensorflow", "pytorch", "python", "deep learning"],
        "salary": "₹8-25 LPA",
        "growth": "Very High",
        "companies": ["Google", "Meta", "OpenAI", "NVIDIA"],
    },
    "Data Scientist": {
        "keywords": ["data", "analytics", "python", "sql", "statistics", "pandas"],
        "salary": "₹8-22 LPA",
        "growth": "Very High",
        "companies": ["Google", "Amazon", "Netflix", "Uber"],
    },
    "Cloud / DevOps Engineer": {
        "keywords": ["aws", "docker", "kubernetes", "cloud", "ci/cd", "terraform"],
        "salary": "₹7-20 LPA",
        "growth": "High",
        "companies": ["AWS", "Microsoft", "Google Cloud", "Atlassian"],
    },
    "IoT / Embedded Engineer": {
        "keywords": ["iot", "arduino", "embedded", "sensor", "raspberry pi", "microcontroller"],
        "salary": "₹5-16 LPA",
        "growth": "High",
        "companies": ["Bosch", "Siemens", "Texas Instruments", "Qualcomm"],
    },
    "Security Engineer": {
        "keywords": ["security", "penetration", "firewall", "cryptography", "network"],
        "salary": "₹7-22 LPA",
        "growth": "Very High",
        "companies": ["CrowdStrike", "Palo Alto", "Cisco", "IBM"],
    },
}


class FCRITAcademicInferenceEngine:
    honours_programs = HONOURS_PROGRAMS
    sem5_electives = SEM5_ELECTIVES

    def __init__(self):
        self._file_parser = None
        self._file_parser_loaded = False

    @property
    def file_parser(self):
        if not self._file_parser_loaded:
            self._file_parser_loaded = True
            try:
                from app.services.file_parser import file_parser
                self._file_parser = file_parser
                logger.info("✅ FileParser loaded successfully")
            except Exception as e:
                logger.warning(f"⚠️ FileParser not available: {e}")
                self._file_parser = None
        return self._file_parser

    # ================================================================
    #  MAIN ANALYSIS
    # ================================================================

    def analyze_project_comprehensive(
        self,
        project_data: Dict[str, Any],
        student_branch: str = "IT",
        student_semester: int = 5,
        uploaded_files: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Full project analysis.
        Returns dict with: extracted_skills, inferred_interests,
        complexity_score, file_analysis, etc.
        """
        # 1. Parse uploaded files
        file_analysis: Dict[str, Any] = {"total_files": 0, "successfully_parsed": 0}
        file_text = ""
        file_skills: List[str] = []

        if uploaded_files and self.file_parser:
            try:
                file_analysis = self.file_parser.parse_multiple(uploaded_files)
                file_text = file_analysis.get("aggregated_text", "")
                file_skills = file_analysis.get("aggregated_skills", [])
            except Exception as e:
                logger.warning(f"File parsing failed (non-critical): {e}")
        elif uploaded_files:
            # Fallback: just read text files directly
            file_analysis["total_files"] = len(uploaded_files)
            for uf in uploaded_files:
                try:
                    path = uf.get("path", "")
                    if path and os.path.exists(path):
                        ext = os.path.splitext(path)[1].lower()
                        if ext in {".txt", ".md", ".py", ".js", ".java", ".cpp", ".ts"}:
                            with open(path, "r", encoding="utf-8", errors="replace") as f:
                                content = f.read(200_000)
                            file_text += content + "\n"
                            file_analysis["successfully_parsed"] = file_analysis.get("successfully_parsed", 0) + 1
                except Exception as e:
                    logger.warning(f"Fallback file read failed: {e}")

        # 2. Extract skills from project metadata
        metadata_skills = self._extract_skills_from_metadata(project_data)

        # 3. Extract skills from descriptions + file text
        text_blob = " ".join([
            project_data.get("title", ""),
            project_data.get("description", ""),
            project_data.get("detailedDescription", ""),
            project_data.get("detailed_description", ""),
            file_text,
        ])
        text_skills = self._extract_skills_from_text(text_blob)

        # 4. Merge all skills
        all_skills = sorted(set(metadata_skills + text_skills + file_skills))

        # 5. Infer interests
        inferred_interests = self._infer_interests(project_data, all_skills, text_blob)

        # 6. Complexity
        complexity = self._calculate_complexity(project_data, all_skills, file_analysis)

        return {
            "extracted_skills": all_skills,
            "inferred_interests": inferred_interests,
            "complexity_score": complexity,
            "file_analysis": {
                "total_files": file_analysis.get("total_files", 0),
                "successfully_parsed": file_analysis.get("successfully_parsed", 0),
                "skills_from_files": file_skills,
                "file_details": [
                    {
                        "filename": r.get("filename", "unknown"),
                        "parse_success": r.get("parse_success", False),
                        "parse_method": r.get("parse_method", "none"),
                        "skills_found": r.get("skills_found", []),
                    }
                    for r in file_analysis.get("file_results", [])
                ],
            },
            "text_analyzed_length": len(text_blob),
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    # ================================================================
    #  SKILL EXTRACTION
    # ================================================================

    @staticmethod
    def _extract_skills_from_metadata(data: Dict[str, Any]) -> List[str]:
        skills: set = set()
        for key in ("programming_languages", "programmingLanguages",
                     "frameworks", "tools", "technologies"):
            for item in data.get(key, []):
                if isinstance(item, str) and item.strip():
                    skills.add(item.strip())
        return list(skills)

    @staticmethod
    def _extract_skills_from_text(text: str) -> List[str]:
        low = text.lower()
        skills: set = set()
        kw_map = {
            "machine learning": "Machine Learning", "deep learning": "Deep Learning",
            "neural network": "Neural Networks", "tensorflow": "TensorFlow",
            "pytorch": "PyTorch", "scikit-learn": "Scikit-learn", "keras": "Keras",
            "react": "React", "angular": "Angular", "vue": "Vue.js",
            "node.js": "Node.js", "express": "Express.js",
            "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
            "docker": "Docker", "kubernetes": "Kubernetes",
            "aws": "AWS", "azure": "Azure", "gcp": "GCP",
            "mongodb": "MongoDB", "postgresql": "PostgreSQL", "mysql": "MySQL",
            "redis": "Redis", "firebase": "Firebase",
            "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
            "java ": "Java", "c++": "C++", "golang": "Go", "rust": "Rust",
            "flutter": "Flutter", "react native": "React Native",
            "arduino": "Arduino", "raspberry pi": "Raspberry Pi",
            "nlp": "NLP", "computer vision": "Computer Vision",
            "data science": "Data Science", "data analysis": "Data Analysis",
            "rest api": "REST API", "graphql": "GraphQL",
            "ci/cd": "CI/CD", "terraform": "Terraform",
            "sql": "SQL", "pandas": "Pandas", "numpy": "NumPy",
            "opencv": "OpenCV", "mqtt": "MQTT", "iot": "IoT",
            "blockchain": "Blockchain", "microservices": "Microservices",
        }
        for kw, canon in kw_map.items():
            if kw in low:
                skills.add(canon)
        return list(skills)

    # ================================================================
    #  INTEREST INFERENCE
    # ================================================================

    def _infer_interests(
        self,
        data: Dict[str, Any],
        skills: List[str],
        text_blob: str,
    ) -> List[Dict[str, Any]]:
        low = text_blob.lower() + " " + " ".join(s.lower() for s in skills)
        results: List[Dict[str, Any]] = []

        for domain, info in INTEREST_PATTERNS.items():
            matches = [kw for kw in info["keywords"] if kw in low]
            if not matches:
                continue
            confidence = min(len(matches) / 4.0, 1.0)
            if confidence < 0.2:
                continue

            results.append({
                "domain": domain,
                "confidence": round(confidence, 2),
                "matched_keywords": matches[:8],
                "relatedSkills": info["related_skills"],
                "careerPaths": info["career_paths"],
                "industryRelevance": info["industry_relevance"],
                "source": "project_analysis",
                "keywords": matches[:5],
            })

        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results[:4]

    # ================================================================
    #  COMPLEXITY
    # ================================================================

    @staticmethod
    def _calculate_complexity(
        data: Dict[str, Any],
        skills: List[str],
        file_analysis: Dict[str, Any],
    ) -> float:
        score = 0.0
        tech = len(skills)
        score += min(tech * 0.06, 0.35)

        if data.get("is_team_project") or data.get("isTeamProject"):
            score += 0.12
            team = data.get("team_size") or data.get("teamSize") or 2
            score += min((team - 1) * 0.03, 0.1)

        desc_len = len(data.get("description", "") + data.get("detailedDescription", ""))
        score += min(desc_len / 1500.0, 0.15)

        if data.get("github_url") or data.get("githubUrl"):
            score += 0.1
        if data.get("demo_url") or data.get("demoUrl"):
            score += 0.1

        achievements = len(data.get("key_achievements") or data.get("keyAchievements") or [])
        score += min(achievements * 0.04, 0.12)

        files_parsed = file_analysis.get("successfully_parsed", 0)
        score += min(files_parsed * 0.03, 0.06)

        return round(min(score, 1.0), 2)

    # ================================================================
    #  CAREER / SKILL-GAP / NEXT-STEPS  (used by endpoints)
    # ================================================================

    def _map_career_paths(
        self,
        interests: List[Dict[str, Any]],
        honours_recommendations: List[Dict[str, Any]],
        student_branch: str,
    ) -> List[Dict[str, Any]]:
        interest_text = " ".join(
            i.get("domain", "").lower() for i in interests
        )
        paths: List[Dict[str, Any]] = []
        for title, info in CAREER_MAPPING.items():
            matches = [kw for kw in info["keywords"] if kw in interest_text]
            if not matches:
                continue
            score = min(len(matches) * 20, 95)
            paths.append({
                "title": title,
                "match_score": score,
                "salary_range": info["salary"],
                "growth_potential": info["growth"],
                "companies": info["companies"],
                "matched_keywords": matches,
            })
        paths.sort(key=lambda x: x["match_score"], reverse=True)
        if not paths:
            paths.append({
                "title": "Software Development Engineer",
                "match_score": 70,
                "salary_range": "₹6-18 LPA",
                "growth_potential": "High",
                "companies": ["TCS", "Infosys", "Wipro", "Google"],
                "matched_keywords": ["general"],
            })
        return paths[:5]

    def _analyze_skill_gaps(
        self,
        current_skills: List[str],
        career_paths: List[Dict[str, Any]],
        interests: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        current_lower = {s.lower() for s in current_skills}
        gaps: List[Dict[str, Any]] = []
        for path in career_paths[:2]:
            title = path.get("title", "")
            info = CAREER_MAPPING.get(title, {})
            required = info.get("keywords", [])
            missing = [kw for kw in required if kw not in current_lower]
            if missing:
                gaps.append({
                    "career": title,
                    "missing_skills": missing[:5],
                    "priority": "high" if len(missing) > 3 else "medium",
                })
        return gaps

    def _generate_next_steps(
        self,
        interests: List[Dict[str, Any]],
        elective_recommendations: List[Dict[str, Any]],
        skill_gaps: List[Dict[str, Any]],
        student_semester: int,
    ) -> List[Dict[str, Any]]:
        steps: List[Dict[str, Any]] = []
        if interests:
            top = interests[0] if isinstance(interests[0], dict) else {"domain": str(interests[0])}
            steps.append({
                "action": f"Build an advanced project in {top.get('domain', 'your interest area')}",
                "category": "Portfolio",
                "priority": "high",
                "deadline": "This semester",
                "details": "Strengthen your portfolio in your strongest interest area.",
            })
        if skill_gaps:
            gap = skill_gaps[0]
            steps.append({
                "action": f"Learn: {', '.join(gap['missing_skills'][:3])}",
                "category": "Skills",
                "priority": gap.get("priority", "medium"),
                "deadline": "Next 3 months",
                "details": f"Required for {gap.get('career', 'target career')}.",
            })
        if student_semester <= 4:
            steps.append({
                "action": "Focus on core subject fundamentals",
                "category": "Academic",
                "priority": "high",
                "deadline": "Current semester",
                "details": "Strong fundamentals improve elective and career prospects.",
            })
        if student_semester >= 4:
            steps.append({
                "action": "Choose electives aligned with your interests",
                "category": "Academic",
                "priority": "high",
                "deadline": "Next registration period",
                "details": "Elective choice impacts Honours eligibility and career path.",
            })
        return steps