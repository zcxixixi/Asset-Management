import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  BrainCircuit,
  ChevronLeft,
  Cpu,
  Database,
  FileClock,
  FileSearch,
  FolderKanban,
  Layers3,
  MessagesSquare,
  Radar,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Workflow,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface AgentMechanismProps {
  onBack: () => void;
}

interface FlowStage {
  step: string;
  title: string;
  body: string;
  accent: string;
  icon: LucideIcon;
}

interface GraphNode {
  id: string;
  title: string;
  caption: string;
  x: number;
  y: number;
  accent: string;
  glow: string;
  icon: LucideIcon;
}

interface GraphEdge {
  from: [number, number];
  to: [number, number];
  color: string;
  delay: number;
}

type ExplainMode = 'learn' | 'graph';

const flowStages: FlowStage[] = [
  {
    step: '01',
    title: 'User turn enters the session log',
    body:
      'Each incoming turn is appended to a channel-scoped JSONL session so the raw chronology of user, assistant, and tool events remains durable.',
    accent: 'from-cyan-400 to-sky-500',
    icon: MessagesSquare,
  },
  {
    step: '02',
    title: 'Prompt builder assembles the working set',
    body:
      'Nanobot combines bootstrap files, `MEMORY.md`, recent unconsolidated turns, runtime metadata, and the current message into the live prompt stack.',
    accent: 'from-blue-500 to-indigo-500',
    icon: Layers3,
  },
  {
    step: '03',
    title: 'Agent reasons on the hot context',
    body:
      'The model sees only the active working set, not the entire historical backlog. This keeps context tight enough to stay fast and legible.',
    accent: 'from-indigo-500 to-violet-500',
    icon: Cpu,
  },
  {
    step: '04',
    title: 'Memory window triggers consolidation',
    body:
      'When unconsolidated history reaches the configured threshold, nanobot starts a background consolidation pass instead of carrying the full tail forever.',
    accent: 'from-violet-500 to-fuchsia-500',
    icon: RefreshCw,
  },
  {
    step: '05',
    title: 'Older turns become durable long-term memory',
    body:
      'The consolidator writes stable facts to `MEMORY.md` and a searchable timestamped summary to `HISTORY.md`, while the newest raw turns remain hot.',
    accent: 'from-emerald-500 to-teal-500',
    icon: Database,
  },
];

const graphNodes: GraphNode[] = [
  {
    id: 'user',
    title: 'User Message',
    caption: 'live input',
    x: 12,
    y: 22,
    accent: 'from-cyan-400 to-sky-500',
    glow: 'rgba(34,211,238,0.34)',
    icon: MessagesSquare,
  },
  {
    id: 'session',
    title: 'Session JSONL',
    caption: 'raw short-term turns',
    x: 31,
    y: 22,
    accent: 'from-sky-500 to-blue-500',
    glow: 'rgba(59,130,246,0.30)',
    icon: FolderKanban,
  },
  {
    id: 'prompt',
    title: 'Prompt Builder',
    caption: 'assembles working context',
    x: 50,
    y: 22,
    accent: 'from-blue-500 to-indigo-500',
    glow: 'rgba(79,70,229,0.32)',
    icon: Layers3,
  },
  {
    id: 'model',
    title: 'Agent / Model',
    caption: 'reasons on hot context',
    x: 74,
    y: 22,
    accent: 'from-indigo-500 to-violet-500',
    glow: 'rgba(99,102,241,0.36)',
    icon: BrainCircuit,
  },
  {
    id: 'window',
    title: 'Memory Window',
    caption: '100-turn trigger',
    x: 50,
    y: 48,
    accent: 'from-fuchsia-500 to-purple-500',
    glow: 'rgba(217,70,239,0.30)',
    icon: Radar,
  },
  {
    id: 'memory',
    title: 'MEMORY.md',
    caption: 'loaded on next prompt',
    x: 30,
    y: 74,
    accent: 'from-emerald-500 to-teal-500',
    glow: 'rgba(16,185,129,0.32)',
    icon: FileClock,
  },
  {
    id: 'history',
    title: 'HISTORY.md',
    caption: 'searchable summaries only',
    x: 69,
    y: 74,
    accent: 'from-amber-500 to-orange-500',
    glow: 'rgba(249,115,22,0.28)',
    icon: FileSearch,
  },
];

