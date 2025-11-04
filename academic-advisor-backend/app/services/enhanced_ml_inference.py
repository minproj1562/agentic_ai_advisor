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
import pypdf2
import docx
from pathlib import Path

logger = logging.getLogger(__name__)

class FCRITAcademicInferenceEngine:
    def __init__(self):
        # Load models
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.nlp = spacy.load("en_core_web_sm")
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
        Comprehensive analysis including interest inference, elective recommendations,
        honours/minor suggestions, and career path mapping
        """
        
        # Extract all features
        text_features = self._extract_text_features(project_data)
        code_features = self._analyze_uploaded_files(uploaded_files) if uploaded_files else {}
        tech_stack = self._analyze_technical_stack(project_data)
        
        # Infer interests
        interests = self._infer_interests_enhanced(
            text_features, 
            code_features, 
            tech_stack,
            student_branch
        )
        
        # Recommend electives
        elective_recommendations = self._recommend_electives(
            interests,
            student_branch,
            student_semester,
            project_data
        )
        
        # Recommend Honours/Minor programs
        honours_recommendations = self._recommend_honours_programs(
            interests,
            student_branch,
            project_data,
            tech_stack
        )
        
        # Map career paths
        career_paths = self._map_career_paths(
            interests,
            honours_recommendations,
            student_branch
        )
        
        # Generate comprehensive report
        return {
            "inferred_interests": interests,
            "elective_recommendations": elective_recommendations,
            "honours_minor_recommendations": honours_recommendations,
            "career_paths": career_paths,
            "skill_gap_analysis": self._analyze_skill_gaps(interests, tech_stack, student_branch),
            "next_steps": self._generate_next_steps(interests, honours_recommendations, student_semester)
        }
    
    def _analyze_uploaded_files(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze uploaded project files, especially code files"""
        features = {
            "code_complexity": 0,
            "languages_detected": [],
            "frameworks_detected": [],
            "design_patterns": [],
            "code_quality_indicators": [],
            "domain_specific_content": []
        }
        
        for file_info in files:
            file_path = file_info.get('path', '')
            file_type = Path(file_path).suffix.lower()
            
            if file_type in ['.py', '.js', '.java', '.cpp', '.c']:
                # Analyze code files
                code_analysis = self._analyze_code_file(file_path, file_type)
                features['languages_detected'].append(file_type[1:])
                features['code_complexity'] += code_analysis.get('complexity', 0)
                features['frameworks_detected'].extend(code_analysis.get('frameworks', []))
                
            elif file_type == '.pdf':
                # Extract text from PDF
                pdf_text = self._extract_pdf_text(file_path)
                features['domain_specific_content'].append(pdf_text[:500])
                
            elif file_type in ['.doc', '.docx']:
                # Extract text from Word documents
                doc_text = self._extract_doc_text(file_path)
                features['domain_specific_content'].append(doc_text[:500])
        
        return features
    
    def _analyze_code_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Analyze source code files for patterns and complexity"""
        analysis = {
            "complexity": 0,
            "frameworks": [],
            "patterns": [],
            "quality_score": 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                
            # Language-specific analysis
            if file_type == '.py':
                analysis['frameworks'] = self._detect_python_frameworks(code)
                analysis['complexity'] = self._calculate_python_complexity(code)
            elif file_type in ['.js', '.jsx']:
                analysis['frameworks'] = self._detect_js_frameworks(code)
            elif file_type == '.java':
                analysis['frameworks'] = self._detect_java_frameworks(code)
                
            # Common patterns
            analysis['patterns'] = self._detect_design_patterns(code)
            analysis['quality_score'] = self._assess_code_quality(code)
            
        except Exception as e:
            logger.error(f"Error analyzing code file: {e}")
        
        return analysis
    
    def _detect_python_frameworks(self, code: str) -> List[str]:
        """Detect Python frameworks and libraries used"""
        frameworks = []
        framework_imports = {
            'django': ['from django', 'import django'],
            'flask': ['from flask', 'import flask'],
            'tensorflow': ['import tensorflow', 'from tensorflow'],
            'pytorch': ['import torch', 'from torch'],
            'pandas': ['import pandas', 'from pandas'],
            'numpy': ['import numpy', 'from numpy'],
            'scikit-learn': ['from sklearn', 'import sklearn'],
            'fastapi': ['from fastapi', 'import fastapi'],
            'opencv': ['import cv2', 'from cv2']
        }
        
        code_lower = code.lower()
        for framework, patterns in framework_imports.items():
            if any(pattern in code_lower for pattern in patterns):
                frameworks.append(framework)
        
        return frameworks
    
    def _calculate_python_complexity(self, code: str) -> int:
        """Calculate code complexity for Python files"""
        complexity = 0
        
        try:
            tree = ast.parse(code)
            
            # Count different node types
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity += 2
                elif isinstance(node, ast.ClassDef):
                    complexity += 3
                elif isinstance(node, (ast.For, ast.While)):
                    complexity += 1
                elif isinstance(node, ast.If):
                    complexity += 1
        except:
            # If parsing fails, estimate based on lines
            complexity = len(code.split('\n')) // 20
        
        return min(complexity, 100)  # Cap at 100
    
    def _recommend_electives(
        self,
        interests: List[Dict[str, Any]],
        student_branch: str,
        student_semester: int,
        project_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Recommend electives based on project analysis"""
        recommendations = []
        
        # Get available electives for branch and semester
        if student_semester == 5 and student_branch in self.sem5_electives:
            electives = self.sem5_electives[student_branch]
            
            for elective_name, elective_info in electives.items():
                score = 0
                reasons = []
                
                # Check keyword matches
                project_text = self._extract_text_features(project_data).lower()
                keyword_matches = sum(1 for kw in elective_info['keywords'] if kw in project_text)
                
                if keyword_matches > 0:
                    score += keyword_matches * 10
                    reasons.append(f"Project aligns with {elective_name} concepts")
                
                # Check skill overlap
                project_skills = set(project_data.get('programmingLanguages', []) + 
                               project_data.get('frameworks', []) + 
                               project_data.get('tools', []))
                skill_overlap = len(project_skills & set(elective_info['skills']))
                
                if skill_overlap > 0:
                    score += skill_overlap * 15
                    reasons.append(f"Your skills match {skill_overlap} requirements")
                
                # Check interest alignment
                for interest in interests[:3]:
                    if any(kw in interest['domain'].lower() for kw in elective_info['keywords']):
                        score += 20
                        reasons.append(f"Aligns with your {interest['domain']} interest")
                        break
                
                if score > 0:
                    recommendations.append({
                        "elective": elective_name,
                        "match_score": min(score, 100),
                        "reasons": reasons,
                        "skills_to_gain": elective_info['skills'],
                        "career_relevance": self._get_elective_career_relevance(elective_name),
                        "difficulty_level": self._estimate_difficulty(elective_info, project_data)
                    })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        return recommendations[:3]
    
    def _recommend_honours_programs(
        self,
        interests: List[Dict[str, Any]],
        student_branch: str,
        project_data: Dict[str, Any],
        tech_stack: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """Recommend Honours/Minor programs based on eligibility and interests"""
        recommendations = []
        
        for program_name, program_info in self.honours_programs.items():
            # Check eligibility
            if student_branch not in program_info['eligible_branches']:
                continue
            
            score = 0
            reasons = []
            program_type = "Honours" if student_branch in program_info['eligible_branches'][:1] else "Minor"
            
            # Calculate interest alignment
            for interest in interests:
                keyword_overlap = len(set(interest['keywords']) & set(program_info['keywords']))
                if keyword_overlap > 0:
                    score += keyword_overlap * 5
                    
            # Check technical stack alignment
            all_tech = tech_stack['languages'] + tech_stack['frameworks'] + tech_stack['tools']
            tech_match = len(set(all_tech) & set(program_info['skills']))
            
            if tech_match > 0:
                score += tech_match * 10
                reasons.append(f"Your technical skills align with {tech_match} program requirements")
            
            # Project type relevance
            project_type = project_data.get('projectType', '')
            if project_type in ['research', 'academic'] and 'research' in program_name.lower():
                score += 20
                reasons.append("Your research experience is valuable for this program")
            
            # Calculate career path alignment
            career_goals = project_data.get('careerGoals', [])
            career_match = len(set(career_goals) & set(program_info['career_paths']))
            if career_match > 0:
                score += career_match * 15
                reasons.append(f"Directly supports your career goal")
            
            if score > 20:  # Minimum threshold
                recommendations.append({
                    "program": program_name,
                    "type": program_type,
                    "match_score": min(score, 100),
                    "reasons": reasons,
                    "courses": program_info['courses'],
                    "career_paths": program_info['career_paths'],
                    "skills_to_develop": program_info['skills'],
                    "semester_commitment": "4 semesters (Sem V-VIII)",
                    "credits": 18,
                    "eligibility_met": True
                })
        
        # Add research option if applicable
        if self._should_recommend_research(interests, project_data):
            recommendations.append({
                "program": "Honours in Research",
                "type": "Research",
                "match_score": 85,
                "reasons": [
                    "Strong research potential demonstrated in projects",
                    "Opportunity to work with IIT/TIFR",
                    "Path to journal publication or patent"
                ],
                "courses": ["Research Methodology", "Literature Review", "Research Project"],
                "career_paths": ["Research Scientist", "PhD Candidate", "R&D Engineer"],
                "skills_to_develop": ["Research Methods", "Academic Writing", "Data Analysis"],
                "semester_commitment": "4 semesters (Sem V-VIII)",
                "credits": 18,
                "eligibility_met": True
            })
        
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        return recommendations[:3]
    
    def _map_career_paths(
        self,
        interests: List[Dict[str, Any]],
        honours_recommendations: List[Dict[str, Any]],
        student_branch: str
    ) -> List[Dict[str, Any]]:
        """Map comprehensive career paths based on all analysis"""
        career_paths = []
        career_scores = defaultdict(float)
        career_details = {}
        
        # Aggregate from interests
        for interest in interests:
            for career in interest.get('career_paths', []):
                career_scores[career] += interest['confidence'] * 30
                if career not in career_details:
                    career_details[career] = {
                        "source_domains": [interest['domain']],
                        "required_skills": interest.get('related_skills', []),
                        "market_demand": self._get_market_demand(career)
                    }
                else:
                    career_details[career]['source_domains'].append(interest['domain'])
        
        # Aggregate from honours recommendations
        for recommendation in honours_recommendations:
            for career in recommendation.get('career_paths', []):
                career_scores[career] += recommendation['match_score'] * 0.5
                if career in career_details:
                    career_details[career]['honours_program'] = recommendation['program']
                else:
                    career_details[career] = {
                        "source_domains": [],
                        "required_skills": recommendation.get('skills_to_develop', []),
                        "honours_program": recommendation['program'],
                        "market_demand": self._get_market_demand(career)
                    }
        
        # Create final career path objects
        for career, score in career_scores.items():
            details = career_details[career]
            career_paths.append({
                "title": career,
                "match_score": min(score, 100),
                "source_domains": list(set(details['source_domains'])),
                "required_skills": list(set(details['required_skills']))[:6],
                "honours_program": details.get('honours_program'),
                "market_demand": details['market_demand'],
                "salary_range": self._get_salary_range(career),
                "growth_potential": self._get_growth_potential(career),
                "preparation_path": self._generate_preparation_path(career, student_branch)
            })
        
        career_paths.sort(key=lambda x: x['match_score'], reverse=True)
        return career_paths[:5]
    
    def _analyze_skill_gaps(
        self,
        interests: List[Dict[str, Any]],
        tech_stack: Dict[str, List[str]],
        student_branch: str
    ) -> Dict[str, Any]:
        """Identify skill gaps and learning recommendations"""
        current_skills = set(
            tech_stack.get('languages', []) + 
            tech_stack.get('frameworks', []) + 
            tech_stack.get('tools', [])
        )
        
        required_skills = set()
        for interest in interests[:3]:
            required_skills.update(interest.get('related_skills', []))
        
        skill_gaps = required_skills - current_skills
        
        return {
            "current_skills": list(current_skills),
            "required_skills": list(required_skills),
            "skill_gaps": list(skill_gaps),
            "priority_skills": self._prioritize_skills(skill_gaps, student_branch),
            "learning_resources": self._get_learning_resources(skill_gaps),
            "estimated_learning_time": f"{len(skill_gaps) * 2} weeks"
        }
    
    def _generate_next_steps(
        self,
        interests: List[Dict[str, Any]],
        honours_recommendations: List[Dict[str, Any]],
        student_semester: int
    ) -> List[Dict[str, Any]]:
        """Generate actionable next steps for the student"""
        next_steps = []
        
        # Academic decisions
        if student_semester == 4:
            next_steps.append({
                "category": "Academic",
                "action": "Choose Honours/Minor Program",
                "deadline": "Before Semester 5 registration",
                "priority": "High",
                "details": f"Consider {honours_recommendations[0]['program']}" if honours_recommendations else "Review available options"
            })
        
        if student_semester >= 5:
            next_steps.append({
                "category": "Academic",
                "action": "Select Electives",
                "deadline": "Next semester registration",
                "priority": "High",
                "details": "Choose electives aligned with your interests and career goals"
            })
        
        # Skill development
        next_steps.append({
            "category": "Skills",
            "action": "Learn Priority Technologies",
            "deadline": "Next 3 months",
            "priority": "Medium",
            "details": f"Focus on {', '.join(interests[0]['related_skills'][:3])}" if interests else "Identify key skills"
        })
        
        # Project enhancement
        next_steps.append({
            "category": "Portfolio",
            "action": "Develop Advanced Project",
            "deadline": "This semester",
            "priority": "Medium",
            "details": f"Build a project in {interests[0]['domain']}" if interests else "Choose a specialization"
        })
        
        return next_steps
    
    def _infer_interests_enhanced(
        self,
        text_features: str,
        code_features: Dict[str, Any],
        tech_stack: Dict[str, List[str]],
        student_branch: str
    ) -> List[Dict[str, Any]]:
        """Enhanced interest inference considering branch-specific patterns"""
        interests = []
        
        # Branch-specific weighting
        branch_weights = self._get_branch_weights(student_branch)
        
        # Combine all features
        all_keywords = self._extract_keywords(text_features)
        
        # Add code-based keywords if available
        if code_features:
            all_keywords.extend(code_features.get('frameworks_detected', []))
            all_keywords.extend(code_features.get('languages_detected', []))
        
        # Calculate domain scores with branch-specific adjustments
        for domain, info in self.honours_programs.items():
            score = 0
            evidence = []
            
            # Text and keyword matching
            keyword_matches = len(set(all_keywords) & set(info['keywords']))
            if keyword_matches > 0:
                score += keyword_matches * 5
                evidence.append(f"Keywords: {keyword_matches} matches")
            
            # Technical stack matching
            tech_matches = len(set(tech_stack['frameworks']) & set(info['skills']))
            if tech_matches > 0:
                score += tech_matches * 10
                evidence.append(f"Tech stack: {tech_matches} matches")
            
            # Apply branch-specific weight
            if domain in branch_weights:
                score *= branch_weights[domain]
            
            if score > 10:
                interests.append({
                    "domain": domain,
                    "confidence": min(score / 100, 1.0),
                    "keywords": list(set(all_keywords) & set(info['keywords']))[:8],
                    "related_skills": info['skills'][:6],
                    "career_paths": info['career_paths'][:3],
                    "industry_relevance": self._calculate_industry_relevance(domain),
                    "reasoning": f"Based on {', '.join(evidence)}",
                    "evidence": evidence
                })
        
        interests.sort(key=lambda x: x['confidence'], reverse=True)
        return interests[:5]
    
    def _get_branch_weights(self, branch: str) -> Dict[str, float]:
        """Get branch-specific domain weights"""
        weights = {
            "IT": {
                "AI & ML": 1.2,
                "Data Science": 1.2,
                "Cyber Security": 1.1,
                "Blockchain": 0.8,
                "IoT & Embedded": 0.9,
                "AR/VR": 1.0
            },
            "COMP": {
                "AI & ML": 1.3,
                "Data Science": 1.1,
                "Cyber Security": 1.2,
                "IoT & Embedded": 0.9,
                "AR/VR": 1.0
            },
            "EXTC": {
                "IoT & Embedded": 1.3,
                "VLSI": 1.3,
                "AI & ML": 0.9,
                "AR/VR": 0.8
            },
            "ELEC": {
                "Electric Vehicle": 1.3,
                "Renewable Energy": 1.3,
                "IoT & Embedded": 1.1,
                "Power Electronics": 1.2
            },
            "MECH": {
                "Additive Manufacturing": 1.3,
                "Electric Vehicle": 1.2,
                "Supply Chain": 1.2,
                "Aeronautical": 1.1
            }
        }
        return weights.get(branch, {})
    
    def _should_recommend_research(
        self,
        interests: List[Dict[str, Any]],
        project_data: Dict[str, Any]
    ) -> bool:
        """Determine if Honours in Research should be recommended"""
        indicators = 0
        
        # Check for research indicators
        if project_data.get('projectType') == 'research':
            indicators += 2
        
        # Check for academic achievements
        achievements = project_data.get('keyAchievements', [])
        research_keywords = ['published', 'paper', 'conference', 'journal', 'patent', 'research']
        
        for achievement in achievements:
            if any(kw in achievement.lower() for kw in research_keywords):
                indicators += 1
        
        # Check interest confidence levels
        if interests and interests[0]['confidence'] > 0.8:
            indicators += 1
        
        return indicators >= 2
    
    def _calculate_industry_relevance(self, domain: str) -> float:
        """Calculate current industry relevance"""
        # This would ideally fetch from a real-time data source
        relevance_scores = {
            "AI & ML": 0.98,
            "Data Science": 0.95,
            "Cyber Security": 0.96,
            "Cloud Computing": 0.94,
            "Electric Vehicle": 0.92,
            "Blockchain": 0.88,
            "IoT & Embedded": 0.90,
            "AR/VR": 0.87,
            "Renewable Energy": 0.91,
            "VLSI": 0.85,
            "Additive Manufacturing": 0.83,
            "Supply Chain": 0.89
        }
        return relevance_scores.get(domain, 0.80)
    
    def _get_market_demand(self, career: str) -> str:
        """Get market demand for a career"""
        high_demand_careers = [
            "ML Engineer", "Data Scientist", "Cloud Architect", "DevOps Engineer",
            "Security Engineer", "Full Stack Developer", "AI Researcher"
        ]
        
        if any(hd in career for hd in high_demand_careers):
            return "Very High"
        elif "Engineer" in career or "Developer" in career:
            return "High"
        else:
            return "Moderate"
    
    def _get_salary_range(self, career: str) -> str:
        """Get typical salary range for career"""
        # These are approximate ranges for Indian market (in LPA)
        salary_ranges = {
            "ML Engineer": "8-25 LPA",
            "Data Scientist": "7-22 LPA",
            "AI Researcher": "10-30 LPA",
            "Full Stack Developer": "5-18 LPA",
            "Security Engineer": "6-20 LPA",
            "DevOps Engineer": "6-18 LPA",
            "IoT Engineer": "5-15 LPA",
            "VLSI Designer": "6-18 LPA",
            "Blockchain Developer": "7-20 LPA"
        }
        
        for career_key, salary in salary_ranges.items():
            if career_key in career:
                return salary
        
        return "5-15 LPA"  # Default range
    
    def _get_growth_potential(self, career: str) -> str:
        """Assess career growth potential"""
        high_growth = ["AI", "ML", "Data", "Cloud", "Security", "Blockchain"]
        
        if any(field in career for field in high_growth):
            return "Excellent"
        elif "Engineer" in career or "Developer" in career:
            return "Good"
        else:
            return "Moderate"
    
    def _generate_preparation_path(self, career: str, branch: str) -> List[str]:
        """Generate step-by-step preparation path"""
        path = []
        
        # Common steps
        path.append("Complete relevant electives in upcoming semesters")
        path.append("Choose appropriate Honours/Minor program")
        
        # Career-specific steps
        if "ML" in career or "AI" in career or "Data" in career:
            path.append("Master Python and key ML libraries")
            path.append("Complete online courses on Coursera/Udacity")
            path.append("Participate in Kaggle competitions")
        elif "Security" in career:
            path.append("Learn ethical hacking and security tools")
            path.append("Get security certifications (CEH, CompTIA)")
        elif "Cloud" in career or "DevOps" in career:
            path.append("Get cloud certifications (AWS/Azure/GCP)")
            path.append("Learn containerization and orchestration")
        
        path.append("Build 2-3 strong projects in the domain")
        path.append("Apply for relevant internships")
        
        return path[:5]
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF files"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages[:5]:  # First 5 pages
                    text += page.extract_text()
                return text
        except:
            return ""
    
    def _extract_doc_text(self, file_path: str) -> str:
        """Extract text from Word documents"""
        try:
            doc = docx.Document(file_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs[:20]])
        except:
            return ""
    
    def _detect_design_patterns(self, code: str) -> List[str]:
        """Detect common design patterns in code"""
        patterns = []
        
        # Simple pattern detection based on keywords
        pattern_indicators = {
            "Singleton": ["getInstance", "_instance", "singleton"],
            "Factory": ["factory", "create", "Creator"],
            "Observer": ["observer", "subscribe", "notify", "listener"],
            "MVC": ["controller", "model", "view"],
            "Repository": ["repository", "dao", "data access"]
        }
        
        code_lower = code.lower()
        for pattern, indicators in pattern_indicators.items():
            if any(indicator in code_lower for indicator in indicators):
                patterns.append(pattern)
        
        return patterns
    
    def _assess_code_quality(self, code: str) -> int:
        """Basic code quality assessment"""
        score = 50  # Base score
        
        # Check for documentation
        if '"""' in code or "'''" in code or '//' in code or '/*' in code:
            score += 10
        
        # Check for proper naming (camelCase or snake_case)
        if re.search(r'[a-z]+[A-Z][a-z]|[a-z]+_[a-z]+', code):
            score += 10
        
        # Check for error handling
        if any(keyword in code for keyword in ['try', 'catch', 'except', 'finally']):
            score += 15
        
        # Check for testing
        if any(keyword in code for keyword in ['test', 'assert', 'expect', '@Test']):
            score += 15
        
        return min(score, 100)
    
    def _get_elective_career_relevance(self, elective: str) -> str:
        """Get career relevance of an elective"""
        high_relevance = ["Data Warehousing", "Cloud Computing", "Machine Learning", "AI"]
        
        if any(hr in elective for hr in high_relevance):
            return "Critical for modern tech careers"
        else:
            return "Important for specialized roles"
    
    def _estimate_difficulty(
        self,
        elective_info: Dict[str, Any],
        project_data: Dict[str, Any]
    ) -> str:
        """Estimate difficulty level for student"""
        student_skills = set(
            project_data.get('programmingLanguages', []) +
            project_data.get('frameworks', [])
        )
        
        required_skills = set(elective_info.get('skills', []))
        skill_gap = len(required_skills - student_skills)
        
        if skill_gap <= 1:
            return "Moderate - Well prepared"
        elif skill_gap <= 3:
            return "Challenging - Some preparation needed"
        else:
            return "Difficult - Significant preparation required"
    
    def _prioritize_skills(
        self,
        skill_gaps: set,
        student_branch: str
    ) -> List[str]:
        """Prioritize skills to learn based on branch and market demand"""
        # Branch-specific priority skills
        branch_priorities = {
            "IT": ["Python", "JavaScript", "React", "AWS", "Docker"],
            "COMP": ["Python", "C++", "TensorFlow", "Algorithms", "System Design"],
            "EXTC": ["MATLAB", "Verilog", "Embedded C", "Signal Processing"],
            "ELEC": ["MATLAB", "Power Systems", "Control Systems", "PLC"],
            "MECH": ["CAD", "ANSYS", "Python", "Manufacturing"]
        }
        
        priorities = branch_priorities.get(student_branch, [])
        
        # Return skills that are both in gaps and priorities
        prioritized = [s for s in priorities if s in skill_gaps]
        
        # Add remaining gaps
        for skill in skill_gaps:
            if skill not in prioritized:
                prioritized.append(skill)
        
        return prioritized[:5]
    
    def _get_learning_resources(self, skill_gaps: set) -> Dict[str, List[str]]:
        """Get learning resources for skill gaps"""
        resources = {}
        
        # Common learning resources mapping
        resource_map = {
            "Python": ["Python for Everybody (Coursera)", "Python Crash Course (Book)", "Real Python"],
            "Machine Learning": ["Andrew Ng's ML Course", "Fast.ai", "Kaggle Learn"],
            "Cloud Computing": ["AWS Training", "Google Cloud Skills Boost", "Azure Learn"],
            "Data Structures": ["LeetCode", "HackerRank", "GeeksforGeeks"],
            "Web Development": ["MDN Web Docs", "FreeCodeCamp", "The Odin Project"]
        }
        
        for skill in list(skill_gaps)[:5]:
            # Find matching resources
            for key, res in resource_map.items():
                if key.lower() in skill.lower() or skill.lower() in key.lower():
                    resources[skill] = res
                    break
            
            # Default resources if no match
            if skill not in resources:
                resources[skill] = ["YouTube Tutorials", "Official Documentation", "Online Courses"]
        
        return resources
    
    def _extract_text_features(self, project_data: Dict[str, Any]) -> str:
        """Extract all text features from project data"""
        text_parts = [
            project_data.get('title', ''),
            project_data.get('description', ''),
            project_data.get('detailedDescription', ''),
            ' '.join(project_data.get('keyAchievements', [])),
            ' '.join(project_data.get('challengesFaced', [])),
            ' '.join(project_data.get('learnings', [])),
            ' '.join(project_data.get('programmingLanguages', [])),
            ' '.join(project_data.get('frameworks', [])),
            ' '.join(project_data.get('tools', []))
        ]
        
        return ' '.join(filter(None, text_parts)).lower()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords using TF-IDF and NLP"""
        keywords = []
        
        try:
            # Use TF-IDF
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([text])
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            
            # Get top keywords
            keyword_scores = [(feature_names[i], scores[i]) 
                            for i in scores.argsort()[-30:][::-1]]
            
            keywords = [kw for kw, _ in keyword_scores if len(kw) > 2]
            
            # Add NER entities
            doc = self.nlp(text[:100000])
            for ent in doc.ents:
                if ent.label_ in ['PRODUCT', 'ORG', 'TECH', 'GPE']:
                    keywords.append(ent.text.lower())
        except:
            pass
        
        return keywords
    
    def _analyze_technical_stack(self, project_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze and categorize technical stack"""
        return {
            'languages': [lang.lower() for lang in project_data.get('programmingLanguages', [])],
            'frameworks': [fw.lower() for fw in project_data.get('frameworks', [])],
            'tools': [tool.lower() for tool in project_data.get('tools', [])]
        }

    def _detect_js_frameworks(self, code: str) -> List[str]:
        """Detect JavaScript frameworks"""
        frameworks = []
        patterns = {
            'react': ['import React', 'from "react"', "from 'react'"],
            'angular': ['@angular', 'ng-'],
            'vue': ['Vue.', 'new Vue'],
            'express': ['express()', 'app.get', 'app.post'],
            'next': ['next/', 'Next.js']
        }
        
        for framework, indicators in patterns.items():
            if any(ind in code for ind in indicators):
                frameworks.append(framework)
        
        return frameworks
    
    def _detect_java_frameworks(self, code: str) -> List[str]:
        """Detect Java frameworks"""
        frameworks = []
        patterns = {
            'spring': ['@SpringBoot', '@Service', '@Controller', 'springframework'],
            'hibernate': ['@Entity', 'hibernate', 'SessionFactory'],
            'junit': ['@Test', 'junit', 'assertEquals']
        }
        
        for framework, indicators in patterns.items():
            if any(ind in code for ind in indicators):
                frameworks.append(framework)
        
        return frameworks