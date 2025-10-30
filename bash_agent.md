(/home/simon/miniconda3/pkgs/zyzk) simon@simon-gpus:~$ curl -s http://127.0.0.1:7869/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "北京现在多少度"}],
    "tools": [{"type": "function", "function": {"name": "get_weather", "description": "获取城市当前天气", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}],
    "stream": false
  }' | jq
{
  "model": "llama3.1:8b",
  "created_at": "2025-10-30T03:29:44.667245744Z",
  "message": {
    "role": "assistant",
    "content": "",
    "tool_calls": [
      {
        "function": {
          "name": "get_weather",
          "arguments": {
            "city": "北京"
          }
        }
      }
    ]
  },
  "done_reason": "stop",
  "done": true,
  "total_duration": 10393399573,
  "load_duration": 4700853267,
  "prompt_eval_count": 157,
  "prompt_eval_duration": 2648657947,
  "eval_count": 23,
  "eval_duration": 3041871626
}
(/home/simon/miniconda3/pkgs/zyzk) simon@simon-gpus:~$ resp=$(curl -s http://127.0.0.1:7869/api/chat \
  -H "Content-Type: application/json" \
  -d "$(jq -n --argjson tools "$(<tools.json)" '
    {model: "llama3.1:8b", messages: [{role: "user", content: "北京现在多少度"}], tools: $tools, stream: false}')")

func=$(echo "$resp" | jq -r '.message.tool_calls[0].function.name')
args=$(echo "$resp" | jq -c '.message.tool_calls[0].function.arguments')
city=$(echo "$args" | jq -r '.city')
echo "模型要求调函数：$func($city)"
模型要求调函数：get_weather(北京)
(/home/simon/miniconda3/pkgs/zyzk) simon@simon-gpus:~$ weather=$(curl -s "https://wttr.in/${city}?format=%t" | sed 's/+//;s/°C//')
echo "真实天气返回：$weather °C"
真实天气返回：14 °C
(/home/simon/miniconda3/pkgs/zyzk) simon@simon-gpus:~$ msgs=$(jq -n \
  --argjson first "$resp" \
  --arg weather "$weather" \
  '{
     model: "llama3.1:8b",
     messages: [
       {role: "user", content: "北京现在多少度"},
       $first.message,
       {role: "user", content: "北京当前气温 \($weather) °C，请口语化一句话总结"}
     ],
     stream: false
   }')
(/home/simon/miniconda3/pkgs/zyzk) simon@simon-gpus:~$ final=$(curl -s http://127.0.0.1:7869/api/chat \
  -H "Content-Type: application/json" \
  -d "$msgs" | jq -r .message.content)
echo "模型最终回答：$final"
模型最终回答："北京现在有点凉快，温度在14度左右。"
