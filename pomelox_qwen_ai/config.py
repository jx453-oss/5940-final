import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'

    # Qwen API configuration
    DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY') or 'your-api-key-here'

    # Server configuration
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 8087))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # School configuration (file field corresponds to actual filename in school_data/ directory, without extension)
    # deptId is the department ID in the backend system, used for automatic school matching
    SCHOOLS = {
        'UCI': {'name': 'UC Irvine', 'name_cn': 'UC Irvine', 'file': 'UCI', 'deptId': None},
        'UCSD': {'name': 'UC San Diego', 'name_cn': 'UC San Diego', 'file': 'UCSD', 'deptId': 216},
        'NYU': {'name': 'New York University', 'name_cn': 'New York University', 'file': 'NYUCU', 'deptId': 226},
        'OSU': {'name': 'Ohio State University', 'name_cn': 'Ohio State University', 'file': 'OSUCU', 'deptId': None},
        'UCB': {'name': 'UC Berkeley', 'name_cn': 'UC Berkeley', 'file': 'UCBCU', 'deptId': 211},
        'UCLA': {'name': 'UC Los Angeles', 'name_cn': 'UC Los Angeles', 'file': 'UCLACU', 'deptId': 214},
        'UPenn': {'name': 'University of Pennsylvania', 'name_cn': 'University of Pennsylvania', 'file': 'UPennCU', 'deptId': None},
        'USC': {'name': 'University of Southern California', 'name_cn': 'University of Southern California', 'file': 'USCCU', 'deptId': 213},
        'UW': {'name': 'University of Washington', 'name_cn': 'University of Washington', 'file': 'UWCU', 'deptId': 218},
    }

    # Reverse mapping from deptId to school_id (for quick school lookup by user department ID)
    DEPT_TO_SCHOOL = {
        211: 'UCB',   # UC Berkeley
        213: 'USC',   # University of Southern California
        214: 'UCLA',  # UC Los Angeles
        216: 'UCSD',  # UC San Diego
        218: 'UW',    # University of Washington
        226: 'NYU',   # New York University
    }

    # RAG configuration
    SCHOOL_DATA_PATH = os.path.join(os.path.dirname(__file__), 'school_data')
    VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), 'vector_store')
    RAG_SIMILARITY_THRESHOLD = 0.2      # Minimum similarity threshold
    RAG_HIGH_QUALITY_THRESHOLD = 0.5    # High quality result threshold (web search triggered below this value)
    RAG_CHUNK_COUNT = 5

    # Web search configuration
    ENABLE_WEB_SEARCH_FALLBACK = True   # Whether to enable web search fallback
    WEB_SEARCH_STRATEGY = 'standard'    # Search strategy: standard, pro (pro returns more sources)

# Set Qwen API key
import dashscope
dashscope.api_key = Config.DASHSCOPE_API_KEY