from config import *
import ollama

def estimate_tokens(text: str)->int:
    return len(text)//4

def count_message_tokens(message: dict) -> int:
    count = 0
    content = message.get("content", "")
    if isinstance(content, str):
        count+=estimate_tokens(content)
    if isinstance(content, list):
        for i in content:
            count+=estimate_tokens(i.get("text",""))
    return count

def count_total_token(messages: list[dict])->int:
    total = 0
    for message in messages:
        total+=count_message_tokens(message)

    return total

def drop_oldest_tool_pair(messages: list[dict])->list[dict]:
    system= messages[:1]
    middle = messages[1:-KEEP_RECENT]
    tail = messages[-KEEP_RECENT:]
    while True:
        old_length= len(middle)
        for i in range(len(middle)):
            if middle[i]["role"]=="tool" and i>0:
                j = i-1
                del middle[i]
                del middle[j]
                break

        new_length = len(middle)
        # if there are no more tool messages break the loop 
        if old_length == new_length:
            break
    return system+middle+tail

context = """
You are a context summarizer for an AI Agent given the conversation history return 
an appropriate summary with all the meaning information from the history captured

"""
def generate_summary(messages: list[dict])->list[dict]:
    system= messages[:1]
    middle = messages[1:-KEEP_RECENT]
    tail = messages[-KEEP_RECENT:]
    result = ""
    for i in middle:
        result += f"\n{i['role'].upper()}: {i.get('content', '')}"

    prompt = context + result
    response = ollama.chat(
        model=MODEL,
        messages=[{"role":"user","content":prompt}]
    )


    summary = response.message.content

    return system + [{"role":"system","content":summary}] + tail



