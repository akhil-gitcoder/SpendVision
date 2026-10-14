"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Send, Sparkles, User, BadgeInfo, Trash2, History } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/States";
import { api, ApiError } from "@/lib/api";
import type { QueryResponse } from "@/types";

const SUGGESTED_QUESTIONS = [
  "How much did I spend on Food last month?",
  "What was my biggest expense this month?",
  "Which category increased the most?",
  "How much did I save this month?",
  "Compare my spending with last month.",
  "What are my top 5 expenses?",
  "Arrange my expenses in descending order.",
  "Arrange my expenses in ascending order.",
];

interface ConversationEntry {
  key: string;
  question: string;
  createdAt: string;
  response?: QueryResponse;
  error?: string;
}

function fromResponse(r: QueryResponse): ConversationEntry {
  return {
    key: r.id ?? `${r.created_at}-${r.question}`,
    question: r.question,
    createdAt: r.created_at ?? new Date().toISOString(),
    response: r,
  };
}

function dayLabel(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return "Today";
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  return d.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: d.getFullYear() === today.getFullYear() ? undefined : "numeric",
  });
}

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" });
}

export default function AskAiPage() {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<ConversationEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [confirmClear, setConfirmClear] = useState(false);
  const [clearing, setClearing] = useState(false);
  // Index into previous questions for ↑/↓ recall in the input (-1 = not recalling).
  const [recallIndex, setRecallIndex] = useState(-1);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadHistory = async () => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const res = await api.getQueryHistory();
      setHistory(res.items.map(fromResponse));
    } catch (err) {
      setHistoryError(err instanceof ApiError ? err.message : "Couldn't load your earlier questions.");
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [history.length, historyLoading]);

  const pastQuestions = useMemo(() => history.map((e) => e.question), [history]);

  const ask = async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setQuestion("");
    setRecallIndex(-1);
    const key = `pending-${Date.now()}`;
    setHistory((h) => [...h, { key, question: trimmed, createdAt: new Date().toISOString() }]);

    try {
      const response = await api.askQuery(trimmed);
      setHistory((h) => h.map((e) => (e.key === key ? { ...fromResponse(response), key } : e)));
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      setHistory((h) => h.map((e) => (e.key === key ? { ...e, error: message } : e)));
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = async () => {
    setClearing(true);
    try {
      await api.clearQueryHistory();
      setHistory([]);
      setConfirmClear(false);
    } catch (err) {
      setHistoryError(err instanceof ApiError ? err.message : "Couldn't clear history.");
    } finally {
      setClearing(false);
    }
  };

  const onInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!pastQuestions.length) return;
    if (e.key === "ArrowUp") {
      e.preventDefault();
      const next = recallIndex === -1 ? pastQuestions.length - 1 : Math.max(0, recallIndex - 1);
      setRecallIndex(next);
      setQuestion(pastQuestions[next]);
    } else if (e.key === "ArrowDown" && recallIndex !== -1) {
      e.preventDefault();
      const next = recallIndex + 1;
      if (next >= pastQuestions.length) {
        setRecallIndex(-1);
        setQuestion("");
      } else {
        setRecallIndex(next);
        setQuestion(pastQuestions[next]);
      }
    }
  };

  return (
    <div>
      <PageHeader title="Ask AI" description="Ask natural-language questions about your finances." />

      <div className="p-4 md:p-8 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className="lg:col-span-2 space-y-6">
        {history.length > 0 && (
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <History size={14} />
              {history.length} {history.length === 1 ? "question" : "questions"} in your history
            </span>
            {confirmClear ? (
              <span className="flex items-center gap-2">
                <span>Delete all earlier questions?</span>
                <button
                  onClick={clearHistory}
                  disabled={clearing}
                  className="rounded-md bg-rose-600 px-2.5 py-1 font-medium text-white hover:bg-rose-700 disabled:opacity-50"
                >
                  {clearing ? "Clearing…" : "Delete"}
                </button>
                <button
                  onClick={() => setConfirmClear(false)}
                  className="rounded-md px-2.5 py-1 font-medium text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
              </span>
            ) : (
              <button
                onClick={() => setConfirmClear(true)}
                disabled={loading}
                className="flex items-center gap-1 rounded-md px-2 py-1 font-medium hover:bg-slate-100 hover:text-rose-600 disabled:opacity-40"
              >
                <Trash2 size={13} />
                Clear history
              </button>
            )}
          </div>
        )}

        {historyLoading ? (
          <LoadingState label="Loading your earlier questions…" />
        ) : historyError ? (
          <ErrorState message={historyError} onRetry={loadHistory} />
        ) : history.length === 0 ? (
          <Card>
            <p className="text-sm text-slate-500">
              Ask a question below, or pick one of the suggestions to get started.
            </p>
          </Card>
        ) : null}

        <div className="space-y-4">
          {history.map((entry, idx) => {
            const showDay = idx === 0 || dayLabel(history[idx - 1].createdAt) !== dayLabel(entry.createdAt);
            return (
              <div key={entry.key} className="space-y-3">
                {showDay && (
                  <div className="flex items-center gap-3 pt-2 text-xs font-medium text-slate-400">
                    <div className="h-px flex-1 bg-slate-200" />
                    {dayLabel(entry.createdAt)}
                    <div className="h-px flex-1 bg-slate-200" />
                  </div>
                )}

                <div className="flex items-start gap-3 justify-end">
                  <div className="flex flex-col items-end gap-1">
                    <div className="rounded-xl rounded-tr-sm bg-brand-500 text-white px-4 py-2.5 text-sm max-w-lg">
                      {entry.question}
                    </div>
                    <span className="text-[11px] text-slate-400">{timeLabel(entry.createdAt)}</span>
                  </div>
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500">
                    <User size={16} />
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-600">
                    <Sparkles size={16} />
                  </div>
                  <Card className="max-w-lg flex-1">
                    {entry.error ? (
                      <p className="text-sm text-rose-600">{entry.error}</p>
                    ) : entry.response ? (
                      <div>
                        <p className="text-sm text-slate-800 whitespace-pre-line">{entry.response.answer}</p>
                        {!entry.response.ai_available && (
                          <span className="mt-2 flex items-center gap-1 text-xs text-slate-400">
                            <BadgeInfo size={12} />
                            Answered from calculated data (no AI key configured)
                          </span>
                        )}
                      </div>
                    ) : (
                      <LoadingState label="Thinking…" />
                    )}
                  </Card>
                </div>
              </div>
            );
          })}
          <div ref={bottomRef} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(question);
          }}
          className="sticky bottom-4 flex gap-2 rounded-xl border border-slate-200 bg-white p-2 shadow-card"
        >
          <input
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value);
              setRecallIndex(-1);
            }}
            onKeyDown={onInputKeyDown}
            placeholder={pastQuestions.length ? "Ask your finances… (↑ for earlier questions)" : "Ask your finances…"}
            className="flex-1 rounded-lg px-3 py-2 text-sm outline-none"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="flex items-center gap-1.5 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-40"
          >
            <Send size={14} />
            Ask
          </button>
        </form>
        </div>

        {/* Suggested questions - always visible, held at the vertical middle of
            the visible area below the page header (never above the header). */}
        <div className="lg:col-span-1 lg:self-start lg:sticky lg:top-[max(8.5rem,calc(50vh_-_12rem))]">
          <Card>
            <p className="text-sm font-medium text-slate-700 mb-3">Try asking</p>
            <div className="flex flex-col gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => ask(q)}
                  disabled={loading}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-left text-xs font-medium text-slate-600 hover:border-brand-300 hover:text-brand-700 hover:bg-brand-50 disabled:opacity-40"
                >
                  {q}
                </button>
              ))}
            </div>
          </Card>
        </div>
        </div>
      </div>
    </div>
  );
}
