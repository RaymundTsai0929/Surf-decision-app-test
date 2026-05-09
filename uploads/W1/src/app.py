import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# 1. 載入環境變數 (.env 檔案中的 GOOGLE_API_KEY)
load_dotenv()

def start_rag():
    # 檢查 dataPDF 資料夾
    if not os.path.exists("dataPDF"):
        os.makedirs("dataPDF")
        print("已建立 'dataPDF' 資料夾。請在其中放入 PDF 檔案後再執行。")
        return

    # 2. 載入 PDF 文件
    pdf_files = [f for f in os.listdir("dataPDF") if f.endswith(".pdf")]
    if not pdf_files:
        print("目前 'dataPDF' 資料夾中沒有 PDF 檔案。")
        print("請放入至少一個 PDF 檔案後重新執行。")
        return

    print(f"正在讀取文件: {pdf_files}...")
    all_docs = []
    for pdf in pdf_files:
        try:
            loader = PyPDFLoader(f"dataPDF/{pdf}")
            all_docs.extend(loader.load())
        except Exception as e:
            print(f"讀取 {pdf} 時發生錯誤: {e}")

    # 3. 文件分塊 (將長文章切碎以便檢索)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=100
    )
    splits = text_splitter.split_documents(all_docs)
    print(f"文件已切分為 {len(splits)} 個區塊。")

    # 4. 建立向量資料庫 (使用 Google 的 Embedding 模型)
    print("正在建立向量資料庫 (這可能需要一點時間)...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    vectorstore = Chroma.from_documents(
        documents=splits, 
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    print("向量資料庫已建立並儲存於 './chroma_db'。")

    # 5. 建立問答鏈 (使用 Gemini Pro)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
    )

    # 6. 互動式問答
    print("\n--- RAG 系統已就緒 ---")
    while True:
        query = input("\n請輸入您的問題 (輸入 'exit' 退出): ")
        if query.lower() in ['exit', 'quit', '退出', '離開']:
            break
        
        if not query.strip():
            continue

        print("思考中...")
        try:
            response = qa_chain.invoke(query)
            print(f"\n回答: {response['result']}")
        except Exception as e:
            print(f"發生錯誤: {e}")

if __name__ == "__main__":
    start_rag()
