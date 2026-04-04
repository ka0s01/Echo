from context import *

# test estimate_tokens
text = "hello world this is a test"
print(estimate_tokens(text))  # what do you expect this to print?

# test count_total_token
messages = [
    {"role": "system", "content": "you are echo"},
    {"role": "user", "content": "read main.py"},
    {"role": "assistant", "content": "sure"},
]
print(count_total_token(messages))




messages = [{"role": "system", "content": "you are echo"}]
messages += [{"role": "user", "content": "read main.py"}]
messages += [{"role": "assistant", "content": '{"name": "read_file"}'}]
messages += [{"role": "tool", "content": "def run(): pass"}]
messages += [{"role": "user", "content": f"message {i}"} for i in range(15)]

print(drop_oldest_tool_pair(messages))
print("\n\n summary")
print(generate_summary(messages))