const graphEdges: GraphEdge[] = [
  { from: [17, 22], to: [26, 22], color: '#38bdf8', delay: 0 },
  { from: [36, 22], to: [45, 22], color: '#60a5fa', delay: 0.25 },
  { from: [56, 22], to: [68, 22], color: '#818cf8', delay: 0.5 },
  { from: [72, 29], to: [54, 45], color: '#a78bfa', delay: 0.9 },
  { from: [46, 29], to: [48, 44], color: '#c084fc', delay: 1.15 },
  { from: [44, 52], to: [34, 68], color: '#34d399', delay: 1.5 },
  { from: [56, 52], to: [64, 68], color: '#f59e0b', delay: 1.8 },
  { from: [34, 70], to: [44, 30], color: '#2dd4bf', delay: 2.15 },
];

const implementationFacts = [
  {
    title: 'Short-term live window',
    value: '100',
    note: 'Configured as `memory_window` in the default agent settings.',
  },
  {
    title: 'Raw turns kept hot',
    value: '~50',
    note: 'After consolidation, the newest half of the window stays as raw working memory.',
  },
  {
    title: 'Provider-side storage',
    value: 'off',
    note: 'Responses-style providers send requests with `store: false`.',
  },
  {
    title: 'Recall mechanism',
    value: 'files',
    note: 'This path uses local files plus grep, not vector embeddings.',
  },
];

const distinctions = [
  {
    label: 'Short-term memory',
    title: 'recent unconsolidated turns',
    body:
      'This is the active working memory. It is recent, raw, and directly injected into the next model call as session history.',
    chips: ['`sessions/*.jsonl`', 'raw chronology', 'prompt-visible'],
    tone: 'border-cyan-200 bg-cyan-50/85',
  },
  {
    label: 'Long-term memory',
    title: 'facts and summaries on disk',
    body:
      'This is the durable layer. `MEMORY.md` carries stable facts forward, while `HISTORY.md` keeps timestamped summaries for search and audit.',
    chips: ['`MEMORY.md`', '`HISTORY.md`', 'compact + durable'],
    tone: 'border-emerald-200 bg-emerald-50/85',
  },
];

const filePanels = [
  {
    title: 'sessions/<chat>.jsonl',
    text: 'Append-only turn log for each conversation. This is where short-term chronology lives before and after consolidation.',
    icon: FolderKanban,
  },
  {
    title: 'memory/MEMORY.md',
    text: 'Stable facts that get injected into later prompts. This is the long-term file the agent actually re-reads every turn.',
    icon: FileClock,
  },
  {
    title: 'memory/HISTORY.md',
    text: 'Timestamped summaries of older exchanges. Persisted for grep-based recall, not dumped wholesale into prompt context.',
    icon: FileSearch,
  },
];

const learnSteps = [
  {
    step: 'A',
    title: '先记住最近对话',
    body: '你刚说的话、nanobot刚回复的话、还有工具调用结果，都会先放进会话文件里。这一层就是短期记忆。',
    accent: 'from-cyan-400 to-sky-500',
  },
  {
    step: 'B',
    title: '模型只看最近的一段',
    body: '下一次回答时，nanobot不会把全部历史都塞给模型，只拿最近还没整理过的那一段，再加上长期记忆文件。',
    accent: 'from-blue-500 to-indigo-500',
  },
  {
    step: 'C',
    title: '太长了就压缩成长期记忆',
    body: '当最近对话积累太多，nanobot会把旧内容总结成两份文件：`MEMORY.md` 保存稳定事实，`HISTORY.md` 保存可搜索摘要。',
    accent: 'from-emerald-500 to-teal-500',
  },
];

