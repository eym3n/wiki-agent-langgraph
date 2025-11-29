# Wiki-Bot API Documentation

## Overview

Wiki-Bot is a multi-agent Wikipedia research assistant powered by LangGraph and Google Gemini. It provides a streaming chat API that can answer questions using Wikipedia as a knowledge source.

## Base URL

```
http://localhost:8000
```

## Endpoints

### POST /api/v1/chat

Streams a response to a user message. The agent will either:
- **Research route**: Search Wikipedia, gather information, and synthesize an answer with article snapshots
- **Reply route**: Respond directly for greetings or simple requests that don't need Wikipedia

#### Request

```http
POST /api/v1/chat
Content-Type: application/json
```

**Body Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | The user's question or message |
| `thread_id` | string | Yes | Unique identifier for the conversation thread. Use the same ID to maintain conversation history. |

**Example Request:**

```bash
curl -N -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Who is the current king of Morocco?", "thread_id": "user-123-session-1"}'
```

#### Response

The response is a **Server-Sent Events (SSE)** stream. Each event is prefixed with `data: ` and contains a JSON object.

**Response Format:**

```
data: {"router": "context"}

data: {"tool": "search_wikipedia"}

data: {"tool": "get_summary", "references": ["https://en.wikipedia.org/wiki/Mohammed_VI_of_Morocco"]}

data: {"content": "<article>...</article>\n\nMohammed VI is the current King of Morocco...", "references": ["https://en.wikipedia.org/wiki/Mohammed_VI_of_Morocco"]}

data: {"references": ["https://en.wikipedia.org/wiki/Mohammed_VI_of_Morocco"]}

data: [DONE]
```

---

## Event Types

### 1. Router Event

Indicates which route the agent has chosen.

```json
{
  "router": "context" | "reply"
}
```

- `"context"`: The agent will research Wikipedia to answer
- `"reply"`: The agent will respond directly without research

---

### 2. Tool Event

Indicates a Wikipedia tool is being called.

```json
{
  "tool": "search_wikipedia" | "get_summary" | "get_article" | "extract_key_facts",
  "references": ["https://en.wikipedia.org/wiki/..."]  // optional, accumulated URLs
}
```

**Available Tools:**

| Tool | Description |
|------|-------------|
| `search_wikipedia` | Searches Wikipedia for relevant articles |
| `get_summary` | Gets a brief summary of an article |
| `get_article` | Gets the full article content |
| `extract_key_facts` | Extracts key facts from an article |

---

### 3. Content Event

The final synthesized response from the agent.

```json
{
  "content": "<article>\n<heading>Article Title</heading>\n<subheading>Topic</subheading>\n<content>Quote from Wikipedia...</content>\n</article>\n\nYour answer here...",
  "references": ["https://en.wikipedia.org/wiki/..."]
}
```

**Content Structure:**

The content includes:
1. **Article Snapshots** (XML format) - Up to 10 quoted excerpts from Wikipedia
2. **Synthesized Answer** - Natural language response

**Article Snapshot Format:**

```xml
<article>
<heading>Article Title</heading>
<subheading>Section or Topic</subheading>
<content>Direct quote or key information from the article...</content>
</article>
```

---

### 4. References Event

Final list of all Wikipedia URLs referenced in the response.

```json
{
  "references": [
    "https://en.wikipedia.org/wiki/Article_1",
    "https://en.wikipedia.org/wiki/Article_2"
  ]
}
```

---

### 5. Done Event

Indicates the stream has completed.

```
data: [DONE]
```

---

### 6. Error Event

Indicates an error occurred.

```
data: [ERROR] Error message here
```

---

## Full Example

### Request

```bash
curl -N -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the Parliament of Morocco?", "thread_id": "demo-thread"}'
```

### Response Stream

```
data: {"router": "context"}

data: {"tool": "search_wikipedia"}

data: {"tool": "get_summary", "references": ["https://en.wikipedia.org/wiki/Parliament_of_Morocco"]}

data: {"tool": "get_article", "references": ["https://en.wikipedia.org/wiki/Parliament_of_Morocco"]}

data: {"content": "<article>\n<heading>Parliament of Morocco</heading>\n<subheading>Structure</subheading>\n<content>The Parliament of Morocco is the bicameral legislature of Morocco, consisting of the House of Representatives and the House of Councillors.</content>\n</article>\n\n<article>\n<heading>Parliament of Morocco</heading>\n<subheading>Powers</subheading>\n<content>The Parliament is responsible for passing laws, approving the budget, and overseeing the government.</content>\n</article>\n\nThe Parliament of Morocco is the country's bicameral legislature. It consists of two chambers: the House of Representatives (lower house) and the House of Councillors (upper house). The Parliament is responsible for passing legislation, approving the national budget, and providing oversight of the government's activities.", "references": ["https://en.wikipedia.org/wiki/Parliament_of_Morocco"]}

data: {"references": ["https://en.wikipedia.org/wiki/Parliament_of_Morocco"]}

data: [DONE]
```

---

## Frontend Implementation Guide

### JavaScript/TypeScript Example

