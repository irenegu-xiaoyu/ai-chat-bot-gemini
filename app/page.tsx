"use client";

import React, { useEffect, useRef, useState } from "react";

type Message = { id: number; sender: "user" | "bot"; text: string };

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const listRef = useRef<HTMLDivElement | null>(null);
  const idRef = useRef(1);

  useEffect(() => {
    // scroll to bottom when messages change
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text) return;
    const userMsg: Message = { id: idRef.current++, sender: "user", text };
    setMessages((p) => [...p, userMsg]);
    setInput("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) {
        throw new Error(`server error: ${res.status}`);
      }

      const data = await res.json();
      const botMsg: Message = {
        id: idRef.current++,
        sender: "bot",
        text: data.reply,
      };
      setMessages((p) => [...p, botMsg]);
    } catch (err: any) {
      // fallback to local echo on network / server error
      const botMsg: Message = {
        id: idRef.current++,
        sender: "bot",
        text: `Error contacting backend, fallback reply: ${
          err?.message ?? String(err)
        }`,
      };
      setMessages((p) => [...p, botMsg]);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-black font-sans">
      <main className="w-full max-w-3xl px-4 py-8">
        <h1 className="text-2xl font-semibold mb-4 text-black dark:text-white">
          AI Chat
        </h1>

        <div className="flex flex-col h-[70vh] bg-white dark:bg-[#0b0b0b] rounded-lg shadow-sm overflow-hidden">
          <div
            ref={listRef}
            className="flex-1 overflow-y-auto p-4 space-y-3 chat-scrollbar"
            data-testid="message-list"
          >
            {messages.length === 0 ? (
              <div className="text-center text-zinc-500 dark:text-zinc-400">
                Start the conversation — say hi 👋
              </div>
            ) : (
              messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex ${
                    m.sender === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] px-4 py-2 rounded-lg whitespace-pre-wrap ${
                      m.sender === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-zinc-100 text-zinc-900 dark:bg-[#111] dark:text-zinc-200"
                    }`}
                  >
                    {m.text}
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="border-t border-zinc-200 dark:border-zinc-800 p-4">
            <div className="flex gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                rows={1}
                placeholder="Type a message and press Enter to send"
                className="flex-1 resize-none rounded-md border border-zinc-200 dark:border-zinc-800 p-2 bg-transparent text-black dark:text-white focus:outline-none"
              />
              <button
                onClick={sendMessage}
                className="px-4 py-2 rounded-md bg-black text-white hover:opacity-90 dark:bg-white dark:text-black"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
