# from langchain.chains.query_constructor.schema import AttributeInfo
# from langchain.retrievers import EnsembleRetriever, SelfQueryRetriever
#
# from server.knowledge_base.kb_service.base import KBServiceFactory
# from server.utils import get_ChatOpenAI
#
# metadata_field_info = [
#     AttributeInfo(
#         name="couponTitle",
#         description="The detail of coupon, deal, discount of coupon, generally describe coupon informationn",
#         type="string",
#     ),
#     AttributeInfo(
#         name="couponCode",
#         description="The coupon code of a [coupon] that can be used",
#         type="string",
#     ),
#     AttributeInfo(
#         name="cashbackDetail",
#         description="The cashback number or cashback rate or deal rate or discount rate for a brand or product or store",
#         type="list",
#     ),
#     AttributeInfo(
#         name="categories",
#         description="The cashback or  coupon in dedicated category,one or more of [Clothing, Electronics,Health & Beauty,Shoes,Travel & Vacations,Accessories,Auto & Tires,Baby & Toddler,Digital Services & Streaming,Events & Entertainment,Gifts Flowers & Parties,Food Drinks & Restaurants,Home & Garden,Office Supplies,Pets,Sports Outdoors & Fitness,Subscription Boxes & Services,Toys & Games]",
#         type="list",
#     )
#
# ]
# llm = get_ChatOpenAI(model_name='openai-api', temperature=0)
# document_content_description = "Brief name of a brand"
# couponServer = KBServiceFactory.get_service_by_name("aime")
# coupon_retriever = couponServer.load_vector_store().obj
# retriever = SelfQueryRetriever.from_llm(
#     llm,
#     coupon_retriever,
#     document_content_description,
#     metadata_field_info,
#     enable_limit=True,
#     search_kwargs={"k": 40}
# )