```typescript
interface ChatEvent {
  router?: 'context' | 'reply';
  tool?: string;
  content?: string;
  references?: string[];
}

async function chat(message: string, threadId: string) {
  const response = await fetch('http://localhost:8000/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      thread_id: threadId,
    }),
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  let references: string[] = [];
  let content = '';

  while (reader) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        
        if (data === '[DONE]') {
          console.log('Stream complete');
          break;
        }
        
        if (data.startsWith('[ERROR]')) {
          console.error('Error:', data);
          break;
        }

        try {
          const event: ChatEvent = JSON.parse(data);
          
          if (event.router) {
            console.log('Route:', event.router);
          }
          
          if (event.tool) {
            console.log('Calling tool:', event.tool);
          }
          
          if (event.content) {
            content = event.content;
            console.log('Content received');
          }
          
          if (event.references) {
            references = event.references;
          }
        } catch (e) {
          // Skip non-JSON lines
        }
      }
    }
  }

  return { content, references };
}

// Usage
const result = await chat('Who is Albert Einstein?', 'my-session-123');
console.log(result.content);
console.log('Sources:', result.references);
```

### React Hook Example

```tsx
import { useState, useCallback } from 'react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  references?: string[];
  isLoading?: boolean;
}

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  currentTool: string | null;
  sendMessage: (message: string) => Promise<void>;
}

export function useChat(threadId: string): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTool, setCurrentTool] = useState<string | null>(null);

  const sendMessage = useCallback(async (message: string) => {
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: message }]);
    setIsLoading(true);
    setCurrentTool(null);

    // Add placeholder for assistant
    setMessages(prev => [...prev, { role: 'assistant', content: '', isLoading: true }]);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, thread_id: threadId }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let finalContent = '';
      let finalReferences: string[] = [];

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = line.slice(6);

          if (data === '[DONE]') break;
          if (data.startsWith('[ERROR]')) {
            throw new Error(data.slice(8));
          }

          try {
            const event = JSON.parse(data);
            
            if (event.tool) {
              setCurrentTool(event.tool);
            }
            
            if (event.content) {
              finalContent = event.content;
            }
            
            if (event.references) {
              finalReferences = event.references;
            }
          } catch (e) {
            // Skip
          }
        }
      }

      // Update assistant message with final content
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: finalContent,
          references: finalReferences,
          isLoading: false,
        };
        return updated;
      });
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: 'Sorry, an error occurred. Please try again.',
          isLoading: false,
        };
        return updated;
      });
    } finally {
      setIsLoading(false);
      setCurrentTool(null);
    }
  }, [threadId]);

  return { messages, isLoading, currentTool, sendMessage };
}
```

### Parsing Article Snapshots

```typescript
interface ArticleSnapshot {
  heading: string;
  subheading: string;
  content: string;
}

function parseArticleSnapshots(content: string): {
  snapshots: ArticleSnapshot[];
  answer: string;
} {
  const snapshots: ArticleSnapshot[] = [];
  const articleRegex = /<article>\s*<heading>(.*?)<\/heading>\s*<subheading>(.*?)<\/subheading>\s*<content>(.*?)<\/content>\s*<\/article>/gs;
  
  let match;
  while ((match = articleRegex.exec(content)) !== null) {
    snapshots.push({
      heading: match[1].trim(),
      subheading: match[2].trim(),
      content: match[3].trim(),
    });
  }

  // Remove article tags to get the answer
  const answer = content
    .replace(/<article>[\s\S]*?<\/article>/g, '')
    .trim();

  return { snapshots, answer };
}

// Usage
const { snapshots, answer } = parseArticleSnapshots(response.content);

console.log('Snapshots:', snapshots);
// [
//   { heading: "Parliament of Morocco", subheading: "Structure", content: "..." },
//   { heading: "Parliament of Morocco", subheading: "Powers", content: "..." }
// ]

console.log('Answer:', answer);
// "The Parliament of Morocco is the country's bicameral legislature..."
```

### React Component Example

```tsx
import { useChat } from './useChat';

function ChatUI() {
  const { messages, isLoading, currentTool, sendMessage } = useChat('my-thread');
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.isLoading ? (
              <div className="loading">
                {currentTool ? `Searching: ${currentTool}...` : 'Thinking...'}
              </div>
            ) : (
              <>
                <MessageContent content={msg.content} />
                {msg.references && msg.references.length > 0 && (
                  <div className="references">
                    <strong>Sources:</strong>
                    <ul>
                      {msg.references.map((url, j) => (
                        <li key={j}>
                          <a href={url} target="_blank" rel="noopener noreferrer">
                            {url.split('/wiki/')[1]?.replace(/_/g, ' ')}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          Send
        </button>
      </form>
    </div>
  );
}

function MessageContent({ content }: { content: string }) {
  const { snapshots, answer } = parseArticleSnapshots(content);

  return (
    <div>
      {snapshots.length > 0 && (
        <div className="snapshots">
          {snapshots.map((snapshot, i) => (
            <blockquote key={i} className="snapshot">
              <cite>{snapshot.heading} — {snapshot.subheading}</cite>
              <p>{snapshot.content}</p>
            </blockquote>
          ))}
        </div>
      )}
      <div className="answer">{answer}</div>
    </div>
  );
}
```

---

## Error Handling

| Status Code | Description |
|-------------|-------------|
| 200 | Success (streaming response) |
| 422 | Validation error (missing/invalid fields) |
| 503 | Agent not initialized (server starting up) |

---

## Notes

- **Thread ID**: Use consistent thread IDs to maintain conversation history. Each unique thread_id creates a separate conversation context.
- **Streaming**: The API uses Server-Sent Events (SSE). Ensure your HTTP client supports streaming responses.
- **References**: Wikipedia URLs are accumulated throughout the research process and provided with each relevant event.
- **Article Snapshots**: The synthesized response includes XML-formatted quotes from Wikipedia articles that can be parsed and displayed separately.

