## 1 环境快照
| 组件   | 版本/说明 |
|--------|-----------|
| Ollama | 0.6.8     |
| 镜像   | llama3.1:8b |
| 端口   | 7869 → 11434 |
| GPU    | 无（CPU 推理） |

## 2 工具定义
保存为 `tools.json`：
```json
[{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "获取城市当前天气",
    "parameters": {
      "type": "object",
      "properties": {
        "city": { "type": "string" }
      },
      "required": ["city"]
    }
  }
}]
```

## 3 完整命令流
```bash
# Step-1 触发工具调用
resp=$(curl -s http://127.0.0.1:7869/api/chat \
  -H "Content-Type: application/json" \
  -d "$(jq -n --argjson tools "$(<tools.json)" '
    {model: "llama3.1:8b", messages: [{role: "user", content: "北京现在多少度"}], tools: $tools, stream: false}')")

# Step-2 提取参数
func=$(echo "$resp" | jq -r '.message.tool_calls[0].function.name')
args=$(echo "$resp" | jq -c '.message.tool_calls[0].function.arguments')
city=$(echo "$args" | jq -r '.city')
echo "模型要求调函数：$func($city)"

# Step-3 真执行（mock）
weather=$(curl -s "https://wttr.in/${city}?format=%t" | sed 's/+//;s/°C//')
echo "真实天气返回：$weather °C"

# Step-4 回传结果
msgs=$(jq -n \
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

# Step-5 拿最终回答
final=$(curl -s http://127.0.0.1:7869/api/chat \
  -H "Content-Type: application/json" \
  -d "$msgs" | jq -r .message.content)
echo "模型最终回答：$final"
```

## 4 运行结果
```
模型要求调函数：get_weather(北京)
真实天气返回：14 °C
模型最终回答："北京现在有点凉快，温度在14度左右。"
```

## 5 一键脚本
把 3~5 步保存为 `agent.sh` 即可重复运行：

```bash
#!/usr/bin/env bash
set -euo pipefail
source agent.sh
```

## 6 下一步
- [ ] 多工具循环模板  
- [ ] 记忆化 messages 落盘  
- [ ] 用 Python 封装远程调用
- [ ] 动态数据库搭建