function ArchitectureGraph() {
  return (
    <section className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div className="space-y-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Structural graph</p>
          <h2
            className="text-3xl font-semibold tracking-[-0.05em] text-slate-950 md:text-4xl"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            Watch the memory mechanism as a system
          </h2>
        </div>
        <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-white/85 px-4 py-2 text-xs text-slate-500 md:inline-flex">
          hot context
          <ArrowRight size={14} />
          consolidation
          <ArrowRight size={14} />
          durable files
        </div>
      </div>

      <div className="relative overflow-hidden rounded-[2.25rem] border border-slate-200 bg-slate-950 p-5 text-white shadow-[0_30px_100px_rgba(15,23,42,0.18)] md:p-7">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(56,189,248,0.20),transparent_28%),radial-gradient(circle_at_top_right,rgba(129,140,248,0.22),transparent_30%),radial-gradient(circle_at_bottom,rgba(16,185,129,0.18),transparent_35%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.06)_1px,transparent_1px)] bg-[size:4.75rem_4.75rem] opacity-60" />

        <div className="relative z-10 mb-5 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.28em] text-cyan-200/70">nanobot memory topology</p>
            <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em]" style={{ fontFamily: 'var(--font-display)' }}>
              Short-term stays hot. Long-term stays inspectable.
            </h3>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/6 px-4 py-2 text-xs text-white/65">
            <Sparkles size={14} className="text-cyan-300" />
            animated data flow
          </div>
        </div>

        <div className="grid gap-3 md:hidden">
          {graphNodes.map((node, index) => {
            const Icon = node.icon;

            return (
              <motion.div
                key={node.id}
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ delay: index * 0.05 }}
                className="rounded-[1.5rem] border border-white/10 bg-white/7 p-4"
              >
                <div className="flex items-center gap-3">
                  <div className={`rounded-2xl bg-gradient-to-br ${node.accent} p-3 text-white`}>
                    <Icon size={18} />
                  </div>
                  <div>
                    <h4 className="font-semibold tracking-[-0.03em] text-white">{node.title}</h4>
                    <p className="text-xs uppercase tracking-[0.18em] text-white/45">{node.caption}</p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        <div className="relative hidden h-[42rem] md:block">
          <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
            <defs>
              <filter id="softGlow">
                <feGaussianBlur stdDeviation="0.8" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {graphEdges.map((edge) => (
              <g key={`${edge.from.join('-')}-${edge.to.join('-')}`}>
                <line
                  x1={edge.from[0]}
                  y1={edge.from[1]}
                  x2={edge.to[0]}
                  y2={edge.to[1]}
                  stroke={edge.color}
                  strokeOpacity="0.32"
                  strokeWidth="0.35"
                  strokeDasharray="0.75 1.15"
                />
                <motion.circle
                  r="0.72"
                  fill={edge.color}
                  filter="url(#softGlow)"
                  animate={{
                    cx: [edge.from[0], edge.to[0]],
                    cy: [edge.from[1], edge.to[1]],
                    opacity: [0, 1, 1, 0],
                    scale: [0.6, 1, 1, 0.6],
                  }}
                  transition={{
                    duration: 3.4,
                    repeat: Infinity,
                    repeatDelay: 0.35,
                    ease: 'linear',
                    delay: edge.delay,
                  }}
                />
                <motion.circle
                  r="0.44"
                  fill="white"
                  animate={{
                    cx: [edge.from[0], edge.to[0]],
                    cy: [edge.from[1], edge.to[1]],
                    opacity: [0, 0.75, 0.75, 0],
                  }}
                  transition={{
                    duration: 3.4,
                    repeat: Infinity,
                    repeatDelay: 0.35,
                    ease: 'linear',
                    delay: edge.delay + 0.22,
                  }}
                />
              </g>
            ))}
          </svg>

          {graphNodes.map((node, index) => {
            const Icon = node.icon;

            return (
              <motion.div
                key={node.id}
                initial={{ opacity: 0, scale: 0.92, y: 18 }}
                whileInView={{ opacity: 1, scale: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ type: 'spring', stiffness: 130, damping: 18, delay: index * 0.05 }}
                className="absolute w-[13.5rem] -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${node.x}%`, top: `${node.y}%` }}
              >
                <motion.div
                  animate={{
                    boxShadow: [
                      `0 0 0 0 ${node.glow}`,
                      `0 0 0 14px rgba(255,255,255,0)`,
                      `0 0 0 0 rgba(255,255,255,0)`,
                    ],
                  }}
                  transition={{
                    duration: 3.2,
                    repeat: Infinity,
                    delay: index * 0.28,
                    ease: 'easeOut',
                  }}
                  className="rounded-[1.6rem] border border-white/10 bg-slate-900/88 p-4 backdrop-blur"
                >
                  <div className="flex items-start gap-3">
                    <div className={`rounded-2xl bg-gradient-to-br ${node.accent} p-3 text-white shadow-lg`}>
                      <Icon size={18} />
                    </div>
                    <div className="min-w-0">
                      <h4 className="text-base font-semibold tracking-[-0.03em] text-white">{node.title}</h4>
                      <p className="mt-1 text-[11px] uppercase tracking-[0.22em] text-white/45">{node.caption}</p>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            );
          })}

          <div className="absolute left-[7%] top-[5%] rounded-full border border-cyan-300/18 bg-cyan-300/10 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-100/75">
            request path
          </div>
          <div className="absolute left-[37%] top-[57%] rounded-full border border-fuchsia-300/18 bg-fuchsia-300/10 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-fuchsia-100/75">
            background consolidation
          </div>
          <div className="absolute left-[60%] top-[81%] rounded-full border border-amber-300/18 bg-amber-300/10 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-50/75">
            grep/manual recall only
          </div>
        </div>
      </div>
    </section>
  );
}

