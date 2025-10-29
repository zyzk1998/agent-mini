# agent-mini

# Bash-Agent 零依赖智能体流水线  
## —— 从 curl 到 ReAct 的 6 步闭环实战手册

---

**版本**：v1.0  
**日期**：2025-10-29  
**作者**：zyzk1998  
**仓库**：`https://github.com/zyzk1998/agent-mini`

---

## 1. 背景与目标

- **零依赖**：仅用 `curl + jq + bash`  
- **零前端**：直接调用 Ollama HTTP API  
- **可循环**：支持多工具 ReAct 闭环  
- **可提交**：文档与代码同仓，Git 版本化

---

## 2. 环境清单

| 组件   | 版本   | 宿主机端口 | 验证命令 |
| ------ | ------ | ---------- | -------- |
| Ollama | 0.6.8  | 7869       | `docker exec ollama ollama --version` |
| 镜像   | llama3.1:8b | — | `curl 127.0.0.1:7869/api/tags` |

---

## 3. 6 步流水线（代码级）

### Step 1 定义工具
```bash
cat > tools.json <<'EOF'
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
EOF
```

### Step 2 触发工具（第一次请求）
```bash
resp=$(curl -s http://127.0.0.1:7869/api/chat \
  -H "Content-Type: application/json" \
  -d "$(jq -n --argjson tools "$(<tools.json)" '
    {model: "llama3.1:8b", messages: [{role: "user", content: "北京现在多少度"}], tools: $tools, stream: false}')")

func=$(echo "$resp" | jq -r '.message.tool_calls[0].function.name')
args=$(echo "$resp" | jq -c '.message.tool_calls[0].function.arguments')
city=$(echo "$args" | jq -r '.city')
echo "模型要求调函数：$func($city)"
```

### Step 3 真执行（mock 示例）
```bash
weather=$(curl -s "https://wttr.in/${city}?format=%t" | sed 's/+//;s/°C//')
echo "真实天气返回：$weather °C"
```

### Step 4 回传结果（user role 兼容无 id）
```bash
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
```

### Step 5 拿自然语言答案
```bash
final=$(curl -s http://127.0.0.1:7869/api/chat \
  -H "Content-Type: application/json" \
  -d "$msgs" | jq -r .message.content)
echo "模型最终回答：$final"
```

### Step 6 多工具循环模板（伪代码）
```bash
while true; do
  resp=$(Agent-Turn $messages $tools)
  if [[ -z "$(echo "$resp" | jq '.message.tool_calls[0] // empty')" ]]; then
    echo "$final" && break
  fi
  # 真执行 → 结果追加到 messages（user role）
done
```

---

## 4. PowerShell 一键函数

```powershell
function Ask-Agent {
    param($Q, $Tools=$(Get-Content tools.json -Raw))
    $uri = 'http://127.0.0.1:7869/api/chat'
    $body = @{
        model    = 'llama3.1:8b'
        messages = @(@{role='user';content=$Q})
        tools    = $Tools | ConvertFrom-Json
        stream   = $false
    } | ConvertTo-Json -Depth 10
    Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType 'application/json'
}
```

---

## 5. 已验证支持 tools 的镜像
- llama3.1:8b ✅  
- llama3.1:70b-instruct-q4_K_M ✅  
其余 deepseek-r1 / qwen3 / gemma3 目前均 ❌

---

## 6. 常用嵌入模型（纯向量）
- bge-m3:latest（768 维）
- bge-large:latest（1024 维）

---

## 7. 版本记录（Git Style）

| 版本 | 日期 | 变更 |
| ---- | ---- | ---- |
| v1.0 | 2025-10-29 | 初始发布，完成天气工具闭环 |

---

## 8. 目录结构建议

```
bash-agent-mini/
├── README.md
├── tools.json
├── agent.sh           # 主脚本
├── agent.ps1          # PowerShell 版
├── make-doc.sh        # 本文档生成器
└── docs/
    └── Agent-Cheatsheet.docx   # 本文件
```

---

## 9. 一句话记忆

> **"让模型决定 → 真执行 → 把结果当 user 塞回去 → 再对话"**  
循环这 4 步，任何工具都能变智能体。

![alt text](image.png)

## 10. 总结
#### 在本地大模型与Ollama已就绪的基础上，我启动本次实验以迈出智能体数字底座的第一步。核心诉求是超越传统工作流的“人驱节点”模式，让模型自身具备推理与行动能力——即一个可调用外部工具、能思考并闭环反馈的Agent-mini版。为此，采用在 bash 里用 curl 命令，通过 HTTP 协议访问 Ollama 的 REST 接口，验证“推理-行动-观测”原子的自主运行，为后续可扩展插件化、可审计的底座奠定自主可控技术核心。
#### 实验证实，无需LangChain等重型框架，仅凭HTTP层即可让本地大模型完成ReAct级闭环——模型主动触发工具、引用实时数据并生成可信回答。方案零依赖、全脚本，成为后续多工具、长期记忆、任务规划等高级能力的横向扩展基座，确保底座自主、可控、可扩展。
#### 未来方向：以本次实验为技术基础，实现在生物医学垂直领域上，通过本地大模型 + 自主工具闭环，让模型不仅能读懂基因序列，更能驱动实验流程、解析病理报告、预测药物响应，形成全链路智能决策引擎，助力精准医疗与生命科学研究迈向自主可控的智能化新纪元。
![alt text](image-1.png)
