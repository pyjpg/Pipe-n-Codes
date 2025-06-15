from langchain_core.prompts import ChatPromptTemplate
from app.core.llm import get_llm
from app.models.grading import GradeDocuments, HallucinationScore
from app.utils.prompts import GRADING_PREAMBLE, HALLUCINATION_PREAMBLE

class GradingService:
    def __init__(self):
        self.llm = get_llm()
        self._setup_graders()
    
    def _setup_graders(self):
        # Document relevance grader
        self.relevance_grader = self.llm.with_structured_output(
            GradeDocuments, 
            preamble=GRADING_PREAMBLE
        )
        
        # Hallucination grader
        self.hallucination_grader = self.llm.with_structured_output(
            HallucinationScore,
            preamble=HALLUCINATION_PREAMBLE
        )
        
        # Prompts
        self.relevance_prompt = ChatPromptTemplate.from_messages([
            ("human", "Retrieved document: \n\n{document}\n\nUser question: {question}")
        ])
        
        self.hallucination_prompt = ChatPromptTemplate.from_messages([
            ("human", "Documents:\n\n{documents}\n\nGenerated answer:\n\n{generation}")
        ])
    
    def grade_document_relevance(self, question: str, document: str) -> str:
        """Grade if document is relevant to question"""
        chain = self.relevance_prompt | self.relevance_grader
        result = chain.invoke({"question": question, "document": document})
        return result.binary_score
    
    def check_hallucination(self, documents: str, generation: str) -> str:
        """Check if answer is grounded in documents"""
        chain = self.hallucination_prompt | self.hallucination_grader
        result = chain.invoke({
            "documents": documents,
            "generation": generation
        })
        return result.binary_score

# Singleton instance
grading_service = GradingService()