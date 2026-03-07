import { useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  BrainCircuit,
  ChevronLeft,
  Database,
  FileClock,
  FileSearch,
  FolderKanban,
  Layers3,
  MessagesSquare,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';

interface AgentMechanismProps {
  onBack: () => void;
}

interface FlowStage {
  step: string;
  title: string;
  body: string;
  accent: string;
  icon: typeof MessagesSquare;
}

const flowStages: FlowStage[] = [
  {
    step: '01',
    title: 'Short-term turns land in a session file',
    body:
      'Each conversation is tracked as a channel-scoped session. Raw user, assistant, and tool messages are appended to JSONL so the latest turn history stays durable and replayable.',
    accent: 'from-cyan-500 to-sky-500',
    icon: MessagesSquare,
  },
  {
    step: '02',
    title: 'Prompt assembly pulls in the live working set',
    body:
      'Nanobot builds the next prompt from bootstrap files, long-term memory, and the unconsolidated tail of session history. That tail is the active short-term context.',
    accent: 'from-blue-500 to-indigo-500',
    icon: Layers3,
  },
  {
    step: '03',
    title: 'A consolidation threshold watches the backlog',
    body:
      'When unconsolidated history reaches the configured memory window, nanobot starts a background consolidation pass instead of shoving the full backlog into every prompt.',
    accent: 'from-violet-500 to-fuchsia-500',
    icon: RefreshCw,
  },
  {
    step: '04',
    title: 'An LLM compresses old turns into durable memory',
    body:
      'The consolidator summarizes older turns into a grep-friendly history entry and a rewritten long-term memory document. Newer turns stay hot; older turns get compacted.',
    accent: 'from-amber-500 to-orange-500',
    icon: BrainCircuit,
  },
  {
    step: '05',
    title: 'Long-term memory stays local and explicit',
    body:
      'Important stable facts go into MEMORY.md and are loaded on future prompts. HISTORY.md stays on disk for search and audit, but it is not injected wholesale into the model context.',
    accent: 'from-emerald-500 to-teal-500',
    icon: Database,
  },
];

const distinctions = [
  {
    label: 'Short-term memory',
    title: 'Session tail in `sessions/*.jsonl`',
    body:
      'This is the model’s working memory. It contains the latest unconsolidated user, assistant, and tool messages, aligned to recent turns.',
    chips: ['default window: 100', 'raw turns', 'loaded into prompt'],
    tone: 'border-cyan-200 bg-cyan-50/80',
  },
  {
    label: 'Long-term memory',
    title: '`memory/MEMORY.md` plus `memory/HISTORY.md`',
    body:
      'This is the durable memory layer. `MEMORY.md` holds stable facts and preferences; `HISTORY.md` stores timestamped summaries for manual or grep-based recall.',
    chips: ['local files', 'summarized facts', 'history not auto-loaded'],
    tone: 'border-emerald-200 bg-emerald-50/80',
  },
];

const implementationFacts = [
  {
    title: 'Trigger threshold',
    value: '100 messages',
    note: 'Configured as `memory_window` in agent defaults.',
  },
  {
    title: 'Hot context after consolidation',
    value: 'Newest ~50 kept raw',
    note: 'The consolidator keeps roughly half the window as live short-term history.',
  },
  {
    title: 'Provider-side retention',
    value: 'Disabled',
    note: 'Responses-style providers send requests with `store: false`.',
  },
  {
    title: 'Recall mode',
    value: 'File + grep',
    note: 'No vector DB or embedding retrieval is wired into this memory path.',
  },
];

const filePanels = [
  {
    title: 'sessions/<chat>.jsonl',
    text: 'Append-only conversation log. This is where the raw turns live before and after consolidation.',
    icon: FolderKanban,
  },
  {
    title: 'memory/MEMORY.md',
    text: 'Curated long-term memory. It gets injected into the system prompt on future requests.',
    icon: FileClock,
  },
  {
    title: 'memory/HISTORY.md',
    text: 'Timestamped summaries of older exchanges. Stored for search and audit rather than automatic prompt loading.',
    icon: FileSearch,
  },
];

export default function AgentMechanism({ onBack }: AgentMechanismProps) {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen overflow-hidden bg-[var(--paper)] text-slate-950">
      <div className="pointer-events-none fixed inset-0 opacity-90">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.18),transparent_30%),radial-gradient(circle_at_top_right,rgba(59,130,246,0.14),transparent_25%),linear-gradient(180deg,rgba(255,255,255,0.84),rgba(242,246,252,0.98))]" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(15,23,42,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(15,23,42,0.06)_1px,transparent_1px)] bg-[size:5.25rem_5.25rem] [mask-image:linear-gradient(to_bottom,rgba(0,0,0,0.9),rgba(0,0,0,0.25))]" />
      </div>

      <nav className="sticky top-0 z-50 border-b border-white/60 bg-white/70 backdrop-blur-2xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 md:px-8">
          <button
            onClick={onBack}
            className="group inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-slate-300 hover:text-slate-950"
          >
            <ChevronLeft size={16} className="transition group-hover:-translate-x-0.5" />
            Dashboard Demo
          </button>

          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_0_6px_rgba(74,222,128,0.12)]" />
            Nanobot Agent Memory
          </div>
        </div>
      </nav>

      <main className="relative z-10 mx-auto flex max-w-6xl flex-col gap-16 px-5 py-10 md:px-8 md:py-14">
        <section className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center gap-3 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-xs font-semibold uppercase tracking-[0.26em] text-slate-500 shadow-sm"
            >
              <ShieldCheck size={14} className="text-cyan-600" />
              File-based memory, not a black box
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="max-w-4xl text-5xl font-semibold leading-[0.95] tracking-[-0.06em] text-slate-950 md:text-7xl"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              How nanobot remembers a conversation after the prompt is gone.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="max-w-2xl text-base leading-8 text-slate-600 md:text-lg"
            >
              Nanobot currently uses a two-layer memory mechanism: raw recent turns for short-term reasoning, then
              local file consolidation for durable context. Older turns are compressed, stable facts are retained, and
              provider-side storage is explicitly turned off.
            </motion.p>
          </div>

          <motion.div
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.15 }}
            className="relative overflow-hidden rounded-[2rem] border border-slate-200 bg-slate-950 p-6 text-white shadow-[0_30px_80px_rgba(15,23,42,0.18)]"
          >
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.32),transparent_45%),radial-gradient(circle_at_bottom_right,rgba(52,211,153,0.22),transparent_32%)]" />
            <div className="relative space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.28em] text-cyan-200/80">Live Prompt Stack</p>
                  <h2 className="mt-2 text-2xl font-semibold tracking-[-0.04em]" style={{ fontFamily: 'var(--font-display)' }}>
                    Active context on each turn
                  </h2>
                </div>
                <BrainCircuit className="text-cyan-300" size={28} />
              </div>

              <div className="space-y-3">
                {['Bootstrap files', 'MEMORY.md', 'Latest unconsolidated session turns', 'Runtime metadata', 'Current user message'].map((item, index) => (
                  <div
                    key={item}
                    className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/6 px-4 py-3"
                  >
                    <span className="text-sm text-white/80">{item}</span>
                    <span className="rounded-full bg-white/10 px-2.5 py-1 text-[11px] font-semibold tracking-[0.22em] text-white/60">
                      {String(index + 1).padStart(2, '0')}
                    </span>
                  </div>
                ))}
              </div>

              <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm leading-6 text-cyan-50">
                Result: recent reasoning stays fast, while older context gets compressed into durable memory files.
              </div>
            </div>
          </motion.div>
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {implementationFacts.map((fact, index) => (
            <motion.article
              key={fact.title}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + index * 0.05 }}
              className="rounded-[1.75rem] border border-slate-200 bg-white/80 p-5 shadow-[0_12px_30px_rgba(15,23,42,0.06)] backdrop-blur"
            >
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">{fact.title}</p>
              <h3 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-slate-950">{fact.value}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{fact.note}</p>
            </motion.article>
          ))}
        </section>

        <section className="space-y-8">
          <div className="flex items-end justify-between gap-4">
            <div className="space-y-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Agent memory flow</p>
              <h2 className="text-3xl font-semibold tracking-[-0.05em] text-slate-950 md:text-4xl" style={{ fontFamily: 'var(--font-display)' }}>
                From raw turns to durable recall
              </h2>
            </div>
            <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-xs text-slate-500 md:inline-flex">
              recent turns stay hot
              <ArrowRight size={14} />
              older turns get compressed
            </div>
          </div>

          <div className="grid gap-5 xl:grid-cols-5">
            {flowStages.map((stage, index) => {
              const Icon = stage.icon;

              return (
                <motion.article
                  key={stage.step}
                  initial={{ opacity: 0, y: 22 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.18 + index * 0.06 }}
                  className="relative overflow-hidden rounded-[1.9rem] border border-slate-200 bg-white/85 p-6 shadow-[0_18px_50px_rgba(15,23,42,0.08)]"
                >
                  <div className={`absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r ${stage.accent}`} />
                  <div className="mb-8 flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">{stage.step}</p>
                      <h3 className="mt-3 text-xl font-semibold leading-tight tracking-[-0.04em] text-slate-950">
                        {stage.title}
                      </h3>
                    </div>
                    <div className={`rounded-2xl bg-gradient-to-br ${stage.accent} p-3 text-white shadow-lg`}>
                      <Icon size={18} />
                    </div>
                  </div>
                  <p className="text-sm leading-7 text-slate-600">{stage.body}</p>
                </motion.article>
              );
            })}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-5 rounded-[2rem] border border-slate-200 bg-white/80 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.07)]">
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Memory split</p>
              <h2 className="text-3xl font-semibold tracking-[-0.05em] text-slate-950" style={{ fontFamily: 'var(--font-display)' }}>
                Short-term and long-term do different jobs
              </h2>
            </div>

            <div className="grid gap-4">
              {distinctions.map((item) => (
                <article key={item.label} className={`rounded-[1.6rem] border p-5 ${item.tone}`}>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.26em] text-slate-500">{item.label}</p>
                  <h3 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-slate-950">{item.title}</h3>
                  <p className="mt-3 text-sm leading-7 text-slate-600">{item.body}</p>
                  <div className="mt-5 flex flex-wrap gap-2">
                    {item.chips.map((chip) => (
                      <span
                        key={chip}
                        className="rounded-full border border-slate-300/70 bg-white/70 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500"
                      >
                        {chip}
                      </span>
                    ))}
                  </div>
                </article>
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
              <p className="text-sm leading-7 text-white/78">
                The current nanobot memory path is explicit and inspectable. It does not use embeddings, a vector
                database, or automatic semantic retrieval for this mechanism. Durable recall is handled through local
                files plus grep-friendly summaries.
              </p>
            </div>

            <div className="rounded-[1.6rem] border border-emerald-400/20 bg-emerald-400/10 p-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-emerald-200">Privacy stance</p>
              <p className="mt-3 text-sm leading-7 text-emerald-50/90">
                Responses-style provider calls are made with storage disabled, so long-term memory remains a local
                workspace concern instead of an opaque provider-side feature.
              </p>
            </div>

            <div className="space-y-3">
              {['Provider request uses `store: false`', '`MEMORY.md` is loaded into prompts', '`HISTORY.md` is persisted for grep search', 'Session JSONL keeps raw turn chronology'].map((item) => (
                <div key={item} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/4 px-4 py-3 text-sm text-white/80">
                  <span className="h-2.5 w-2.5 rounded-full bg-cyan-300" />
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="space-y-6">
          <div className="space-y-2">
            <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Where memory lives</p>
            <h2 className="text-3xl font-semibold tracking-[-0.05em] text-slate-950 md:text-4xl" style={{ fontFamily: 'var(--font-display)' }}>
              Three artifacts make the mechanism understandable
            </h2>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {filePanels.map((panel, index) => {
              const Icon = panel.icon;

              return (
                <motion.article
                  key={panel.title}
                  initial={{ opacity: 0, y: 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + index * 0.05 }}
                  className="rounded-[1.8rem] border border-slate-200 bg-white/80 p-6 shadow-[0_16px_40px_rgba(15,23,42,0.06)]"
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
