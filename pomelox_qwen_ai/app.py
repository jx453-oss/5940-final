from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
import dashscope
import uuid
import json
import os
from rag_service import retrieve, get_system_prompt

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Set Qwen API key
dashscope.api_key = Config.DASHSCOPE_API_KEY

# Chat history storage path
CHAT_HISTORY_PATH = os.path.join(os.path.dirname(__file__), 'chat_history.json')

# Session storage dictionary
# Structure: {session_id: {'school_id': str, 'messages': list}}
sessions = {}


# ==================== Chat History File Storage ====================
def load_chat_history():
    """Load chat history from file"""
    if os.path.exists(CHAT_HISTORY_PATH):
        try:
            with open(CHAT_HISTORY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load chat history: {e}")
            return []
    return []


def save_chat_history(history):
    """Save chat history to file"""
    try:
        with open(CHAT_HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save chat history: {e}")
        return False


@app.route('/chat-history', methods=['GET'])
def get_chat_history():
    """Get all chat history"""
    history = load_chat_history()
    return jsonify({'chats': history})


@app.route('/chat-history', methods=['POST'])
def save_chat():
    """Save or update chat record"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body cannot be empty'}), 400

        session_id = data.get('sessionId')
        if not session_id:
            return jsonify({'error': 'sessionId cannot be empty'}), 400

        history = load_chat_history()

        # Check if session already exists
        existing_index = next((i for i, chat in enumerate(history) if chat.get('sessionId') == session_id), -1)

        chat_data = {
            'sessionId': session_id,
            'deptId': data.get('deptId'),
            'schoolId': data.get('schoolId'),
            'schoolName': data.get('schoolName'),
            'title': data.get('title', 'New Chat'),
            'messages': data.get('messages', []),
            'updatedAt': data.get('updatedAt'),
            'createdAt': data.get('createdAt') if existing_index < 0 else history[existing_index].get('createdAt')
        }

        if existing_index >= 0:
            history[existing_index] = chat_data
        else:
            history.insert(0, chat_data)

        if save_chat_history(history):
            return jsonify({'success': True, 'message': 'Save successful'})
        else:
            return jsonify({'error': 'Save failed'}), 500

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/chat-history/<session_id>', methods=['DELETE'])
def delete_chat(session_id):
    """Delete specified chat record"""
    try:
        history = load_chat_history()
        new_history = [chat for chat in history if chat.get('sessionId') != session_id]

        if len(new_history) == len(history):
            return jsonify({'error': 'Session does not exist'}), 404

        if save_chat_history(new_history):
            return jsonify({'success': True, 'message': 'Delete successful'})
        else:
            return jsonify({'error': 'Delete failed'}), 500

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/chat-history/clear', methods=['DELETE'])
def clear_all_chats():
    """Clear all chat history"""
    try:
        if save_chat_history([]):
            return jsonify({'success': True, 'message': 'All history cleared'})
        else:
            return jsonify({'error': 'Clear failed'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


def call_ai_with_web_search(messages, enable_search=False, search_strategy='standard'):
    """
    Call Qwen API with web search support

    Args:
        messages: Message list
        enable_search: Whether to enable web search
        search_strategy: Search strategy ('standard' or 'pro')

    Returns:
        tuple: (answer, sources) - Answer content and source information
    """
    call_params = {
        'model': 'qwen-plus',
        'messages': messages,
        'result_format': 'message'
    }

    if enable_search:
        call_params['enable_search'] = True
        call_params['search_options'] = {
            'search_strategy': search_strategy,
            'enable_source': True,
            'enable_citation': True
        }

    response = dashscope.Generation.call(**call_params)

    if response.status_code == 200:
        answer = response.output.choices[0].message.content
        # Get search source information (if available)
        sources = None
        try:
            if enable_search:
                # Check search_info in output (primary location for web search results)
                if hasattr(response.output, 'search_info'):
                    sources = response.output.search_info

                # Check web_search_results in message (alternative location)
                message = response.output.choices[0].message
                if hasattr(message, 'web_search_results'):
                    sources = {'search_results': message.web_search_results}

                # Check web_search in output (another alternative)
                if hasattr(response.output, 'web_search'):
                    sources = response.output.web_search
        except Exception as e:
            print(f"[Web Search] Error getting sources: {e}")
        return answer, sources
    else:
        raise Exception(f'API call failed: {response.message}')


@app.route('/ask', methods=['POST'])
def ask_ai():
    """AI Q&A endpoint (integrated with RAG)"""
    try:
        # Check request content type
        if not request.is_json:
            return jsonify({'error': 'Request must be in JSON format'}), 400

        # Get JSON data
        data = request.get_json(force=True, silent=True)

        # Check if data is empty
        if data is None:
            if not request.data or len(request.data) == 0:
                return jsonify({'error': 'Request body cannot be empty'}), 400
            else:
                return jsonify({'error': 'Request body must be valid JSON format'}), 400

        # Get parameters
        session_id = data.get('session_id', str(uuid.uuid4()))
        question = data.get('question', '')
        dept_id = data.get('deptId') or data.get('dept_id')  # Support both camelCase and snake_case

        # Validate question parameter
        if not question or not isinstance(question, str):
            return jsonify({'error': 'Question cannot be empty and must be a string'}), 400

        # Validate deptId parameter
        if not dept_id:
            return jsonify({
                'error': 'deptId cannot be empty',
                'available_dept_ids': list(Config.DEPT_TO_SCHOOL.keys())
            }), 400

        # Ensure dept_id is an integer
        try:
            dept_id = int(dept_id)
        except (ValueError, TypeError):
            return jsonify({
                'error': f'Invalid department ID format: {dept_id}',
                'available_dept_ids': list(Config.DEPT_TO_SCHOOL.keys())
            }), 400

        # Get school_id through deptId mapping
        school_id = Config.DEPT_TO_SCHOOL.get(dept_id)
        if not school_id:
            return jsonify({
                'error': f'School not found for department ID: {dept_id}',
                'available_dept_ids': list(Config.DEPT_TO_SCHOOL.keys())
            }), 400
        print(f"[Auth] Matched school via deptId={dept_id}: {school_id}")

        # If session doesn't exist, create new session
        if session_id not in sessions:
            sessions[session_id] = {
                'school_id': school_id,
                'messages': []
            }

        # Check if session's school_id matches
        if sessions[session_id]['school_id'] != school_id:
            # School changed, clear history
            sessions[session_id] = {
                'school_id': school_id,
                'messages': []
            }

        # RAG retrieve relevant content, get content, score and quality flag
        retrieved_content, max_score, has_high_quality = retrieve(school_id, question)

        # Determine if web search should be enabled
        use_web_search = False
        if not has_high_quality and Config.ENABLE_WEB_SEARCH_FALLBACK:
            use_web_search = True
            print(f"[RAG] Retrieval score: {max_score:.3f}, below high-quality threshold, enabling web search")
        else:
            print(f"[RAG] Retrieval score: {max_score:.3f}, using knowledge base content")

        # Generate system prompt
        system_prompt = get_system_prompt(school_id, retrieved_content, use_web_search)

        # Build message list
        messages = [{'role': 'system', 'content': system_prompt}]
        messages.extend(sessions[session_id]['messages'])
        messages.append({'role': 'user', 'content': question})

        # Call Qwen API (enable web search if needed)
        answer, sources = call_ai_with_web_search(
            messages,
            enable_search=use_web_search,
            search_strategy=Config.WEB_SEARCH_STRATEGY
        )

        # Save conversation history (don't save system prompt, only user dialogue)
        sessions[session_id]['messages'].append({'role': 'user', 'content': question})
        sessions[session_id]['messages'].append({'role': 'assistant', 'content': answer})

        # Build response
        response_data = {
            'session_id': session_id,
            'school_id': school_id,
            'question': question,
            'answer': answer,
            'source_type': 'web_search' if use_web_search else 'knowledge_base',
            'rag_score': round(max_score, 3)
        }

        # If web search sources exist, add to response
        if sources:
            response_data['web_sources'] = sources

        return jsonify(response_data)

    except Exception as e:
        # Catch all exceptions and return appropriate error message
        error_msg = str(e)
        if "Failed to decode JSON object" in error_msg:
            return jsonify({'error': 'Request body must be valid JSON format'}), 400
        return jsonify({'error': f'Server error: {error_msg}'}), 500


@app.route('/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """Query conversation history endpoint"""
    try:
        if session_id in sessions:
            return jsonify({
                'session_id': session_id,
                'school_id': sessions[session_id]['school_id'],
                'history': sessions[session_id]['messages']
            })
        else:
            return jsonify({'error': 'Session does not exist'}), 404
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/clear/<session_id>', methods=['DELETE'])
def clear_session(session_id):
    """Clear session records endpoint"""
    try:
        if session_id in sessions:
            del sessions[session_id]
            return jsonify({'message': 'Session cleared'})
        else:
            return jsonify({'error': 'Session does not exist'}), 404
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/schools', methods=['GET'])
def list_schools():
    """Get available schools list endpoint"""
    return jsonify({
        'schools': Config.SCHOOLS
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
