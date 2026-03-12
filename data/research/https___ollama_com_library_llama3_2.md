[ ![Ollama](https://ollama.com/public/ollama.png) ](https://ollama.com/)
[Models](https://ollama.com/search) [Docs](https://ollama.com/docs) [Pricing](https://ollama.com/pricing)
[Sign in](https://ollama.com/signin) [Download](https://ollama.com/download)
[Models](https://ollama.com/search) [Download](https://ollama.com/download) [Docs](https://ollama.com/docs) [Pricing](https://ollama.com/pricing) [Sign in](https://ollama.com/signin)
[llama3.2](https://ollama.com/library/llama3.2 "llama3.2")
60M Downloads Updated  1 year ago
##  Meta's Llama 3.2 goes small with 1B and 3B models. 
Meta's Llama 3.2 goes small with 1B and 3B models. 
Cancel 
tools 1b 3b
CLI cURL Python JavaScript
[Documentation ](https://github.com/ollama/ollama-python) [Documentation ](https://github.com/ollama/ollama-js)
```
ollama run llama3.2
```

```
curl http://localhost:11434/api/chat \
  -d '{
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

```
from ollama import chat

response = chat(
    model='llama3.2',
    messages=[{'role': 'user', 'content': 'Hello!'}],
)
print(response.message.content)
```

```
import ollama from 'ollama'

const response = await ollama.chat({
  model: 'llama3.2',
  messages: [{role: 'user', content: 'Hello!'}],
})
console.log(response.message.content)
```

## Applications
![Claude Code](https://ollama.com/public/claude.png)
Claude Code `ollama launch claude --model llama3.2`
![Codex](https://ollama.com/public/openai.png)
Codex `ollama launch codex --model llama3.2`
![OpenCode](https://ollama.com/public/opencode.png)
OpenCode `ollama launch opencode --model llama3.2`
![OpenClaw](https://ollama.com/public/openclaw.png)
OpenClaw `ollama launch openclaw --model llama3.2`
## Models
[View all →](https://ollama.com/library/llama3.2/tags)
Name
63 models
Size
Context
Input
[ llama3.2:latest 2.0GB · 128K context window · Text · 1 year ago ](https://ollama.com/library/llama3.2:latest)
[llama3.2:latest](https://ollama.com/library/llama3.2:latest)
2.0GB
128K
Text 
[ llama3.2:1b 1.3GB · 128K context window · Text · 1 year ago ](https://ollama.com/library/llama3.2:1b)
[llama3.2:1b](https://ollama.com/library/llama3.2:1b)
1.3GB
128K
Text 
[ llama3.2:3b latest 2.0GB · 128K context window · Text · 1 year ago ](https://ollama.com/library/llama3.2:3b)
[llama3.2:3b](https://ollama.com/library/llama3.2:3b) latest
2.0GB
128K
Text 
## Readme
![](https://ollama.com/assets/library/llama3.2/be01fadf-7fbd-404d-929b-50a77249b030)
The Meta Llama 3.2 collection of multilingual large language models (LLMs) is a collection of pretrained and instruction-tuned generative models in 1B and 3B sizes (text in/text out). The Llama 3.2 instruction-tuned text only models are optimized for multilingual dialogue use cases, including agentic retrieval and summarization tasks. They outperform many of the available open source and closed chat models on common industry benchmarks.
## Sizes
### 3B parameters (default)
The 3B model outperforms the Gemma 2 2.6B and Phi 3.5-mini models on tasks such as:
  * Following instructions
  * Summarization
  * Prompt rewriting
  * Tool use

```
ollama run llama3.2

```

### 1B parameters
The 1B model is competitive with other 1-3B parameter models. It’s use cases include:
  * Personal information management
  * Multilingual knowledge retrieval
  * Rewriting tasks running locally on edge

```
ollama run llama3.2:1b

```

### Benchmarks
![Llama 3.2 instruction-tuned benchmarks](https://ollama.com/assets/library/llama3.2/c1a51716-d8bb-4642-8044-48f5022b777d)
**Supported Languages:** English, German, French, Italian, Portuguese, Hindi, Spanish, and Thai are officially supported. Llama 3.2 has been trained on a broader collection of languages than these 8 supported languages.
Write Preview
<img src="/assets/library/llama3.2/be01fadf-7fbd-404d-929b-50a77249b030" width="280" /> The Meta Llama 3.2 collection of multilingual large language models (LLMs) is a collection of pretrained and instruction-tuned generative models in 1B and 3B sizes (text in/text out). The Llama 3.2 instruction-tuned text only models are optimized for multilingual dialogue use cases, including agentic retrieval and summarization tasks. They outperform many of the available open source and closed chat models on common industry benchmarks. ## Sizes ### 3B parameters (default) The 3B model outperforms the Gemma 2 2.6B and Phi 3.5-mini models on tasks such as: * Following instructions * Summarization * Prompt rewriting * Tool use ``` ollama run llama3.2 ``` ### 1B parameters The 1B model is competitive with other 1-3B parameter models. It's use cases include: * Personal information management * Multilingual knowledge retrieval * Rewriting tasks running locally on edge ``` ollama run llama3.2:1b ``` ### Benchmarks ![Llama 3.2 instruction-tuned benchmarks](https://ollama.com/assets/library/llama3.2/c1a51716-d8bb-4642-8044-48f5022b777d) **Supported Languages:** English, German, French, Italian, Portuguese, Hindi, Spanish, and Thai are officially supported. Llama 3.2 has been trained on a broader collection of languages than these 8 supported languages.
Paste, drop or click to upload images (.png, .jpeg, .jpg, .svg, .gif) 
© 2026 Ollama
[Download](https://ollama.com/download) [Blog](https://ollama.com/blog) [Docs](https://docs.ollama.com) [GitHub](https://github.com/ollama/ollama) [Discord](https://discord.com/invite/ollama) [X (Twitter)](https://twitter.com/ollama) Contact
  * [Blog](https://ollama.com/blog)
  * [Download](https://ollama.com/download)
  * [Docs](https://docs.ollama.com)


  * [GitHub](https://github.com/ollama/ollama)
  * [Discord](https://discord.com/invite/ollama)
  * [X (Twitter)](https://twitter.com/ollama)
  * [Meetups](https://lu.ma/ollama)


© 2026 Ollama Inc. 
