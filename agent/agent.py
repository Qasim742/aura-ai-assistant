
import os
import logging
import sqlite3
import tempfile
import threading
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.tools import tools


logger = logging.getLogger(__name__)

# =========================================================
# CONFIGURATION
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")

groq_client = Groq(api_key=GROQ_API_KEY)

MEMORY_PATH = PROJECT_ROOT / "aura_memory.sqlite"
THREAD_ID = "aura-main"


SYSTEM_PROMPT = """
You are AURA, a helpful Windows voice assistant.

GENERAL RULES
- Keep responses clear, concise, and natural for speech.
- Use the available LangChain tools to perform actions.
- Never claim an action succeeded unless the tool confirms it.
- Do not confuse the user's message to AURA with a message to another application.

WHATSAPP DESKTOP RULES
- When the user asks to search for a WhatsApp contact, search inside
  the installed WhatsApp Desktop application, not in AURA's chat,
  a web search, or Chrome.
- This applies to requests such as:
  "Search Jawad Uni", "Find Jawad Uni on WhatsApp",
  and "Open Jawad Uni chat".
- When the user says "open WhatsApp" and then asks to find a contact,
  preserve that conversational context and use WhatsApp Desktop tools.
- Use the available WhatsApp tools to open the app, search for the
  contact, and open the matching chat.
- Searching for a contact is not the same as opening the chat.
  Do not claim the chat is open until the tool confirms it.
- Type a message only into the verified intended WhatsApp chat.
- Do not send a message unless the user explicitly asks you to send it.
- Before sending, verify the intended contact and prepared message
  as far as the available tools allow.
- Never claim a message was sent unless the tool confirms the action.
- If a contact cannot be identified or the correct window cannot
  be verified, explain the limitation instead of guessing.
- Never type a contact search into AURA's own chat input.

WINDOW AND APPLICATION RULES
- Use the correct application-specific tool for every request.
- Do not use keyboard shortcuts on an unverified active window.
- Do not assume WhatsApp Desktop is Chrome or WhatsApp Web.
"""



# =========================================================
# LANGCHAIN + GROQ LLM
# =========================================================

llm = ChatGroq(
    model="qwen/qwen3.8-27b",
    temperature=0,
    max_tokens=300,
).bind_tools(tools)


# =========================================================
# SQLITE MEMORY
# =========================================================

sqlite_connection = sqlite3.connect(
    str(MEMORY_PATH),
    check_same_thread=False,
)

memory = SqliteSaver(sqlite_connection)
graph_lock = threading.RLock()


# =========================================================
# LANGGRAPH
# =========================================================

def assistant_node(state: MessagesState):
    messages = state["messages"]

    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *messages]

    response = llm.invoke(messages)
    return {"messages": [response]}


builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant_node)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

graph = builder.compile(checkpointer=memory)

CONFIG = {
    "configurable": {
        "thread_id": THREAD_ID,
    }
}


# =========================================================
# GROQ TTS
# =========================================================

def speak(text, strict=False):
    """Generate speech with Groq Orpheus and play the WAV."""
    from playsound3 import playsound

    if not text:
        return

    text = str(text).strip()
    if not text:
        return

    print(f"\nAURA: {text}", flush=True)

    # Keep chunks short for speech generation.
    words = text.split()
    chunks = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()

        if len(candidate) > 180 and current:
            chunks.append(current)
            current = word
        else:
            current = candidate

    if current:
        chunks.append(current)

    for chunk in chunks:
        audio_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
            ) as audio_file:
                audio_path = audio_file.name

            response = groq_client.audio.speech.create(
                model="canopylabs/orpheus-v1-english",
                voice="troy",
                input=chunk,
                response_format="wav",
            )

            response.write_to_file(audio_path)

            # Play the generated speech file, not a system notification.
            playsound(audio_path, block=True)

        except Exception as error:
            print(f"Groq TTS/playback error: {error}")
            if strict:
                raise

        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    pass


# =========================================================
# GROQ STT: WHISPER
# =========================================================