export default function AgentMechanism({ onBack }: AgentMechanismProps) {
  const [mode, setMode] = useState<ExplainMode>('learn');

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen overflow-hidden bg-[var(--paper)] text-slate-950">
      <div className="pointer-events-none fixed inset-0 opacity-95">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.18),transparent_30%),radial-gradient(circle_at_top_right,rgba(59,130,246,0.12),transparent_28%),radial-gradient(circle_at_bottom,rgba(16,185,129,0.10),transparent_30%),linear-gradient(180deg,rgba(255,255,255,0.9),rgba(241,246,252,1))]" />
        <motion.div
          animate={{ opacity: [0.3, 0.45, 0.3] }}
          transition={{ duration: 5.5, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute inset-0 bg-[linear-gradient(to_right,rgba(15,23,42,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(15,23,42,0.06)_1px,transparent_1px)] bg-[size:5.25rem_5.25rem] [mask-image:linear-gradient(to_bottom,rgba(0,0,0,0.9),rgba(0,0,0,0.12))]"
        />
      </div>

      <nav className="sticky top-0 z-50 border-b border-white/60 bg-white/72 backdrop-blur-2xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 md:px-8">
          <button
            onClick={onBack}
            className="group inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-slate-300 hover:text-slate-950"
          >
            <ChevronLeft size={16} className="transition group-hover:-translate-x-0.5" />
            Dashboard Demo
          </button>

          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/82 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_0_6px_rgba(74,222,128,0.12)]" />
            Nanobot Agent Memory
          </div>
        </div>
      </nav>

      <main className="relative z-10 mx-auto flex max-w-6xl flex-col gap-16 px-5 py-10 md:px-8 md:py-14">
        <section className="grid gap-8 lg:grid-cols-[1.03fr_0.97fr] lg:items-stretch">
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center gap-3 rounded-full border border-slate-200 bg-white/85 px-4 py-2 text-xs font-semibold uppercase tracking-[0.26em] text-slate-500 shadow-sm"
            >
              <ShieldCheck size={14} className="text-cyan-600" />
              learn mode first
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.04 }}
              className="max-w-4xl text-5xl font-semibold leading-[0.93] tracking-[-0.065em] text-slate-950 md:text-7xl"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              Learn nanobot memory by watching the data move.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="max-w-2xl text-base leading-8 text-slate-600 md:text-lg"
            >
              This view turns the memory mechanism into a structural graph: you can see raw turns enter short-term
              session history, prompt assembly happen on the live stack, and consolidation push old context into local
              long-term memory files.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.12 }}
              className="inline-flex w-fit rounded-full border border-slate-200 bg-white/88 p-1 shadow-sm"
            >
              <button
                onClick={() => setMode('learn')}
                className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                  mode === 'learn' ? 'bg-slate-950 text-white' : 'text-slate-600 hover:text-slate-950'
                }`}
              >
                Learn Mode
              </button>
              <button
                onClick={() => setMode('graph')}
                className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                  mode === 'graph' ? 'bg-slate-950 text-white' : 'text-slate-600 hover:text-slate-950'
                }`}
              >
                Graph Mode
              </button>
            </motion.div>

            <div className="grid gap-4 md:grid-cols-2">
              {implementationFacts.slice(0, 2).map((fact, index) => (
                <motion.article
                  key={fact.title}
                  initial={{ opacity: 0, y: 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.14 + index * 0.05 }}
                  className="rounded-[1.7rem] border border-slate-200 bg-white/82 p-5 shadow-[0_14px_36px_rgba(15,23,42,0.06)]"
                >
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">{fact.title}</p>
                  <h2 className="mt-3 text-4xl font-semibold tracking-[-0.05em] text-slate-950">{fact.value}</h2>
                  <p className="mt-3 text-sm leading-6 text-slate-600">{fact.note}</p>
                </motion.article>
              ))}
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.18 }}
            className="relative overflow-hidden rounded-[2.2rem] border border-slate-200 bg-slate-950 p-6 text-white shadow-[0_34px_100px_rgba(15,23,42,0.18)]"
          >
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.28),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(16,185,129,0.18),transparent_38%)]" />
            <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.06)_1px,transparent_1px)] bg-[size:4.5rem_4.5rem] opacity-55" />

            <div className="relative z-10 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.28em] text-cyan-200/78">Live stack</p>
                  <h2 className="mt-2 text-2xl font-semibold tracking-[-0.04em]" style={{ fontFamily: 'var(--font-display)' }}>
                    What the model actually sees
                  </h2>
                </div>
                <Workflow className="text-cyan-300" size={28} />
              </div>

              <div className="space-y-3">
                {[
                  'bootstrap files and identity',
                  'MEMORY.md long-term facts',
                  'recent unconsolidated session turns',
                  'runtime metadata block',
                  'current user message',
                ].map((item, index) => (
                  <motion.div
                    key={item}
                    initial={{ opacity: 0, x: -14 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 + index * 0.06 }}
                    className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/7 px-4 py-3"
                  >
                    <motion.div
                      animate={{ x: ['-110%', '120%'] }}
                      transition={{ duration: 3.8, repeat: Infinity, repeatDelay: 1.2, ease: 'easeInOut', delay: index * 0.28 }}
                      className="absolute inset-y-0 w-20 bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.16),transparent)]"
                    />
                    <div className="relative flex items-center justify-between">
                      <span className="text-sm text-white/82">{item}</span>
                      <span className="rounded-full bg-white/10 px-2.5 py-1 text-[11px] font-semibold tracking-[0.22em] text-white/55">
                        {String(index + 1).padStart(2, '0')}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {implementationFacts.slice(2).map((fact) => (
                  <div key={fact.title} className="rounded-2xl border border-white/10 bg-white/6 p-4">
                    <p className="text-[11px] uppercase tracking-[0.24em] text-white/45">{fact.title}</p>
                    <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-white">{fact.value}</h3>
                    <p className="mt-2 text-sm leading-6 text-white/68">{fact.note}</p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </section>

        {mode === 'learn' ? (
          <section className="space-y-8">
            <div className="space-y-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Plain explanation</p>
              <h2
                className="text-3xl font-semibold tracking-[-0.05em] text-slate-950 md:text-4xl"
                style={{ fontFamily: 'var(--font-display)' }}
              >
                先只看 3 件事
              </h2>
              <p className="max-w-3xl text-base leading-8 text-slate-600">
                如果把 nanobot 想成一个人在工作，它其实只做三件事：先记最近的话，再把最近的话拿去回答，最后把太旧的内容压缩存档。
              </p>
            </div>

            <div className="grid gap-5 lg:grid-cols-3">
              {learnSteps.map((item, index) => (
                <motion.article
                  key={item.step}
                  initial={{ opacity: 0, y: 18 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.25 }}
                  transition={{ delay: index * 0.06 }}
                  className="relative overflow-hidden rounded-[2rem] border border-slate-200 bg-white/88 p-6 shadow-[0_18px_50px_rgba(15,23,42,0.07)]"
                >
                  <div className={`absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r ${item.accent}`} />
                  <div className="mb-5 flex items-center justify-between">
                    <span className="rounded-full bg-slate-950 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-white">
                      {item.step}
                    </span>
                  </div>
                  <h3 className="text-2xl font-semibold tracking-[-0.04em] text-slate-950">{item.title}</h3>
                  <p className="mt-4 text-sm leading-7 text-slate-600">{item.body}</p>
                </motion.article>
              ))}
            </div>

            <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
              <motion.article
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.25 }}
                className="rounded-[2rem] border border-slate-200 bg-slate-950 p-6 text-white shadow-[0_24px_70px_rgba(15,23,42,0.16)]"
              >
                <p className="text-[11px] uppercase tracking-[0.28em] text-cyan-200/70">一句话版</p>
                <p className="mt-4 text-xl leading-9 text-white/90">
                  短期记忆 = 最近原始对话。
                  <br />
                  长期记忆 = 从旧对话里提炼出来的事实和摘要。
                </p>
              </motion.article>

              <motion.article
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.25 }}
                className="rounded-[2rem] border border-slate-200 bg-white/88 p-6 shadow-[0_18px_50px_rgba(15,23,42,0.07)]"
              >
                <p className="text-[11px] uppercase tracking-[0.28em] text-slate-400">对应文件</p>
                <div className="mt-4 space-y-3 text-sm leading-7 text-slate-600">
                  <div><strong className="text-slate-950">短期：</strong>`sessions/*.jsonl`</div>
                  <div><strong className="text-slate-950">长期事实：</strong>`memory/MEMORY.md`</div>
                  <div><strong className="text-slate-950">长期摘要：</strong>`memory/HISTORY.md`</div>
                </div>
              </motion.article>
            </div>
          </section>
        ) : (
          <ArchitectureGraph />
        )}

        <section className="space-y-8">
          <div className="flex items-end justify-between gap-4">
            <div className="space-y-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Motion narrative</p>
              <h2
                className="text-3xl font-semibold tracking-[-0.05em] text-slate-950 md:text-4xl"
                style={{ fontFamily: 'var(--font-display)' }}
              >
                A single conversation turn moving through the agent
              </h2>
            </div>
            <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-white/85 px-4 py-2 text-xs text-slate-500 md:inline-flex">
              one turn
              <ArrowRight size={14} />
              active context
              <ArrowRight size={14} />
              durable memory
            </div>
          </div>

          <div className="relative">
            <div className="absolute left-5 top-0 hidden h-full w-px bg-gradient-to-b from-cyan-300 via-indigo-300 to-emerald-300 md:block" />
            <div className="space-y-5">
              {flowStages.map((stage, index) => {
                const Icon = stage.icon;

                return (
                  <motion.article
                    key={stage.step}
                    initial={{ opacity: 0, y: 22 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0.28 }}
                    transition={{ duration: 0.55, delay: index * 0.05 }}
                    className="relative rounded-[2rem] border border-slate-200 bg-white/84 p-6 shadow-[0_16px_44px_rgba(15,23,42,0.07)] md:ml-12"
                  >
                    <motion.div
                      animate={{ scale: [1, 1.18, 1], opacity: [0.8, 1, 0.8] }}
                      transition={{ duration: 2.8, repeat: Infinity, delay: index * 0.24 }}
                      className="absolute left-[-2.95rem] top-8 hidden h-5 w-5 rounded-full border border-white bg-slate-950 shadow-[0_0_0_8px_rgba(255,255,255,0.9)] md:block"
                    />
                    <div className={`absolute inset-x-0 top-0 h-1.5 rounded-t-[2rem] bg-gradient-to-r ${stage.accent}`} />
                    <div className="grid gap-6 md:grid-cols-[auto_1fr] md:items-start">
                      <div className="flex items-center gap-4 md:block">
                        <div className={`inline-flex rounded-[1.5rem] bg-gradient-to-br ${stage.accent} p-4 text-white shadow-lg`}>
                          <Icon size={20} />
                        </div>
                        <div className="md:mt-4">
                          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">{stage.step}</p>
                          <p className="mt-1 text-sm font-medium text-slate-500">animated phase</p>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <h3 className="text-2xl font-semibold tracking-[-0.04em] text-slate-950">{stage.title}</h3>
                        <p className="max-w-3xl text-sm leading-7 text-slate-600 md:text-[15px]">{stage.body}</p>
                        <div className="relative mt-4 h-3 overflow-hidden rounded-full bg-slate-100">
                          <motion.div
                            animate={{ x: ['-12%', '104%'] }}
                            transition={{ duration: 2.9, repeat: Infinity, ease: 'easeInOut', delay: index * 0.24 }}
                            className={`absolute inset-y-0 w-28 rounded-full bg-gradient-to-r ${stage.accent}`}
                          />
                        </div>
                      </div>
                    </div>
                  </motion.article>
                );
              })}
            </div>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-5 rounded-[2rem] border border-slate-200 bg-white/84 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.07)]">
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Memory split</p>
              <h2
                className="text-3xl font-semibold tracking-[-0.05em] text-slate-950"
                style={{ fontFamily: 'var(--font-display)' }}
              >
                Short-term and long-term do different jobs
              </h2>
            </div>

            <div className="grid gap-4">
              {distinctions.map((item, index) => (
                <motion.article
                  key={item.label}
                  initial={{ opacity: 0, y: 18 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.25 }}
                  transition={{ delay: index * 0.06 }}
                  className={`rounded-[1.6rem] border p-5 ${item.tone}`}
                >
                  <p className="text-[11px] font-semibold uppercase tracking-[0.26em] text-slate-500">{item.label}</p>
                  <h3 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-slate-950">{item.title}</h3>
                  <p className="mt-3 text-sm leading-7 text-slate-600">{item.body}</p>
                  <div className="mt-5 flex flex-wrap gap-2">
                    {item.chips.map((chip) => (
                      <span
                        key={chip}
                        className="rounded-full border border-slate-300/70 bg-white/72 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500"
                      >
                        {chip}
                      </span>
                    ))}
                  </div>
                </motion.article>
              ))}
            </div>
          </div>

          <div className="space-y-5 rounded-[2rem] border border-slate-200 bg-slate-950 p-6 text-white shadow-[0_22px_60px_rgba(15,23,42,0.16)]">
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-white/45">What this is not</p>
              <h2 className="text-3xl font-semibold tracking-[-0.05em]" style={{ fontFamily: 'var(--font-display)' }}>
                No hidden vector memory layer here
              </h2>
            </div>

            <div className="rounded-[1.6rem] border border-white/10 bg-white/6 p-5">
              <p className="text-sm leading-7 text-white/80">
                The current nanobot memory path is explicit and inspectable. It does not use embeddings, a vector
                database, or automatic semantic retrieval for this mechanism. Durable recall is handled through local
                files plus grep-friendly summaries.
              </p>
            </div>

            <div className="rounded-[1.6rem] border border-emerald-400/20 bg-emerald-400/10 p-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-emerald-200">Privacy stance</p>
              <p className="mt-3 text-sm leading-7 text-emerald-50/90">
                Provider requests are configured with storage disabled, so long-term memory stays a local workspace
                concern rather than an opaque provider-side feature.
              </p>
            </div>

            <div className="space-y-3">
              {[
                'provider requests use `store: false`',
                '`MEMORY.md` is injected into future prompts',
                '`HISTORY.md` stays persisted for grep-based recall',
                'session JSONL preserves raw chronology',
              ].map((item, index) => (
                <motion.div
                  key={item}
                  initial={{ opacity: 0, x: -14 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, amount: 0.25 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/4 px-4 py-3 text-sm text-white/82"
                >
                  <span className="h-2.5 w-2.5 rounded-full bg-cyan-300" />
                  {item}
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section className="space-y-6">
          <div className="space-y-2">
            <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Where memory lives</p>
            <h2
              className="text-3xl font-semibold tracking-[-0.05em] text-slate-950 md:text-4xl"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              Three artifacts make the mechanism inspectable
            </h2>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {filePanels.map((panel, index) => {
              const Icon = panel.icon;

              return (
                <motion.article
                  key={panel.title}
                  initial={{ opacity: 0, y: 18 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.25 }}
                  transition={{ delay: index * 0.05 }}
                  className="rounded-[1.8rem] border border-slate-200 bg-white/84 p-6 shadow-[0_16px_40px_rgba(15,23,42,0.06)]"
                >
                  <div className="mb-5 flex items-center gap-3">
                    <div className="rounded-2xl bg-slate-950 p-3 text-cyan-300">
                      <Icon size={18} />
                    </div>
                    <h3 className="text-lg font-semibold tracking-[-0.04em] text-slate-950">{panel.title}</h3>
                  </div>
                  <p className="text-sm leading-7 text-slate-600">{panel.text}</p>
                </motion.article>
              );
            })}
          </div>
        </section>
      </main>
    </div>
  );
}
