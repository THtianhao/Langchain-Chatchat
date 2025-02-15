import os
import shutil
from typing import List, Dict

from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.chroma import Chroma
from langchain_core.documents import Document

import pysqlite3
import sys

sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
from configs import SCORE_THRESHOLD
from server.knowledge_base.kb_service.base import KBService, SupportedVSType, EmbeddingsFunAdapter, KBServiceFactory
from server.knowledge_base.utils import get_vs_path, get_kb_path, KnowledgeFile
from server.utils import torch_gc, get_ChatOpenAI


class ChromaKBService(KBService):
    vs_path: str
    kb_path: str
    vector_name: str = None
    chroma: Chroma = None

    def vs_type(self) -> str:
        return SupportedVSType.CHROMA

    def get_vs_path(self):
        return get_vs_path(self.kb_name, self.vector_name)

    def get_kb_path(self):
        return get_kb_path(self.kb_name)

    def load_vector_store(self) -> Chroma:
        if self.chroma is None:
            if self.embed_model == "text-embedding-ada-002":
                self.chroma = Chroma(collection_name=self.kb_name,
                                     embedding_function=OpenAIEmbeddings(),
                                     persist_directory=self.get_vs_path())
            else:
                self.chroma = Chroma(collection_name=self.kb_name,
                                     embedding_function=EmbeddingsFunAdapter(self.embed_model),
                                     persist_directory=self.get_vs_path())
        return self.chroma

    def save_vector_store(self):
        self.load_vector_store().persist()

    def get_doc_by_ids(self, ids: List[str]) -> List[Document]:

        results = self.load_vector_store().get(ids)
        docs = [(Document(id=result[0], page_content=result[1], metadata=result[2] or {}))
                for result in zip(results["ids"], results["documents"], results["metadatas"], )]
        return docs

    def do_init(self):
        self.vector_name = self.vector_name or self.embed_model
        self.kb_path = self.get_kb_path()
        self.vs_path = self.get_vs_path()
        self.load_vector_store()

    def do_create_kb(self):
        if not os.path.exists(self.vs_path):
            os.makedirs(self.vs_path)
        self.load_vector_store()

    def do_drop_kb(self):
        self.clear_vs()
        try:
            shutil.rmtree(self.kb_path)
        except Exception:
            ...

    def do_search(self,
                  query: str,
                  top_k: int,
                  score_threshold: float = SCORE_THRESHOLD,
                  ) -> List[Document]:
        docs = self.load_vector_store().similarity_search(query, k=top_k, score_threshold=score_threshold)
        return docs

    def do_add_doc(self,
                   docs: List[Document],
                   **kwargs,
                   ) -> List[Dict]:
        ids = self.load_vector_store().add_documents(docs)
        if not kwargs.get("not_refresh_vs_cache"):
            self.save_vector_store()
        doc_infos = [{"id": id, "metadata": doc.metadata} for id, doc in zip(ids, docs)]
        torch_gc()
        return doc_infos

    def do_delete_doc(self,
                      kb_file: KnowledgeFile,
                      **kwargs):
        # query_result = chromaService.load_vector_store().get(where={"source"} == kb_file.filename)
        query_result = self.load_vector_store().get(where={"source": {"$eq": kb_file.filename}})
        ids = query_result['ids']
        if len(ids):
            self.load_vector_store().delete(ids)
        if not kwargs.get("not_refresh_vs_cache"):
            self.save_vector_store()
        return []
        # return ids

    def do_clear_vs(self):
        self.load_vector_store().delete_collection()
        try:
            shutil.rmtree(self.vs_path)
        except Exception:
            ...
        self.chroma = None
        os.makedirs(self.vs_path, exist_ok=True)

    def exist_doc(self, file_name: str):
        if super().exist_doc(file_name):
            return "in_db"

        content_path = os.path.join(self.kb_path, "content")
        if os.path.isfile(os.path.join(content_path, file_name)):
            return "in_folder"
        else:
            return False


if __name__ == '__main__':
    # ====== FQA
    # chromaService = ChromaKBService("FQA", )
    file_name = "FQA.md"
    # kb = KnowledgeFile(file_name, "FQA")
    # kb.text_splitter_name = "MarkdownHeaderTextSplitter"
    # chromaService.add_doc(kb)
    # model = get_ChatOpenAI(
    #     model_name='openai-api',
    #     temperature=0.8
    # )
    # result = RetrievalQA.from_chain_type(llm=model, chain_type="stuff", retriever=chromaService.load_vector_store().as_retriever()).run("How can I earn cashback?")
    # print("qa result =====", result)
    #
    # print("query result =====", chromaService.search_docs("How can I earn cashback?"))
    # ===== FQA end

    # ====== start aime
    chromaService = KBServiceFactory.get_service_by_name("aime")
    if isinstance(chromaService, ChromaKBService):
        print("query result =====", chromaService.load_vector_store().search('nike'))

        # ====== end aime

        # chromaService = ChromaKBService("aime", )
        # filename = "cashback/cashback_response_1.json"
        # chromaService.add_doc(KnowledgeFile(file_name, "aime"))
        # print("query result =====", chromaService.search_docs("ciherb"))
        # chromaService.delete_doc(KnowledgeFile("test_files/test.txt", "samples"))
        # chromaService.do_drop_kb()
        ids = chromaService.load_vector_store().get(where={"source"} == file_name)['ids']
        print('ids ======  length = ', len(ids))
        doc1 = chromaService.get_doc_by_ids([ids[0], ids[1]])
        print("doc =====", doc1)
        chromaService.load_vector_store().delete([ids[0], ids[1]])
        ids = chromaService.load_vector_store().get(where={"source"} == file_name)['ids']
        print('delete ids ==', [ids[0], ids[1]])
        print('after delete ids ======  length = ', len(ids))
        chromaService.do_delete_doc(KnowledgeFile("test_files/test.txt", knowledge_base_name="aaa"))
        ids = chromaService.load_vector_store().get(where={"source"} == file_name)['ids']
        print('after delete know ======  length = ', len(ids))
