from urllib.parse import quote
import json
import urllib.request
import urllib.error

OLLAMA_URL = "http://127.0.0.1:7869/api/chat"

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取城市当前天气",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"]
        }
    }
}]

def rpc(messages):
    """向 Ollama 发送一次 chat 请求，返回解析好的 JSON"""
    data = json.dumps({
        "model": "llama3.1:8b",
        "messages": messages,
        "tools": TOOLS,
 "stream": False
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.URLError as e:
        print("❌ 无法连接 Ollama:", e)
        raise SystemExit(1)

def get_weather(city: str) -> str:
    """真执行：调用 wttr.in 返回温度字符串"""
    city_enc = quote(city)                # 中文转 %E5%8C%97%E4%BA%AC
    url = f"https://wttr.in/{city_enc}?format=%t"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            tmp = resp.read().decode().strip()
        tmp = tmp.replace("+", "").replace("°C", "")
        return tmp
    except Exception as e:
        return f"获取天气失败：{e}"

def main():
    messages = [{"role": "user", "content": "北京现在多少度"}]
 # Step-2：首次请求 → 拿到工具调用
    resp1 = rpc(messages)
    tool = resp1["message"]["tool_calls"][0]["function"]
    name, args = tool["name"], tool["arguments"]
    print(f"模型要求调函数：{name}({args['city']})")

    # Step-3：真执行
    temp = get_weather(args["city"])
    print(f"真实天气返回：{temp} °C")

    # Step-4：把工具结果追加到 messages
    messages.append(resp1["message"])
    messages.append({
        "role": "user",
        "content": f"北京当前气温 {temp} °C，请口语化一句话总结"
    })

    # Step-5：再次请求 → 自然语言回答
    resp2 = rpc(messages)
    answer = resp2["message"]["content"]
    print("模型最终回答：", answer)

if __name__ == "__main__":
    main()
