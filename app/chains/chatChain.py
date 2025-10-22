# app/chains/chat_chain.py
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import RedisChatMessageHistory, ConversationBufferMemory
from qdrant_client import QdrantClient
from app.config import settings

logger = logging.getLogger(__name__)

# 1️⃣ Inicializar cliente Qdrant (ya configurado en tu servicio)
qdrant_client = QdrantClient(url=settings.QDRANT_URL)

# 2️⃣ Configurar embeddings (usa el mismo modelo que en embeddings.py)
embedding_function = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

# 3️⃣ Crear el vectorstore basado en tu colección actual
vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=settings.QDRANT_COLLECTION,
    embeddings=embedding_function,
)

# 4️⃣ Inicializar modelo Gemini con LangChain
llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL_NAME,
    api_key=settings.GEMINI_API_KEY,
    temperature=0.3
)

# 5️⃣ Configurar la memoria en Redis (aprovechando tu servidor actual)
def get_memory(user_id: str):
    """
    Crea memoria persistente para cada usuario usando Redis como backend.
    """
    redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    history = RedisChatMessageHistory(
        url=redis_url,
        session_id=user_id
    )
    return ConversationBufferMemory(
        memory_key="chat_history",
        chat_memory=history,
        return_messages=True
    )

# 6️⃣ Crear la cadena LangChain (RAG conversacional)
def get_langchain_chat(user_id: str):
    memory = get_memory(user_id)
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": settings.RAG_TOP_K}
        ),
        memory=memory,
        verbose=False
    )
    return qa_chain

# 7️⃣ Función principal para generar respuesta usando LangChain
async def chat_with_langchain(user_id: str, user_message: str) -> str:
    """
    Procesa el mensaje del usuario usando LangChain, Gemini y Qdrant.
    Incluye contexto del conocimiento + memoria persistente.
    """
    try:
        chain = get_langchain_chat(user_id)
        response = chain.invoke({"question": user_message})
        answer = response.get("answer", "").strip()
        if not answer:
            answer = "No tengo información específica sobre eso, pero puedo ayudarte con otra pregunta. ☕"
        return answer
    except Exception as e:
        logger.exception(f"💥 Error en LangChain chat: {e}")
        return "Hubo un error procesando tu mensaje, por favor intenta nuevamente."
