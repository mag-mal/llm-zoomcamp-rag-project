from flask import Flask, request, jsonify
import uuid
from datetime import datetime
import rag
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# In-memory storage for conversations (replace with database later)
conversations = {}

@app.route('/ask', methods=['POST'])
def ask_question():
    """
    Endpoint to ask a question and get an answer from the RAG system.
    
    Expected JSON payload:
    {
        "question": "What plants are safe for cats?"
    }
    
    Returns:
    {
        "conversation_id": "uuid-string",
        "question": "user question",
        "answer": "RAG generated answer",
        "timestamp": "ISO datetime"
    }
    """
    try:
        # Get question from request
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                "error": "Missing 'question' field in request body"
            }), 400
        
        question = data['question'].strip()
        
        if not question:
            return jsonify({
                "error": "Question cannot be empty"
            }), 400
        
        # Generate conversation ID
        conversation_id = str(uuid.uuid4())
        
        # Get answer from RAG system
        answer = rag.rag_groq(
            query=question,
            prompt_template=rag.prompt_template1,
            entry_template=rag.entry_template1
        )
        
        # Store conversation for potential feedback
        conversation_data = {
            "conversation_id": conversation_id,
            "question": question,
            "answer": answer,
            "timestamp": datetime.utcnow().isoformat(),
            "feedback": None
        }
        
        conversations[conversation_id] = conversation_data
        
        # Return response
        return jsonify({
            "conversation_id": conversation_id,
            "question": question,
            "answer": answer,
            "timestamp": conversation_data["timestamp"]
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"An error occurred while processing your question: {str(e)}"
        }), 500


@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Endpoint to submit feedback for a conversation.
    
    Expected JSON payload:
    {
        "conversation_id": "uuid-string",
        "feedback": 1  // +1 for positive, -1 for negative
    }
    
    Returns:
    {
        "message": "Feedback received",
        "conversation_id": "uuid-string",
        "feedback": 1
    }
    """
    try:
        # Get feedback data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Missing request body"
            }), 400
        
        if 'conversation_id' not in data:
            return jsonify({
                "error": "Missing 'conversation_id' field in request body"
            }), 400
        
        if 'feedback' not in data:
            return jsonify({
                "error": "Missing 'feedback' field in request body"
            }), 400
        
        conversation_id = data['conversation_id']
        feedback = data['feedback']
        
        # Validate feedback value
        if feedback not in [1, -1]:
            return jsonify({
                "error": "Feedback must be either +1 (positive) or -1 (negative)"
            }), 400
        
        # Check if conversation exists
        if conversation_id not in conversations:
            return jsonify({
                "error": "Conversation ID not found"
            }), 404
        
        # Store feedback
        conversations[conversation_id]['feedback'] = feedback
        conversations[conversation_id]['feedback_timestamp'] = datetime.utcnow().isoformat()
        
        return jsonify({
            "message": "Feedback received successfully",
            "conversation_id": conversation_id,
            "feedback": feedback
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"An error occurred while processing feedback: {str(e)}"
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "healthy",
        "message": "RAG Flask application is running"
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed"
    }), 405


if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True, host='0.0.0.0', port=5000)