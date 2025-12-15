"""
知识库构建脚本
读取 school_data/ 目录下的 docx 文件，为每个学校创建向量知识库
"""
import os
import sys
from config import Config
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.dashscope import (
    DashScopeEmbedding,
    DashScopeTextEmbeddingModels,
    DashScopeTextEmbeddingType,
)

# 配置嵌入模型
EMBED_MODEL = DashScopeEmbedding(
    model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V2,
    text_type=DashScopeTextEmbeddingType.TEXT_TYPE_DOCUMENT,
)
Settings.embed_model = EMBED_MODEL


def build_single_school(school_id: str):
    """
    为单个学校构建知识库

    Args:
        school_id: 学校ID，如 'UCI', 'UCSD' 等
    """
    # 检查学校是否在配置中
    if school_id not in Config.SCHOOLS:
        print(f"错误: 学校 {school_id} 不在配置中")
        return False

    # 获取实际文件名
    school_info = Config.SCHOOLS[school_id]
    file_name = school_info.get('file', school_id)

    # 查找对应的 docx 文件
    docx_path = os.path.join(Config.SCHOOL_DATA_PATH, f"{file_name}.docx")
    if not os.path.exists(docx_path):
        print(f"错误: 找不到文件 {docx_path}")
        return False

    # 向量存储目录
    vector_path = os.path.join(Config.VECTOR_STORE_PATH, school_id)

    print(f"正在为 {school_id} 构建知识库...")
    print(f"  源文件: {docx_path}")
    print(f"  目标目录: {vector_path}")

    try:
        # 读取文档
        reader = SimpleDirectoryReader(input_files=[docx_path])
        documents = reader.load_data()
        print(f"  已加载 {len(documents)} 个文档片段")

        # 创建向量索引
        index = VectorStoreIndex.from_documents(documents)

        # 保存索引
        if not os.path.exists(vector_path):
            os.makedirs(vector_path)
        index.storage_context.persist(vector_path)

        print(f"  [OK] {school_id} 知识库构建完成")
        return True

    except Exception as e:
        print(f"  [FAIL] {school_id} 知识库构建失败: {e}")
        return False


def build_all_schools():
    """为所有配置的学校构建知识库"""
    print("=" * 50)
    print("开始构建所有学校知识库")
    print("=" * 50)

    # 确保向量存储目录存在
    if not os.path.exists(Config.VECTOR_STORE_PATH):
        os.makedirs(Config.VECTOR_STORE_PATH)

    success_count = 0
    fail_count = 0
    skip_count = 0

    for school_id, school_info in Config.SCHOOLS.items():
        file_name = school_info.get('file', school_id)
        docx_path = os.path.join(Config.SCHOOL_DATA_PATH, f"{file_name}.docx")

        if not os.path.exists(docx_path):
            print(f"跳过 {school_id}: 文件不存在 ({docx_path})")
            skip_count += 1
            continue

        if build_single_school(school_id):
            success_count += 1
        else:
            fail_count += 1

    print("=" * 50)
    print(f"构建完成: 成功 {success_count}, 失败 {fail_count}, 跳过 {skip_count}")
    print("=" * 50)


def list_available_files():
    """列出 school_data 目录中的所有文件"""
    print("\nschool_data/ 目录中的文件:")
    print("-" * 30)

    if not os.path.exists(Config.SCHOOL_DATA_PATH):
        print("目录不存在!")
        return

    files = os.listdir(Config.SCHOOL_DATA_PATH)
    if not files:
        print("目录为空!")
        return

    for f in files:
        print(f"  {f}")

    print("\n配置的学校ID:")
    print("-" * 30)
    for school_id, school_info in Config.SCHOOLS.items():
        file_name = school_info.get('file', school_id)
        docx_path = os.path.join(Config.SCHOOL_DATA_PATH, f"{file_name}.docx")
        status = "[OK]" if os.path.exists(docx_path) else "[X] (文件缺失)"
        print(f"  {school_id}: {status} -> {file_name}.docx")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            list_available_files()
        elif command == "all":
            build_all_schools()
        elif command in Config.SCHOOLS:
            build_single_school(command)
        else:
            print(f"未知的命令或学校ID: {command}")
            print("\n用法:")
            print("  python build_knowledge_base.py list    - 列出可用文件")
            print("  python build_knowledge_base.py all     - 构建所有学校知识库")
            print("  python build_knowledge_base.py UCI     - 构建单个学校知识库")
    else:
        print("知识库构建工具")
        print("\n用法:")
        print("  python build_knowledge_base.py list    - 列出可用文件")
        print("  python build_knowledge_base.py all     - 构建所有学校知识库")
        print("  python build_knowledge_base.py <学校ID> - 构建单个学校知识库")
        print(f"\n可用的学校ID: {', '.join(Config.SCHOOLS.keys())}")
