"""Routes pour le chatbot Lexa."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from psycopg2.extras import Json
import os
from google import genai
from api.services.rag_service import rag_service
from config import get_database_connection, close_database_connection

bp = Blueprint('chat', __name__, url_prefix='/api/chat')


def _get_db():
    return get_database_connection()


def _get_session_owner(cursor, session_id, user_id):
    cursor.execute(
        "SELECT id, title, mode FROM public.chat_sessions WHERE id = %s AND user_id = %s",
        (session_id, user_id)
    )
    return cursor.fetchone()


def _create_session(cursor, user_id, mode, title):
    cursor.execute(
        """
        INSERT INTO public.chat_sessions (user_id, title, mode)
        VALUES (%s, %s, %s)
        RETURNING id, title, mode, created_at, updated_at
        """,
        (user_id, title, mode)
    )
    return cursor.fetchone()


def _touch_session(cursor, session_id, title=None):
    if title:
        cursor.execute(
            """
            UPDATE public.chat_sessions
            SET title = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (title, session_id)
        )
    else:
        cursor.execute(
            "UPDATE public.chat_sessions SET updated_at = NOW() WHERE id = %s",
            (session_id,)
        )


@bp.route('/sessions', methods=['GET'])
@jwt_required()
def list_sessions():
    user_id = get_jwt_identity()
    mode = request.args.get('mode', 'analyst')

    conn = _get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, title, mode, created_at, updated_at
            FROM public.chat_sessions
            WHERE user_id = %s AND mode = %s
            ORDER BY updated_at DESC
            LIMIT 50
            """,
            (user_id, mode)
        )
        rows = cursor.fetchall()
        sessions = [
            {
                "id": r[0],
                "title": r[1],
                "mode": r[2],
                "created_at": r[3].isoformat() if r[3] else None,
                "updated_at": r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ]
        return jsonify(sessions), 200
    finally:
        cursor.close()
        close_database_connection(conn)


@bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_session():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    mode = data.get('mode', 'analyst')
    title = data.get('title', 'New Chat')

    conn = _get_db()
    cursor = conn.cursor()
    try:
        session = _create_session(cursor, user_id, mode, title)
        conn.commit()
        return jsonify({
            "id": session[0],
            "title": session[1],
            "mode": session[2],
            "created_at": session[3].isoformat() if session[3] else None,
            "updated_at": session[4].isoformat() if session[4] else None,
        }), 201
    finally:
        cursor.close()
        close_database_connection(conn)


@bp.route('/sessions/<session_id>', methods=['PATCH'])
@jwt_required()
def rename_session(session_id):
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify(msg="Title is required"), 400

    conn = _get_db()
    cursor = conn.cursor()
    try:
        if not _get_session_owner(cursor, session_id, user_id):
            return jsonify(msg="Session not found"), 404

        cursor.execute(
            """
            UPDATE public.chat_sessions
            SET title = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id, title, mode, created_at, updated_at
            """,
            (title, session_id)
        )
        session = cursor.fetchone()
        conn.commit()
        return jsonify({
            "id": session[0],
            "title": session[1],
            "mode": session[2],
            "created_at": session[3].isoformat() if session[3] else None,
            "updated_at": session[4].isoformat() if session[4] else None,
        }), 200
    finally:
        cursor.close()
        close_database_connection(conn)


@bp.route('/sessions/<session_id>', methods=['DELETE'])
@jwt_required()
def delete_session(session_id):
    user_id = get_jwt_identity()
    conn = _get_db()
    cursor = conn.cursor()
    try:
        if not _get_session_owner(cursor, session_id, user_id):
            return jsonify(msg="Session not found"), 404

        cursor.execute("DELETE FROM public.chat_sessions WHERE id = %s", (session_id,))
        conn.commit()
        return jsonify(msg="Session deleted"), 200
    finally:
        cursor.close()
        close_database_connection(conn)


@bp.route('/sessions/<session_id>/messages', methods=['GET'])
@jwt_required()
def list_messages(session_id):
    user_id = get_jwt_identity()
    conn = _get_db()
    cursor = conn.cursor()
    try:
        if not _get_session_owner(cursor, session_id, user_id):
            return jsonify(msg="Session not found"), 404

        cursor.execute(
            """
            SELECT role, content, sources, created_at
            FROM public.chat_messages
            WHERE session_id = %s
            ORDER BY created_at ASC
            """,
            (session_id,)
        )
        rows = cursor.fetchall()
        messages = [
            {
                "role": r[0],
                "content": r[1],
                "sources": r[2] or [],
                "created_at": r[3].isoformat() if r[3] else None,
            }
            for r in rows
        ]
        return jsonify(messages), 200
    finally:
        cursor.close()
        close_database_connection(conn)

@bp.route('/message', methods=['POST'])
@jwt_required()
def chat_message():
    """Gerer l'envoi d'un message au chatbot."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
         return jsonify({"error": "GEMINI_API_KEY non configuree"}), 500
         
    client = genai.Client(api_key=api_key)
    
    data = request.json
    mode = data.get('mode', 'analyst')
    session_id = data.get('session_id')
    message = data.get('message', '')
    
    if mode not in ("analyst", "finance"):
        return jsonify({"error": "Mode inconnu"}), 400

    if not message:
        return jsonify({"error": "Message est requis"}), 400

    conn = None
    cursor = None
    try:
        user_id = get_jwt_identity()
        conn = _get_db()
        cursor = conn.cursor()

        if session_id:
            session = _get_session_owner(cursor, session_id, user_id)
            if not session:
                cursor.close()
                close_database_connection(conn)
                return jsonify({"error": "Session not found"}), 404
        else:
            session = _create_session(cursor, user_id, mode, "New Chat")
            session_id = session[0]

        cursor.execute(
            """
            INSERT INTO public.chat_messages (session_id, role, content)
            VALUES (%s, %s, %s)
            """,
            (session_id, "user", message)
        )

        if mode == 'analyst':
            # Prompt system for analyst
            sys_msg = "Tu es Lexa, l'assistant expert en analyse de donnees financieres."
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{sys_msg}\n\nUser: {message}"
            )
            response_text = response.text

            cursor.execute(
                """
                INSERT INTO public.chat_messages (session_id, role, content, sources)
                VALUES (%s, %s, %s, %s)
                """,
                (session_id, "assistant", response_text, Json([]))
            )

            if message and (session is None or session[1] == "New Chat"):
                title = message.strip().replace("\n", " ")
                title = title[:42] + "..." if len(title) > 45 else title
                _touch_session(cursor, session_id, title=title)
            else:
                _touch_session(cursor, session_id)

            conn.commit()
            
            return jsonify({
                "response": response_text,
                "sources": [],
                "session_id": session_id
            }), 200
            
        elif mode == 'finance':
            # Recuperer le contexte RAG
            search_results = rag_service.search(message, n_results=3)
            context = "\n".join([f"Source ({res['metadata'].get('source', 'Inconnu')}): {res['text']}" for res in search_results])
            
            sources = [res['metadata'].get('source', 'Document Inconnu') for res in search_results] if search_results else []
            # Deduplicate sources
            sources = list(set(sources))

            # Prompt system for finance with context
            sys_msg = f"""SYSTEM PROMPT - TUNISIAN FINANCIAL LAW ANALYST (LEXA - FINANCE MODE)

IDENTITY & ROLE
You are Lexa, an expert financial analyst and legal interpreter specialized exclusively in the Tunisian financial ecosystem. You operate as the explanation and insight layer of a deterministic financial analysis platform.

CRITICAL OPERATING PRINCIPLE - NEVER VIOLATE
THE DETERMINISTIC ENGINE COMPUTES. YOU ONLY EXPLAIN.
You will receive pre-computed financial metrics from the backend engine. These numbers are authoritative and final.

You MUST NEVER:
- Recalculate taxes independently
- Override or adjust computed values
- Guess or estimate tax rates not provided in the data block
- Contradict computed net income, EPS, or valuation figures
- Perform DCF calculations on your own
- Invent or assume financial data not provided to you
- Translate Arabic law text - quote it as-is and explain separately

You MUST ALWAYS:
- Explain computed results in clear professional language
- Contextualize results within Tunisian financial law
- Read Arabic law text directly from the law_text_ar field (do not translate it)
- Quote the Arabic legal source when referencing a law, then explain its meaning in the user's language
- Identify regulatory risks affecting future performance
- Generate analyst-grade narrative based only on provided data
- Flag legal uncertainties the user should be aware of

INPUT FORMAT YOU MAY RECEIVE (IF PROVIDED BY THE ENGINE)
BLOCK 1 - FINANCIAL DATA (Engine Output)
BLOCK 2 - LAW RULES APPLIED (Arabic Source)

If these blocks are present, treat them as the only authoritative data. If they are not present, answer only from the RAG context below.

OUTPUT STRUCTURE (always use numbered sections, detailed report)
- Each section MUST start on a new line and MUST be separated by ONE blank line.
- Use EXACT headings in the user's language (Arabic/French/English) and keep them bold.
- Format MUST be exactly:
1. **DIRECT ANSWER** <text>

2. **FINANCIAL ANALYSIS** <text>

3. **LEGAL & REGULATORY CONTEXT** <text including law_text_ar quote + article/law_name/JORT>

4. **RISK INTERPRETATION** <text>

5. **ANALYST CONCLUSION** <text>

LANGUAGE HANDLING
- Detect the user's language automatically
- Respond entirely in that language (Arabic, French, or English)
- Always include Arabic law_text_ar as-is, then explain its meaning separately
- Use official French legal terminology in parentheses when referencing law names

STRICT FALLBACK RULE
- If a requested detail is not in the provided blocks or the RAG context, say: "Information not found in the knowledge base".

RAG CONTEXT (PRIMARY SOURCE WHEN NO ENGINE BLOCKS ARE PRESENT):
{context}
"""
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{sys_msg}\n\nUser: {message}"
            )
            response_text = response.text

            cursor.execute(
                """
                INSERT INTO public.chat_messages (session_id, role, content, sources)
                VALUES (%s, %s, %s, %s)
                """,
                (session_id, "assistant", response_text, Json(sources))
            )

            if message and (session is None or session[1] == "New Chat"):
                title = message.strip().replace("\n", " ")
                title = title[:42] + "..." if len(title) > 45 else title
                _touch_session(cursor, session_id, title=title)
            else:
                _touch_session(cursor, session_id)

            conn.commit()
            
            return jsonify({
                "response": response_text,
                "sources": sources,
                "session_id": session_id
            }), 200
            
    except Exception as e:
        print(f"Error in chat: {e}")
        # Fallback to mock response if quota exceeded or other error
        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str or "503" in error_str or "unavailable" in error_str:
            mock_text = f"[MOCK - API Limit/Unavailable] Vous avez dit: '{message}'. \n(L'API Gemini est actuellement indisponible ou le quota est atteint.)"
            return jsonify({
                "response": mock_text,
                "sources": [] if mode == 'analyst' else ["Mocked Source due to Error"]
            }), 200
            
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            close_database_connection(conn)
