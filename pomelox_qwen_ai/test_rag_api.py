import requests
import json
import uuid
import sys

# 修复 Windows 控制台编码问题
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 测试基础URL
BASE_URL = 'http://localhost:8087'


def test_health_check():
    """测试健康检查接口"""
    url = f'{BASE_URL}/health'
    response = requests.get(url)
    print("1. 健康检查:")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}\n")
    return response.status_code == 200


def test_list_schools():
    """测试获取学校列表接口"""
    url = f'{BASE_URL}/schools'
    response = requests.get(url)
    print("2. 获取学校列表:")
    print(f"   状态码: {response.status_code}")
    data = response.json()
    print(f"   可用学校: {list(data.get('schools', {}).keys())}\n")
    return response.status_code == 200


def test_ask_without_school_id():
    """测试缺少school_id参数"""
    url = f'{BASE_URL}/ask'
    payload = {
        "question": "这个学校怎么样？"
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("3. 测试缺少school_id:")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}\n")
    return response.status_code == 400


def test_ask_with_invalid_school_id():
    """测试无效的school_id"""
    url = f'{BASE_URL}/ask'
    payload = {
        "question": "这个学校怎么样？",
        "school_id": "INVALID_SCHOOL"
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("4. 测试无效school_id:")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}\n")
    return response.status_code == 400


def test_ask_with_rag(school_id: str, question: str):
    """测试RAG问答功能"""
    url = f'{BASE_URL}/ask'
    payload = {
        "question": question,
        "school_id": school_id
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print(f"5. 测试RAG问答 (school_id={school_id}):")
    print(f"   问题: {question}")
    print(f"   状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   会话ID: {data.get('session_id')}")
        print(f"   学校ID: {data.get('school_id')}")
        print(f"   回答: {data.get('answer')[:200]}..." if len(data.get('answer', '')) > 200 else f"   回答: {data.get('answer')}")
        return data
    else:
        print(f"   错误: {response.json()}")
        return None


def test_multi_turn_conversation(school_id: str):
    """测试多轮对话"""
    url = f'{BASE_URL}/ask'
    headers = {'Content-Type': 'application/json'}

    print(f"6. 测试多轮对话 (school_id={school_id}):")

    # 第一轮
    payload1 = {
        "question": "请介绍一下这个学校",
        "school_id": school_id
    }
    response1 = requests.post(url, headers=headers, data=json.dumps(payload1))
    data1 = response1.json()
    session_id = data1.get('session_id')
    print(f"   [第1轮] 问: {payload1['question']}")
    print(f"   [第1轮] 答: {data1.get('answer')[:100]}..." if len(data1.get('answer', '')) > 100 else f"   [第1轮] 答: {data1.get('answer')}")

    # 第二轮 (使用相同session_id)
    payload2 = {
        "question": "那申请条件是什么？",
        "school_id": school_id,
        "session_id": session_id
    }
    response2 = requests.post(url, headers=headers, data=json.dumps(payload2))
    data2 = response2.json()
    print(f"   [第2轮] 问: {payload2['question']}")
    print(f"   [第2轮] 答: {data2.get('answer')[:100]}..." if len(data2.get('answer', '')) > 100 else f"   [第2轮] 答: {data2.get('answer')}")

    return session_id


def test_get_history(session_id: str):
    """测试查询对话历史"""
    url = f'{BASE_URL}/history/{session_id}'
    response = requests.get(url)
    print(f"7. 查询对话历史 (session_id={session_id[:8]}...):")
    print(f"   状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   学校ID: {data.get('school_id')}")
        print(f"   对话轮数: {len(data.get('history', [])) // 2}")
    print()


def test_clear_session(session_id: str):
    """测试清除会话"""
    url = f'{BASE_URL}/clear/{session_id}'
    response = requests.delete(url)
    print(f"8. 清除会话 (session_id={session_id[:8]}...):")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("          RAG API 测试")
    print("=" * 60)
    print()

    # 基础测试
    if not test_health_check():
        print("服务未启动，请先运行: python app.py")
        exit(1)

    test_list_schools()
    test_ask_without_school_id()
    test_ask_with_invalid_school_id()

    # RAG功能测试
    print("-" * 60)
    print("RAG 功能测试")
    print("-" * 60)

    # 测试UCI学校的问答
    test_ask_with_rag("UCI", "请告诉我关于这个学校的信息")
    print()

    # 测试多轮对话
    session_id = test_multi_turn_conversation("UCLA")
    print()

    if session_id:
        test_get_history(session_id)
        test_clear_session(session_id)

    print("=" * 60)
    print("测试完成!")
    print("=" * 60)
