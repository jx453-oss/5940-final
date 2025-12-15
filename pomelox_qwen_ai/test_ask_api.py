import requests
import json

# 测试基础URL
BASE_URL = 'http://localhost:8087'

def test_ask_with_valid_json():
    """测试使用有效JSON请求"""
    url = f'{BASE_URL}/ask'
    payload = {
        "question": "你好，你能告诉我今天的天气怎么样吗？"
    }
    
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("测试有效JSON请求:")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}\n")

def test_ask_with_empty_body():
    """测试空请求体"""
    url = f'{BASE_URL}/ask'
    
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers, data='')
    print("测试空请求体:")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}\n")

def test_ask_with_invalid_content_type():
    """测试无效内容类型"""
    url = f'{BASE_URL}/ask'
    payload = {
        "question": "你好，你能告诉我今天的天气怎么样吗？"
    }
    
    # 不设置Content-Type或设置错误的Content-Type
    response = requests.post(url, data=json.dumps(payload))
    print("测试无效内容类型:")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}\n")

def test_ask_with_missing_question():
    """测试缺少问题参数"""
    url = f'{BASE_URL}/ask'
    payload = {
        "session_id": "test-session-id"
        # 故意缺少question字段
    }
    
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("测试缺少问题参数:")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}\n")

if __name__ == "__main__":
    print("=== 测试修复后的/ask接口 ===\n")
    
    test_ask_with_valid_json()
    test_ask_with_empty_body()
    test_ask_with_invalid_content_type()
    test_ask_with_missing_question()