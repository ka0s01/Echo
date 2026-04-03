import ollama

response = ollama.chat(
    model = "qwen2.5-coder",
    messages = [{"role":"user","content":"how good are u at coding"}]
)

print(response['message']['content'])

