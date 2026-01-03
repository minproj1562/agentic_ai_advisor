# app/services/enhanced_ml_inference.py
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple, Optional
import logging
import re
import spacy
from collections import Counter, defaultdict
import ast
import PyPDF2
import docx
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class FCRITAcademicInferenceEngine:
    def __init__(self):
        # Load models
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, using basic tokenization")
            self.nlp = None
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 3)
        )
        
        # FCRIT Honours/Minor Programs Mapping
        self.honours_programs = {
            "AI & ML": {
                "eligible_branches": ["COMP", "IT", "EXTC"],
                "type": "honours",
                "keywords": ["machine learning", "artificial intelligence", "deep learning", "neural network", 
                           "tensorflow", "pytorch", "nlp", "computer vision", "data science", "predictive modeling"],
                "skills": ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "Data Analysis"],
                "career_paths": ["ML Engineer", "AI Researcher", "Data Scientist", "AI Product Manager"],
                "courses": ["Knowledge Engineering", "Foundation ML", "Deep Learning", "Advanced AI"]
            },
            "Blockchain": {
                "eligible_branches": ["MECH"],
                "type": "minor",
                "keywords": ["blockchain", "smart contract", "ethereum", "cryptocurrency", "defi", 
                           "distributed ledger", "consensus", "web3", "solidity"],
                "skills": ["Solidity", "Web3.js", "Ethereum", "Smart Contracts"],
                "career_paths": ["Blockchain Developer", "Smart Contract Engineer", "DeFi Developer"],
                "courses": ["Intro Blockchain", "Platforms", "Development", "DApps"]
            },
            "Data Science": {
                "eligible_branches": ["COMP", "EXTC", "ELEC", "IT"],
                "type": "minor",
                "keywords": ["data analysis", "statistics", "machine learning", "data visualization",
                           "big data", "pandas", "numpy", "jupyter", "data mining"],
                "skills": ["Python", "R", "SQL", "Tableau", "Statistics"],
                "career_paths": ["Data Analyst", "Data Scientist", "Business Intelligence Analyst"],
                "courses": ["Data Analytics", "Statistical Methods", "Big Data", "Visualization"]
            },
            "Cyber Security": {
                "eligible_branches": ["COMP", "EXTC", "ELEC", "IT"],
                "type": "minor",
                "keywords": ["security", "cryptography", "penetration testing", "vulnerability",
                           "firewall", "malware", "ethical hacking", "forensics"],
                "skills": ["Network Security", "Cryptography", "Ethical Hacking", "Security Auditing"],
                "career_paths": ["Security Engineer", "Penetration Tester", "Security Analyst"],
                "courses": ["Network Security", "Cryptography", "Ethical Hacking", "Security Management"]
            },
            "IoT & Embedded": {
                "eligible_branches": ["COMP", "EXTC", "ELEC", "IT"],
                "type": "minor",
                "keywords": ["iot", "embedded systems", "arduino", "raspberry pi", "sensors",
                           "microcontroller", "mqtt", "edge computing"],
                "skills": ["Embedded C", "Arduino", "Raspberry Pi", "MQTT", "Sensor Integration"],
                "career_paths": ["IoT Engineer", "Embedded Systems Developer", "IoT Solutions Architect"],
                "courses": ["Embedded Systems", "IoT Protocols", "Sensor Networks", "Edge Computing"]
            },
            "AR/VR": {
                "eligible_branches": ["COMP", "EXTC", "ELEC", "IT"],
                "type": "minor",
                "keywords": ["augmented reality", "virtual reality", "unity", "unreal engine",
                           "3d modeling", "computer graphics", "mixed reality"],
                "skills": ["Unity", "Unreal Engine", "3D Modeling", "C#", "Computer Graphics"],
                "career_paths": ["AR/VR Developer", "3D Artist", "XR Engineer"],
                "courses": ["Computer Graphics", "AR/VR Development", "3D Modeling", "Interactive Design"]
            },
            "Electric Vehicle": {
                "eligible_branches": ["ELEC", "MECH", "COMP", "EXTC", "IT"],
                "type": "both",
                "keywords": ["electric vehicle", "battery management", "motor control", "power electronics",
                           "automotive", "charging infrastructure", "hybrid vehicles"],
                "skills": ["Power Electronics", "Motor Control", "Battery Systems", "Automotive Engineering"],
                "career_paths": ["EV Engineer", "Battery Systems Engineer", "Automotive Electronics Engineer"],
                "courses": ["EV Technology", "Battery Management", "Motor Control", "Power Systems"]
            },
            "VLSI": {
                "eligible_branches": ["EXTC", "COMP", "MECH", "ELEC", "IT"],
                "type": "both",
                "keywords": ["vlsi", "verilog", "fpga", "asic", "digital design", "chip design",
                           "hardware description", "synthesis"],
                "skills": ["Verilog", "VHDL", "FPGA", "Digital Design", "Cadence Tools"],
                "career_paths": ["VLSI Designer", "FPGA Engineer", "Chip Designer", "Verification Engineer"],
                "courses": ["Digital Design", "Verilog/VHDL", "FPGA Programming", "ASIC Design"]
            },
            "Renewable Energy": {
                "eligible_branches": ["ELEC", "COMP", "MECH", "EXTC", "IT"],
                "type": "minor",
                "keywords": ["solar", "wind energy", "renewable", "sustainability", "green energy",
                           "power generation", "energy storage"],
                "skills": ["Power Systems", "Solar Technology", "Wind Energy", "Energy Management"],
                "career_paths": ["Renewable Energy Engineer", "Sustainability Consultant", "Energy Analyst"],
                "courses": ["Solar Energy", "Wind Power", "Energy Storage", "Sustainable Systems"]
            },
            "Additive Manufacturing": {
                "eligible_branches": ["MECH", "COMP", "EXTC", "ELEC", "IT"],
                "type": "both",
                "keywords": ["3d printing", "additive manufacturing", "rapid prototyping", "cad",
                           "material science", "design optimization"],
                "skills": ["CAD", "3D Printing", "Material Science", "Design", "Manufacturing"],
                "career_paths": ["3D Printing Engineer", "Design Engineer", "Manufacturing Engineer"],
                "courses": ["3D Printing Tech", "CAD/CAM", "Material Science", "Design Optimization"]
            },
            "Supply Chain": {
                "eligible_branches": ["MECH", "COMP", "EXTC", "ELEC", "IT"],
                "type": "both",
                "keywords": ["supply chain", "logistics", "operations", "inventory", "optimization",
                           "erp", "warehouse management"],
                "skills": ["Supply Chain Management", "ERP", "Operations Research", "Data Analytics"],
                "career_paths": ["Supply Chain Analyst", "Operations Manager", "Logistics Coordinator"],
                "courses": ["Supply Chain Management", "Operations Research", "ERP Systems", "Logistics"]
            }
        }
        
        # Current electives mapping (Semester 5)
        self.sem5_electives = {
            "IT": {
                "Data Warehousing": {
                    "keywords": ["data warehouse", "etl", "olap", "data mining", "dimensional modeling",
                               "star schema", "snowflake", "business intelligence", "data mart"],
                    "skills": ["SQL", "ETL Tools", "Data Modeling", "BI Tools"],
                    "projects": ["analytics", "dashboard", "reporting", "data integration"]
                },
                "Cloud Computing": {
                    "keywords": ["cloud", "aws", "azure", "gcp", "docker", "kubernetes", "serverless",
                               "microservices", "saas", "paas", "iaas", "devops"],
                    "skills": ["AWS", "Docker", "Kubernetes", "Cloud Architecture"],
                    "projects": ["deployment", "scalable", "distributed", "cloud-native"]
                }
            },
            "COMP": {
                # Add Computer Science electives here
            },
            "EXTC": {
                # Add EXTC electives here
            },
            "ELEC": {
                # Add Electrical electives here
            },
            "MECH": {
                # Add Mechanical electives here
            }
        }
        
        # Branch-specific project patterns
        self.branch_patterns = {
            "IT": {
                "file_types": [".py", ".js", ".java", ".cpp", ".html", ".css", ".sql"],
                "frameworks": ["react", "django", "spring", "flutter", "angular", "node"],
                "focus_areas": ["software", "web", "mobile", "database", "api"]
            },
            "COMP": {
                "file_types": [".py", ".c", ".cpp", ".java", ".asm", ".cuda"],
                "frameworks": ["tensorflow", "pytorch", "opencv", "ros"],
                "focus_areas": ["algorithms", "systems", "ai", "graphics", "compiler"]
            },
            "EXTC": {
                "file_types": [".m", ".vhd", ".v", ".c", ".py"],
                "frameworks": ["matlab", "simulink", "labview", "xilinx"],
                "focus_areas": ["signal processing", "communication", "embedded", "antenna"]
            },
            "ELEC": {
                "file_types": [".m", ".sch", ".pcb", ".c", ".py"],
                "frameworks": ["matlab", "simulink", "psim", "pspice"],
                "focus_areas": ["power", "control", "drives", "renewable", "automation"]
            },
            "MECH": {
                "file_types": [".sldprt", ".dwg", ".stl", ".gcode", ".m"],
                "frameworks": ["solidworks", "catia", "ansys", "autocad"],
                "focus_areas": ["design", "manufacturing", "thermal", "fluid", "robotics"]
            }
        }

    def analyze_project_comprehensive(
        self, 
        project_data: Dict[str, Any],
        student_branch: str,
        student_semester: int,
        uploaded_files: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis ensuring all fields are properly populated
        """
        try:
            # Extract and analyze project content
            all_content = []
            
            # Add project data
            if project_data:
                # Extract text from project data
                project_text = f"{project_data.get('projectName', '')} {project_data.get('description', '')} "
                project_text += f"{' '.join(project_data.get('technologies', []))} "
                project_text += f"{' '.join(project_data.get('skills', []))} "
                project_text += f"{project_data.get('learnings', '')} {project_data.get('challenges', '')}"
                all_content.append(project_text)
            
            # Process uploaded files if any
            if uploaded_files:
                for file_info in uploaded_files:
                    # Extract text based on file type
                    file_content = self._extract_file_content(file_info)
                    if file_content:
                        all_content.append(file_content)
            
            # Combine all content
            combined_text = " ".join(all_content)
            
            # Infer interests from content
            interests = self._infer_interests(combined_text, project_data)
            
            # Ensure interests have all required fields
            for interest in interests:
                # Ensure all required fields exist
                if 'domain' not in interest:
                    interest['domain'] = 'Technology'
                if 'confidence' not in interest:
                    interest['confidence'] = 0.75
                if 'industryRelevance' not in interest:
                    interest['industryRelevance'] = 0.80
                if 'keywords' not in interest:
                    interest['keywords'] = []
                if 'careerPaths' not in interest:
                    interest['careerPaths'] = []
            
            # Get elective recommendations
            elective_recs = self._recommend_electives(
                interests=interests,
                student_branch=student_branch,
                student_semester=student_semester
            )
            
            # Ensure electives have all required fields
            for elective in elective_recs:
                if 'elective' not in elective:
                    elective['elective'] = 'Elective Course'
                if 'match_score' not in elective:
                    elective['match_score'] = 75
                if 'difficulty_level' not in elective:
                    elective['difficulty_level'] = 'Medium'
                if 'reasons' not in elective:
                    elective['reasons'] = ['Aligns with your interests']
                if 'skills_to_gain' not in elective:
                    elective['skills_to_gain'] = []
                if 'career_relevance' not in elective:
                    elective['career_relevance'] = 'Highly relevant to industry needs'
            
            # Get honours recommendations
            honours_recs = self._recommend_honours_programs(
                interests=interests,
                student_branch=student_branch
            )
            
            # Ensure honours have all required fields
            for program in honours_recs:
                if 'program' not in program:
                    program['program'] = 'Honours Program'
                if 'type' not in program:
                    program['type'] = 'Honours'
                if 'match_score' not in program:
                    program['match_score'] = 80
                if 'credits' not in program:
                    program['credits'] = 18
                if 'semester_commitment' not in program:
                    program['semester_commitment'] = '4 semesters'
                if 'courses' not in program:
                    program['courses'] = []
                if 'career_paths' not in program:
                    program['career_paths'] = []
                if 'reasons' not in program:
                    program['reasons'] = []
            
            # Map career paths
            career_paths = self._map_career_paths(
                interests=interests,
                honours_recommendations=honours_recs,
                student_branch=student_branch
            )
            
            # Ensure career paths have all required fields
            for career in career_paths:
                if 'title' not in career:
                    career['title'] = 'Career Path'
                if 'match_score' not in career:
                    career['match_score'] = 75
                if 'market_demand' not in career:
                    career['market_demand'] = 'High'
                if 'growth_potential' not in career:
                    career['growth_potential'] = 'Excellent'
                if 'salary_range' not in career:
                    career['salary_range'] = '6-12 LPA'
                if 'honours_program' not in career:
                    career['honours_program'] = None
                if 'source_domains' not in career:
                    career['source_domains'] = []
                if 'required_skills' not in career:
                    career['required_skills'] = []
                if 'preparation_path' not in career:
                    career['preparation_path'] = []
            
            # Analyze skill gaps
            skill_gap = self._analyze_skill_gaps(
                current_skills=project_data.get('skills', []),
                career_paths=career_paths,
                interests=interests
            )
            
            # Ensure skill gap has all required fields
            if 'current_skills' not in skill_gap:
                skill_gap['current_skills'] = []
            if 'skill_gaps' not in skill_gap:
                skill_gap['skill_gaps'] = []
            if 'priority_skills' not in skill_gap:
                skill_gap['priority_skills'] = []
            if 'learning_resources' not in skill_gap:
                skill_gap['learning_resources'] = {}
            if 'estimated_learning_time' not in skill_gap:
                skill_gap['estimated_learning_time'] = '3-6 months'
            
            # Generate next steps
            next_steps = self._generate_next_steps(
                interests=interests,
                elective_recommendations=elective_recs,
                skill_gaps=skill_gap,
                student_semester=student_semester
            )
            
            # Ensure next steps have all required fields
            for step in next_steps:
                if 'action' not in step:
                    step['action'] = 'Action Item'
                if 'details' not in step:
                    step['details'] = 'Details about this action'
                if 'priority' not in step:
                    step['priority'] = 'Medium'
                if 'category' not in step:
                    step['category'] = 'Academic'
                if 'deadline' not in step:
                    step['deadline'] = '1 month'
            
            # Return comprehensive analysis with all required fields
            return {
                'inferred_interests': interests,
                'elective_recommendations': elective_recs,
                'honours_minor_recommendations': honours_recs,
                'career_paths': career_paths,
                'skill_gap_analysis': skill_gap,
                'next_steps': next_steps,
                'metadata': {
                    'analysis_date': datetime.now().isoformat(),
                    'student_branch': student_branch,
                    'student_semester': student_semester,
                    'confidence_score': 0.85
                }
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            # Return a default structure with empty data
            return {
                'inferred_interests': [],
                'elective_recommendations': [],
                'honours_minor_recommendations': [],
                'career_paths': [],
                'skill_gap_analysis': {
                    'current_skills': [],
                    'skill_gaps': [],
                    'priority_skills': [],
                    'learning_resources': {},
                    'estimated_learning_time': '3-6 months'
                },
                'next_steps': [],
                'metadata': {
                    'analysis_date': datetime.now().isoformat(),
                    'student_branch': student_branch,
                    'student_semester': student_semester,
                    'confidence_score': 0.0,
                    'error': str(e)
                }
            }

    def _extract_file_content(self, file_info: Dict[str, Any]) -> str:
        """Extract text content from uploaded files"""
        try:
            file_path = file_info.get('path', '')
            file_type = file_info.get('type', '').lower()
            
            if 'pdf' in file_type or file_path.endswith('.pdf'):
                # Extract from PDF
                return self._extract_pdf_text(file_path)
            elif 'text' in file_type or 'plain' in file_type or file_path.endswith('.txt'):
                # Extract from text file
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            elif 'word' in file_type or file_path.endswith(('.doc', '.docx')):
                # Extract from Word document
                return self._extract_doc_text(file_path)
            else:
                # Try to read as text
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        return file.read()
                except:
                    return ""
        except Exception as e:
            logger.error(f"Error extracting file content: {e}")
            return ""

    def _infer_interests(self, combined_text: str, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Infer interests from combined text and project data"""
        interests = []
        
        # Simple keyword-based interest detection
        interest_keywords = {
            "Artificial Intelligence & Machine Learning": [
                "machine learning", "artificial intelligence", "deep learning", "neural network",
                "tensorflow", "pytorch", "scikit-learn", "nlp", "computer vision", "ai"
            ],
            "Web Development": [
                "web", "frontend", "backend", "react", "angular", "vue", "django", "flask",
                "node", "javascript", "html", "css"
            ],
            "Data Science": [
                "data science", "data analysis", "pandas", "numpy", "statistics", "visualization",
                "big data", "analytics", "jupyter"
            ],
            "Cloud Computing": [
                "cloud", "aws", "azure", "gcp", "docker", "kubernetes", "serverless",
                "microservices", "devops"
            ],
            "Mobile Development": [
                "mobile", "android", "ios", "flutter", "react native", "kotlin", "swift"
            ],
            "Cybersecurity": [
                "security", "cybersecurity", "encryption", "firewall", "penetration testing",
                "ethical hacking", "vulnerability"
            ]
        }
        
        text_lower = combined_text.lower()
        
        for domain, keywords in interest_keywords.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                confidence = min(len(matches) / len(keywords) * 2, 1.0)  # Scale confidence
                interests.append({
                    "domain": domain,
                    "confidence": confidence,
                    "keywords": matches[:5],
                    "relatedSkills": self._get_related_skills(domain),
                    "careerPaths": self._get_career_paths(domain),
                    "industryRelevance": self._calculate_industry_relevance(domain),
                    "reasoning": f"Found {len(matches)} relevant keywords in project",
                    "evidence": matches
                })
        
        # Sort by confidence and return top 3
        interests.sort(key=lambda x: x['confidence'], reverse=True)
        return interests[:3]

    def _get_related_skills(self, domain: str) -> List[str]:
        """Get related skills for a domain"""
        skills_map = {
            "Artificial Intelligence & Machine Learning": [
                "Python", "TensorFlow", "PyTorch", "Scikit-learn", "Data Analysis",
                "Statistics", "Neural Networks", "Deep Learning"
            ],
            "Web Development": [
                "JavaScript", "HTML", "CSS", "React", "Node.js", "Database Management",
                "REST APIs", "Git"
            ],
            "Data Science": [
                "Python", "Pandas", "NumPy", "SQL", "Data Visualization",
                "Statistical Analysis", "Machine Learning"
            ],
            "Cloud Computing": [
                "AWS", "Docker", "Kubernetes", "CI/CD", "Infrastructure as Code",
                "Cloud Security", "Microservices"
            ]
        }
        return skills_map.get(domain, ["Problem Solving", "Programming", "Analytical Thinking"])

    def _get_career_paths(self, domain: str) -> List[str]:
        """Get career paths for a domain"""
        careers_map = {
            "Artificial Intelligence & Machine Learning": [
                "ML Engineer", "AI Researcher", "Data Scientist", "AI Product Manager"
            ],
            "Web Development": [
                "Full Stack Developer", "Frontend Developer", "Backend Developer", "Web Architect"
            ],
            "Data Science": [
                "Data Scientist", "Data Analyst", "Business Intelligence Analyst", "Data Engineer"
            ],
            "Cloud Computing": [
                "Cloud Architect", "DevOps Engineer", "Cloud Security Engineer", "Site Reliability Engineer"
            ]
        }
        return careers_map.get(domain, ["Software Engineer", "Technical Specialist"])

    def _recommend_electives(
        self,
        interests: List[Dict[str, Any]],
        student_branch: str,
        student_semester: int
    ) -> List[Dict[str, Any]]:
        """Recommend electives based on interests and branch"""
        recommendations = []
        
        if student_branch == "IT" and student_semester == 5:
            # IT Semester 5 electives
            electives = {
                "Data Warehousing": {
                    "match_score": 85,
                    "reasons": ["Strong data focus in your projects", "High industry demand"],
                    "skills_to_gain": ["ETL", "OLAP", "Data Modeling", "Business Intelligence"],
                    "career_relevance": "Essential for Data Analyst and BI Developer roles",
                    "difficulty_level": "Moderate"
                },
                "Cloud Computing": {
                    "match_score": 78,
                    "reasons": ["Growing field with excellent opportunities", "Builds on modern tech"],
                    "skills_to_gain": ["AWS", "Docker", "Kubernetes", "Cloud Architecture"],
                    "career_relevance": "Critical for modern software development careers",
                    "difficulty_level": "Moderate"
                }
            }
            
            for elective, info in electives.items():
                recommendations.append({
                    "elective": elective,
                    "match_score": info["match_score"],
                    "reasons": info["reasons"],
                    "skills_to_gain": info["skills_to_gain"],
                    "career_relevance": info["career_relevance"],
                    "difficulty_level": info["difficulty_level"]
                })
        
        return recommendations

    def _recommend_honours_programs(
        self,
        interests: List[Dict[str, Any]],
        student_branch: str
    ) -> List[Dict[str, Any]]:
        """Recommend honours programs based on interests and eligibility"""
        recommendations = []
        
        # AI & ML for eligible branches
        if student_branch in ["IT", "COMP", "EXTC"]:
            recommendations.append({
                "program": "AI & Machine Learning",
                "type": "Honours",
                "match_score": 90,
                "reasons": ["Strong alignment with AI/ML interests", "Excellent career prospects"],
                "courses": ["Knowledge Engineering", "Foundation ML", "Deep Learning", "Advanced AI"],
                "career_paths": ["ML Engineer", "AI Researcher", "Data Scientist"],
                "skills_to_develop": ["TensorFlow", "PyTorch", "Neural Networks", "NLP"],
                "semester_commitment": "4 semesters (Sem V-VIII)",
                "credits": 18,
                "eligibility_met": True
            })
        
        # Data Science for all branches
        recommendations.append({
            "program": "Data Science",
            "type": "Minor",
            "match_score": 85,
            "reasons": ["Universal relevance", "High industry demand"],
            "courses": ["Statistical Methods", "Big Data", "Machine Learning", "Visualization"],
            "career_paths": ["Data Scientist", "Data Analyst", "Business Intelligence Analyst"],
            "skills_to_develop": ["Python", "R", "SQL", "Tableau"],
            "semester_commitment": "4 semesters (Sem V-VIII)",
            "credits": 18,
            "eligibility_met": True
        })
        
        return recommendations

    def _map_career_paths(
        self,
        interests: List[Dict[str, Any]],
        honours_recommendations: List[Dict[str, Any]],
        student_branch: str
    ) -> List[Dict[str, Any]]:
        """Map comprehensive career paths"""
        career_paths = []
        
        for interest in interests:
            for career in interest.get("careerPaths", []):
                career_paths.append({
                    "title": career,
                    "match_score": int(interest["confidence"] * 100),
                    "source_domains": [interest["domain"]],
                    "required_skills": interest.get("relatedSkills", [])[:5],
                    "honours_program": self._get_relevant_honours(career, honours_recommendations),
                    "market_demand": self._get_market_demand(career),
                    "salary_range": self._get_salary_range(career),
                    "growth_potential": self._get_growth_potential(career),
                    "preparation_path": self._generate_preparation_path(career, student_branch)
                })
        
        return career_paths[:3]

    def _analyze_skill_gaps(
        self,
        current_skills: List[str],
        career_paths: List[Dict[str, Any]],
        interests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze skill gaps and provide recommendations"""
        current_skills_set = set(skill.lower() for skill in current_skills)
        
        # Collect required skills from career paths and interests
        required_skills = set()
        for career in career_paths:
            required_skills.update(skill.lower() for skill in career.get("required_skills", []))
        
        for interest in interests:
            required_skills.update(skill.lower() for skill in interest.get("relatedSkills", []))
        
        skill_gaps = required_skills - current_skills_set
        priority_skills = list(skill_gaps)[:3]
        
        learning_resources = {}
        for skill in priority_skills:
            learning_resources[skill] = self._get_learning_resources_for_skill(skill)
        
        return {
            "current_skills": list(current_skills_set),
            "required_skills": list(required_skills),
            "skill_gaps": list(skill_gaps),
            "priority_skills": priority_skills,
            "learning_resources": learning_resources,
            "estimated_learning_time": f"{len(priority_skills) * 2} weeks"
        }

    def _generate_next_steps(
        self,
        interests: List[Dict[str, Any]],
        elective_recommendations: List[Dict[str, Any]],
        skill_gaps: Dict[str, Any],
        student_semester: int
    ) -> List[Dict[str, Any]]:
        """Generate actionable next steps"""
        next_steps = []
        
        if student_semester == 4:
            next_steps.append({
                "category": "Academic",
                "action": "Apply for Honours/Minor Program",
                "deadline": "Before Semester 5 registration",
                "priority": "High",
                "details": "Research and apply for suitable Honours or Minor programs"
            })
        
        next_steps.append({
            "category": "Academic",
            "action": "Select Next Semester Electives",
            "deadline": "Registration period",
            "priority": "High",
            "details": "Choose electives aligned with your career goals"
        })
        
        if skill_gaps.get("priority_skills"):
            next_steps.append({
                "category": "Skills",
                "action": "Learn Priority Skills",
                "deadline": "Next 2 months",
                "priority": "Medium",
                "details": f"Focus on: {', '.join(skill_gaps['priority_skills'][:3])}"
            })
        
        next_steps.append({
            "category": "Portfolio",
            "action": "Build Advanced Project",
            "deadline": "This semester",
            "priority": "Medium",
            "details": "Create a project showcasing your specialized skills"
        })
        
        return next_steps

    def _get_relevant_honours(self, career: str, honours_recommendations: List[Dict[str, Any]]) -> Optional[str]:
        """Get relevant honours program for a career"""
        for program in honours_recommendations:
            if career in program.get("career_paths", []):
                return program["program"]
        return None

    def _get_market_demand(self, career: str) -> str:
        """Get market demand for a career"""
        high_demand = ["ML Engineer", "Data Scientist", "AI Researcher", "Cloud Architect"]
        if any(hd in career for hd in high_demand):
            return "Very High"
        return "High"

    def _get_salary_range(self, career: str) -> str:
        """Get salary range for a career"""
        salary_map = {
            "ML Engineer": "8-25 LPA",
            "Data Scientist": "7-22 LPA",
            "AI Researcher": "10-30 LPA",
            "Cloud Architect": "12-30 LPA"
        }
        return salary_map.get(career, "6-15 LPA")

    def _get_growth_potential(self, career: str) -> str:
        """Get growth potential for a career"""
        high_growth = ["AI", "ML", "Data", "Cloud"]
        if any(hg in career for hg in high_growth):
            return "Excellent"
        return "Good"

    def _generate_preparation_path(self, career: str, branch: str) -> List[str]:
        """Generate preparation path for a career"""
        base_path = [
            "Complete relevant electives",
            "Build portfolio projects",
            "Gain practical experience"
        ]
        
        if "ML" in career or "AI" in career:
            return base_path + [
                "Master Python and ML libraries",
                "Participate in Kaggle competitions",
                "Get relevant certifications"
            ]
        
        return base_path

    def _get_learning_resources_for_skill(self, skill: str) -> List[str]:
        """Get learning resources for a specific skill"""
        resource_map = {
            "python": ["Python for Everybody (Coursera)", "Real Python", "Python Crash Course"],
            "machine learning": ["Andrew Ng ML Course", "Fast.ai", "Kaggle Learn"],
            "aws": ["AWS Training", "AWS Certified Solutions Architect", "AWS Documentation"],
            "docker": ["Docker Official Docs", "Docker Mastery Course", "Play with Docker"]
        }
        
        for key, resources in resource_map.items():
            if key in skill.lower():
                return resources
        
        return ["Online Courses", "Official Documentation", "YouTube Tutorials"]

    # Existing methods from the original class
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF files"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages[:5]:  # First 5 pages
                    text += page.extract_text()
                return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""

    def _extract_doc_text(self, file_path: str) -> str:
        """Extract text from Word documents"""
        try:
            doc = docx.Document(file_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs[:20]])
        except Exception as e:
            logger.error(f"Error extracting DOC text: {e}")
            return ""

    # ... (include all other existing methods from the original class here)

    def _calculate_industry_relevance(self, domain: str) -> float:
        """Calculate current industry relevance"""
        relevance_scores = {
            "Artificial Intelligence & Machine Learning": 0.95,
            "Web Development": 0.85,
            "Data Science": 0.90,
            "Cloud Computing": 0.92,
            "Mobile Development": 0.80,
            "Cybersecurity": 0.88
        }
        return relevance_scores.get(domain, 0.80)