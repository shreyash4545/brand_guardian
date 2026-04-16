import os
import glob
import logging
from dotenv import load_env
load_env(override=True)


#Document loaders and splitters
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

#Azure components
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch

#setup logging and config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger=logging.getLogger("indexer")

def index_docs():
    '''
    Reads the docs,chunks them and upload them to Azure AI Search which is knowledge base
    '''
    #define the paths,we look for data folder
    current_dir=os.path.dirname(os.path.abspath(__file__))
    data_folder=os.path.join(current_dir,"../../backend/data")

    #check env variables
    logger.info("="*60)
    logger.info("ENV config check:")
    logger.info(f"AZURE_OPENAI_ENDPOINT:{os.getenv('AZURE_OPENAI_ENDPOINT')}")
    logger.info(f"AZURE_OPENAI_API_VERSION:{os.getenv('AZURE_OPENAI_API_VERSION')}")
    logger.info(f"EMBEDDING DEPLOYMENT:{os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT','text-embedding-3-small')}")
    logger.info(f"AZURE_SEARCH_ENDPOINT:{os.getenv('AZURE_SEARCH_ENDPOINT')}")
    logger.info(f"AZURE_SEARCH_INDEX_NAME:{os.getenv('AZURE_SEARCH_INDEX_NAME')}")
    logger.info("="*60)

    #Validate the required variables
    required_var=[
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_INDEX_NAME",
        "AZURE_SEARCH_API_KEY"
    ]
    missing_var=[var for  var in required_var if not os.getenv(var)]
    if missing_var:
        logger.error(f"Missing required Variables :{missing_var}")
        logger.error("Please recheck your .env file")
        return


    #Initialize embedding model:turn text into vectors
    try:
        logger.info("Initializing Azure Open AI Embeddings...........")
        embeddings=AzureOpenAIEmbeddings(
            azure_deployment=os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT','text-embedding-3-small'),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION","2024-02-01"),

        )
        logger.info("Embeddings model is initialized succesfully......")
    except Exception as e:
        logger.error(f"Failed to initialize embeddings:{e}")
        return

    #initialize the azure search
    try:
        logger.info("Initializing Azure Open AI Search vector stores.......")
        vector_store=AzureSearch(
            azure_search_endpoint=os.getenv('AZURE_OPENAI_SEARCH_ENDPOINT'),
            azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            embedding_function=embeddings.embed_query,
        )
        logger.info(f"Vector search initialized succesfully for the index: {index_name}......")
    except Exception as e:
        logger.error(f"Failed to initialize Azure Search:{e}")
        return
    #Find the PDF files
    pdf_files=glob.glob(os.path.join(data_folder,"*.pdf"))
    if not pdf_files:
        logger.warning(f"NO PDFs FOUND IN {data_folder}")
    logger.info(f"FOUND  {len(pdf_files)} PDFs to process: {[os.path.basename(f) for f in pdf_files]}")


    all_splits=[]

    #process each pdf
    for pdf_path in pdf_files:
        try:
            logger.info(f"LOADING {os.path.basename(pdf_path)}.........")
            loader=PyPDFLoader(pdf_path)
            raw_docs=loader.load()

            #chunking
            text_splitter=RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits=text_splitter.split_documents(raw_docs)
            for split in splits:
                split.metadata["source"]=os.path.basename(pdf_path)

            all_splits.extend(splits)
            logger.info(f"Split into {len(splits)} chunks.")
        except Exception as e:
            logger.error(f"Failed to process {pdf_path}  : {e}")

        #Upload to azure
    if all_splits:
         logger.info(f"Uploading  {len(splits)} chunks to Azure AI Search index '{index_name}'")
         try:
            #Azure search accepts batches automatically via this method.
                vector_store.add_documents(documents=all_splits)
                logger.info("="*60)
                logger.info("Indexing Complete. KnowledgeBase is ready.")
                logger.info(f"Total chucks indexed : {len(all_splits)}")
                logger.info("="*60)
         except Exception as e:
                logger.error(f"Failed to upload the document to Azure AISearch: {e}")
                logger.error("Please check config of AzureAISearch and try again.")
    else:
        logger.warning("No documents were processed.")

if __name__=="__main__":
    index_docs()