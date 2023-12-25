import os
import shutil
from typing import List, Dict

from langchain.vectorstores.chroma import Chroma
from langchain_core.documents import Document

from configs import SCORE_THRESHOLD
from server.knowledge_base.kb_service.base import KBService, SupportedVSType, EmbeddingsFunAdapter
from server.knowledge_base.utils import get_vs_path, get_kb_path, KnowledgeFile
from server.utils import torch_gc


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
        embed_func = EmbeddingsFunAdapter(self.embed_model)
        # embeddings = embed_func.embed_query(query)
        docs = self.load_vector_store().similarity_search(query, k=top_k, score_threshold=score_threshold)
        # with self.load_vector_store().acquire() as vs:
        #     docs = vs.similarity_search_with_score_by_vector(embeddings, k=top_k, score_threshold=score_threshold)
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

        query_result = chromaService.load_vector_store().get(where={"source"} == kb_file.filename)
        ids = query_result['ids']
        self.load_vector_store().delete(ids)
        if not kwargs.get("not_refresh_vs_cache"):
            self.save_vector_store()
        return ids
        # with self.load_vector_store().acquire() as vs:
        #     ids = [k for k, v in vs.docstore._dict.items() if v.metadata.get("source") == kb_file.filename]
        #     if len(ids) > 0:
        #         vs.delete(ids)
        #     if not kwargs.get("not_refresh_vs_cache"):
        #         vs.save_local(self.vs_path)
        # return ids

    def do_clear_vs(self):
        # with kb_faiss_pool.atomic:
        #     kb_faiss_pool.pop((self.kb_name, self.vector_name))
        # try:
        shutil.rmtree(self.vs_path)
        # except Exception:
        #     ...
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
    chromaService = ChromaKBService("samples", )
    chromaService.add_doc(KnowledgeFile("test_files/test.txt", "samples"))
    print("query result =====", chromaService.search_docs("chatGPT是什么？"))
    # chromaService.delete_doc(KnowledgeFile("test_files/test.txt", "samples"))
    # chromaService.do_drop_kb()
    ids = chromaService.load_vector_store().get(where={"source"} == "test_files/test.txt")['ids']
    print('ids ======  length = ', len(ids))
    doc1 = chromaService.get_doc_by_ids([ids[0], ids[1]])
    print("doc =====", doc1)
    chromaService.load_vector_store().delete([ids[0], ids[1]])
    ids = chromaService.load_vector_store().get(where={"source"} == "test_files/test.txt")['ids']
    print('delete ids ==', [ids[0], ids[1]])
    print('after delete ids ======  length = ', len(ids))
    chromaService.do_delete_doc(KnowledgeFile("test_files/test.txt", knowledge_base_name="aaa"))
    ids = chromaService.load_vector_store().get(where={"source"} == "test_files/test.txt")['ids']
    print('after delete know ======  length = ', len(ids))