def listen(
    stop_event=None,
    on_listening=None,
    on_transcribing=None,
    should_stop=None,
    raise_errors=False,
):
    import speech_recognition as sr

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("\nListening...", flush=True)

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5,
            )

            if on_listening:
                on_listening()

            while not stop_event or not stop_event.is_set():
                try:
                    audio = recognizer.listen(
                        source,
                        timeout=1 if stop_event else None,
                        phrase_time_limit=15,
                    )
                    break
                except sr.WaitTimeoutError:
                    if stop_event and stop_event.is_set():
                        return ""
                    if should_stop and should_stop():
                        return ""
            else:
                return ""

        if stop_event and stop_event.is_set():
            return ""
        if on_transcribing:
            on_transcribing()
        print("Transcribing with Groq Whisper...", flush=True)

        transcription = groq_client.audio.transcriptions.create(
            file=("audio.wav", audio.get_wav_data()),
            model="whisper-large-v3-turbo",
            language="en",
            response_format="text",
            prompt=(
                "AURA, Windows applications, Python, software engineering, "
                "artificial intelligence, and computer commands."
            ),
        )

        text = (
            transcription
            if isinstance(transcription, str)
            else getattr(transcription, "text", "")
        ).strip()

        if text:
            print(f"\nYou: {text}", flush=True)

        return text

    except Exception as error:
        logger.warning("Groq STT/microphone request failed (%s)", type(error).__name__)
        if raise_errors:
            raise
        return ""


# =========================================================
# CONVERSATION HISTORY
# =========================================================

def show_history():
    try:
        with graph_lock:
            state = graph.get_state(CONFIG)
        messages = state.values.get("messages", [])

        if not messages:
            print("\nNo conversation history yet.")
            return

        print("\n========== CONVERSATION HISTORY ==========")

        for message in messages:
            if isinstance(message, HumanMessage):
                print(f"\nYou: {message.content}")
            elif getattr(message, "type", None) == "ai" and message.content:
                print(f"\nAURA: {message.content}")

        print("\n==========================================")

    except Exception as error:
        print(f"History error: {error}")


# =========================================================
# PROCESS MESSAGE
# =========================================================

def _message_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            item["text"]
            for item in content
            if isinstance(item, dict) and item.get("text")
        )
    return str(content)


def get_conversation_history(thread_id=THREAD_ID):
    config = {"configurable": {"thread_id": thread_id}}
    with graph_lock:
        state = graph.get_state(config)

    history = []
    for message in state.values.get("messages", []):
        if isinstance(message, HumanMessage):
            sender = "user"
        elif getattr(message, "type", None) == "ai":
            sender = "aura"
        else:
            continue

        text = _message_text(message.content).strip()
        if text:
            history.append({"sender": sender, "text": text})
    return history


def process_message(user_input, thread_id=THREAD_ID, speak_response=True):
    if not isinstance(user_input, str) or not user_input.strip():
        raise ValueError("Message must not be empty.")

    config = {"configurable": {"thread_id": thread_id}}
    with graph_lock:
        result = graph.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
        )

    answer = _message_text(result["messages"][-1].content)
    if speak_response and answer.strip():
        speak(answer)
    return answer


# =========================================================
# MAIN LOOP
# =========================================================


def run():
    print("\nAURA - CONTINUOUS VOICE ASSISTANT")
    print("Groq Whisper | LangChain | LangGraph | Groq Orpheus")
    print("AURA is listening continuously.")
    print("Say 'exit' or press Ctrl+C to stop.\n")

    speak("Hello! I am AURA. I am listening. How can I help you?")

    while True:
        try:
            # Listen directly instead of waiting for typed input.
            user_input = listen()

            if not user_input:
                continue

            command = user_input.strip().lower()

            if command in {"exit", "quit", "stop", "goodbye"}:
                speak("Goodbye!")
                break

            if command in {"show history", "conversation history"}:
                show_history()
                continue

            # Send recognized speech to LangGraph.
            process_message(user_input)

            # After speaking, the loop returns to the microphone.
            print("\nAURA is listening again...", flush=True)

        except KeyboardInterrupt:
            print("\nAURA stopped.")
            break

        except Exception as error:
            print(f"\nAURA error: {error}")

    sqlite_connection.close()


if __name__ == "__main__":
    run()



if __name__ == "__main__":
    run()
