import requests
import json
import uuid

# 测试基础URL
BASE_URL = 'http://localhost:8087'

def test_ask_question(session_id=None):
    """测试提问AI接口"""
    url = f'{BASE_URL}/ask'
    question = "你好，你能告诉我今天的天气怎么样吗？"
    
    payload = {
        "question": question
    }
    
    if session_id:
        payload["session_id"] = session_id
    
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print(f"提问接口响应: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()

def test_get_history(session_id):
    """测试查询对话历史接口"""
    url = f'{BASE_URL}/history/{session_id}'
    
    response = requests.get(url)
    print(f"\n查询历史接口响应: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_clear_session(session_id):
    """测试清除会话记录接口"""
    url = f'{BASE_URL}/clear/{session_id}'
    
    response = requests.delete(url)
    print(f"\n清除会话接口响应: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_health_check():
    """测试健康检查接口"""
    url = f'{BASE_URL}/health'
    
    response = requests.get(url)
    print(f"健康检查接口响应: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("=== 千问API对接测试 ===")
    
    # 1. 测试健康检查
    print("\n1. 测试健康检查接口:")
    test_health_check()
    
    # 2. 测试提问接口
    print("\n2. 测试提问接口:")
    result = test_ask_question()
    
    # 获取会话ID用于后续测试
    session_id = result.get("session_id") if result.get("session_id") else str(uuid.uuid4())
    
    # 3. 测试查询历史接口
    print("\n3. 测试查询历史接口:")
    test_get_history(session_id)
    
    # 4. 测试清除会话接口
    print("\n4. 测试清除会话接口:")
    test_clear_session(session_id)