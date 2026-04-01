# academic-advisor-backend/app/services/chatbot/rag_service.py

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import json
import os

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        # Fallback stub so server doesn't crash
        import logging
        logging.getLogger(__name__).warning("langchain text_splitter not available")
        class RecursiveCharacterTextSplitter:
            def __init__(self, **kwargs): 
                self.chunk_size = kwargs.get('chunk_size', 1000)
                self.chunk_overlap = kwargs.get('chunk_overlap', 200)
            def split_text(self, text): 
                return [text[i:i+self.chunk_size] for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]
            def split_documents(self, docs): 
                return docs
            
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Beanie ODM imports – assume these models are Beanie documents
from app.models.chatbot import SyllabusContent, FacultyProfile, AcademicKnowledgeBase
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation service for academic content.
    Handles vector storage, similarity search, and content retrieval.
    Uses Beanie ODM for MongoDB and LangChain Chroma for vector search.
    """
    
    def __init__(self):
        # No database session needed – Beanie handles connections globally
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        self._initialize_vector_stores()
        
    def _initialize_vector_stores(self):
        """Initialize Chroma vector stores for different content types"""
        
        persist_directory = os.path.join(settings.DATA_DIR, "vector_stores")
        os.makedirs(persist_directory, exist_ok=True)
        
        # Syllabus vector store
        self.syllabus_store = Chroma(
            collection_name="syllabus_content",
            embedding_function=self.embeddings,
            persist_directory=os.path.join(persist_directory, "syllabus")
        )
        
        # Faculty vector store
        self.faculty_store = Chroma(
            collection_name="faculty_profiles",
            embedding_function=self.embeddings,
            persist_directory=os.path.join(persist_directory, "faculty")
        )
        
        # General knowledge store
        self.knowledge_store = Chroma(
            collection_name="academic_knowledge",
            embedding_function=self.embeddings,
            persist_directory=os.path.join(persist_directory, "knowledge")
        )
        
    async def index_syllabus_content(self, syllabus: SyllabusContent):
        """Index syllabus content for retrieval"""
        
        # Create document text
        content_parts = [
            f"Subject: {syllabus.subject_name} ({syllabus.subject_code})",
            f"Department: {syllabus.department}",
            f"Semester: {syllabus.semester}",
            f"Unit {syllabus.unit_number}: {syllabus.unit_title}",
            f"Topics: {', '.join(syllabus.topics)}",
        ]
        
        if syllabus.detailed_content:
            content_parts.append(f"Content: {syllabus.detailed_content}")
            
        if syllabus.learning_objectives:
            content_parts.append(f"Learning Objectives: {', '.join(syllabus.learning_objectives)}")
            
        full_content = "\n".join(content_parts)
        
        # Split into chunks
        chunks = self.text_splitter.split_text(full_content)
        
        # Create documents with metadata
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "id": str(syllabus.id),
                    "subject_code": syllabus.subject_code,
                    "subject_name": syllabus.subject_name,
                    "unit": syllabus.unit_number,
                    "type": "syllabus"
                }
            )
            for chunk in chunks
        ]
        
        # Add to vector store
        self.syllabus_store.add_documents(documents)
        self.syllabus_store.persist()
        
    async def index_faculty_profile(self, faculty: FacultyProfile):
        """Index faculty profile for retrieval"""
        
        content_parts = [
            f"Faculty: {faculty.name}",
            f"Department: {faculty.department}",
            f"Designation: {faculty.designation or 'Professor'}",
            f"Experience: {faculty.experience_years or 0} years",
            f"Subjects Taught: {', '.join(faculty.subjects_taught)}",
            f"Research Areas: {', '.join(faculty.research_areas)}",
            f"Teaching Style: {faculty.teaching_style or 'Interactive'}",
            f"Mentoring Focus: {', '.join(faculty.mentoring_focus)}",
            f"Specializations: {', '.join(faculty.specializations)}",
        ]
        
        full_content = "\n".join(content_parts)
        
        document = Document(
            page_content=full_content,
            metadata={
                "id": str(faculty.id),
                "faculty_id": faculty.faculty_id,
                "name": faculty.name,
                "department": faculty.department,
                "type": "faculty"
            }
        )
        
        self.faculty_store.add_documents([document])
        self.faculty_store.persist()
        
    async def retrieve_syllabus_content(
        self,
        query: str,
        subject_code: Optional[str] = None,
        unit: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant syllabus content — ONLY from syllabus store."""

        filter_dict = {"type": "syllabus"}
        if subject_code:
            filter_dict["subject_code"] = subject_code
        if unit:
            filter_dict["unit"] = unit

        try:
            results = self.syllabus_store.similarity_search_with_score(
                query,
                k=top_k * 2,  # fetch more, then filter
                filter=filter_dict if len(filter_dict) > 1 else None
            )
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            results = []

        # Filter out low-relevance results (distance > 1.2 typically means poor match)
        filtered_results = [(doc, score) for doc, score in results if score < 1.2]

        db_results = await self._search_syllabus_db(query, subject_code, unit)

        combined = self._merge_results(filtered_results[:top_k], db_results)

        return combined
        
    async def _search_syllabus_db(
        self,
        query: str,
        subject_code: Optional[str] = None,
        unit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search syllabus in MongoDB using Beanie"""
        
        query_lower = query.lower()
        
        # Build filter conditions
        filters = {}
        if subject_code:
            filters["subject_code"] = subject_code
        if unit:
            filters["unit_number"] = unit
            
        # Retrieve all matching documents (no built‑in full‑text search, so we filter in code)
        # Note: This may be inefficient for large collections – consider adding a text index later.
        results = await SyllabusContent.find(filters).to_list()
        
        # Filter by relevance manually
        relevant_results = []
        for syllabus in results:
            relevance_score = 0
            
            # Check topics
            for topic in syllabus.topics:
                if query_lower in topic.lower():
                    relevance_score += 0.3
                    
            # Check keywords
            if syllabus.keywords:
                for keyword in syllabus.keywords:
                    if keyword.lower() in query_lower:
                        relevance_score += 0.2
                        
            # Check detailed content
            if syllabus.detailed_content and query_lower in syllabus.detailed_content.lower():
                relevance_score += 0.5
                
            if relevance_score > 0:
                relevant_results.append({
                    'content': syllabus,
                    'score': relevance_score,
                    'source': 'database'
                })
                
        return sorted(relevant_results, key=lambda x: x['score'], reverse=True)
        
    async def retrieve_faculty_info(
        self,
        query: str,
        department: Optional[str] = None,
        subject: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant faculty information"""
        
        # Search vector store
        results = self.faculty_store.similarity_search_with_score(
            query,
            k=top_k
        )
        
        # Also search MongoDB
        db_results = await self._search_faculty_db(department, subject)
        
        # Format results
        formatted_results = []
        
        for doc, score in results:
            formatted_results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': 1 - score,  # Convert distance to similarity
                'source': 'vector_store'
            })
            
        for faculty in db_results:
            formatted_results.append({
                'content': self._format_faculty_info(faculty),
                'metadata': {
                    'faculty_id': faculty.faculty_id,
                    'name': faculty.name
                },
                'score': 0.8,  # Default score for DB results
                'source': 'database'
            })
            
        return formatted_results[:top_k]
    
    async def _search_faculty_db(
        self,
        department: Optional[str] = None,
        subject: Optional[str] = None
    ) -> List[FacultyProfile]:
        """Search faculty in MongoDB using Beanie"""
        
        filters = {}
        if department:
            filters["department"] = department
        if subject:
            # Filter by subjects_taught array containing the subject
            # This is an array containment query in MongoDB
            filters["subjects_taught"] = subject
            
        return await FacultyProfile.find(filters).to_list()
        
    def _format_faculty_info(self, faculty: FacultyProfile) -> Dict[str, Any]:
        """Format faculty profile for response"""
        
        return {
            'name': faculty.name,
            'department': faculty.department,
            'designation': faculty.designation,
            'subjects_taught': faculty.subjects_taught,
            'experience_years': faculty.experience_years,
            'teaching_style': faculty.teaching_style,
            'research_areas': faculty.research_areas,
            'mentoring_focus': faculty.mentoring_focus,
            'specializations': faculty.specializations,
            'available_for_mentoring': faculty.available_for_mentoring,
            'rating': faculty.rating,
            'office_hours': faculty.office_hours
        }
        
    async def retrieve_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        department: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve from general academic knowledge base"""
        
        filter_dict = {}
        if category:
            filter_dict["category"] = category
            
        results = self.knowledge_store.similarity_search_with_score(
            query,
            k=top_k,
            filter=filter_dict if filter_dict else None
        )
        
        # Also check MongoDB
        db_query = AcademicKnowledgeBase.find()
        if category:
            db_query = db_query.find(AcademicKnowledgeBase.category == category)
        if department:
            db_query = db_query.find(AcademicKnowledgeBase.department == department)
            
        db_results = await db_query.limit(top_k).to_list()
        
        formatted_results = []
        
        for doc, score in results:
            formatted_results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': 1 - score,
                'source': 'vector_store'
            })
            
        # Optionally add db_results here if needed – for now just vector results
            
        return formatted_results
        
    def _merge_results(
        self, 
        vector_results: List[Tuple], 
        db_results: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Merge and deduplicate results from vector store and database"""
        
        merged = []
        seen_ids = set()
        
        # Add vector results
        for doc, score in vector_results:
            doc_id = doc.metadata.get('id')
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                merged.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': 1 - score,
                    'source': 'vector_store'
                })
                
        # Add database results
        for result in db_results:
            content = result.get('content')
            if content and hasattr(content, 'id'):
                doc_id = str(content.id)
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    merged.append(result)
                    
        # Sort by score
        merged.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return merged
        
    async def get_retrieval_confidence(self, results: List[Dict]) -> str:
        """Determine confidence level based on retrieval results"""
        
        if not results:
            return "Low"
            
        avg_score = sum(r.get('score', 0) for r in results) / len(results)
        
        if avg_score >= 0.8:
            return "High"
        elif avg_score >= 0.5:
            return "Medium"
        else:
            return "Low"
        
    async def index_open_elective_knowledge(self):
        """Index the 5 Sem-VII Open Elective syllabi into the knowledge store."""
        from app.ml.models.recommendation_engine import OPEN_ELECTIVE_META

        for key, meta in OPEN_ELECTIVE_META.items():
            content_parts = [
                f"Open Elective: {meta['name']} ({meta['code']})",
                f"Semester: {meta['semester']}",
                f"Credits: {meta['credits']}",
                f"Category: {meta['category']}",
                f"Description: {meta['description']}",
                f"Skills: {', '.join(meta['skills'])}",
                f"Career Paths: {', '.join(meta['career_paths'])}",
            ]
            if meta.get("modules"):
                content_parts.append("Modules:")
                for i, mod in enumerate(meta["modules"], 1):
                    content_parts.append(f"  {i}. {mod}")

            full_content = "\n".join(content_parts)
            chunks = self.text_splitter.split_text(full_content)

            documents = [
                Document(
                    page_content=chunk,
                    metadata={
                        "id": f"oec_{key}_{i}",
                        "subject_code": meta["code"],
                        "subject_name": meta["name"],
                        "type": "syllabus",
                        "category": "open_elective",
                        "semester": 7,
                    }
                )
                for i, chunk in enumerate(chunks)
            ]

            self.knowledge_store.add_documents(documents)
            # Also add to syllabus store for subject queries
            self.syllabus_store.add_documents(documents)

        self.knowledge_store.persist()
        self.syllabus_store.persist()
        logger.info("✅ Indexed 5 Open Elective syllabi into vector stores")