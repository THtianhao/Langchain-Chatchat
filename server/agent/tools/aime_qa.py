from langchain.chains import RetrievalQA
from server.agent import model_container
from server.knowledge_base.kb_service.base import KBServiceFactory
from server.knowledge_base.kb_service.chroma_kb_service import ChromaKBService
from pydantic import BaseModel, Field


def qa_tool(query: str):
    fqa_service = KBServiceFactory.get_service_by_name("FQA")
    if isinstance(fqa_service, ChromaKBService):
        return RetrievalQA.from_chain_type(llm=model_container.MODEL,
                                           chain_type="stuff",
                                           retriever=fqa_service.load_vector_store().as_retriever(search_kwargs={"k": 3}),
                                           ).run(query)

class FQAInput(BaseModel):
    question: str = Field(description="Questions to inquire")
