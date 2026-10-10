interface ScoreBarProps {
  cost: number;
  time: number;
  risk: number;
}

export default function ScoreBar({ cost, time, risk }: ScoreBarProps) {
  const total = cost + time + risk || 1;
  const segments = [
    { label: 'Cost', value: cost, color: '#21D4C2' },
    { label: 'Time', value: time, color: '#76E4D4' },
    { label: 'Risk', value: risk, color: '#34D399' },
  ];

  return (
    <div className="space-y-3">
      <div className="label">Priority Weights</div>
      <div className="flex h-3 rounded-full overflow-hidden gap-0.5">
        {segments.map((s) => (
          <div
            key={s.label}
            style={{ width: `${(s.value / total) * 100}%`, backgroundColor: s.color }}
            className="transition-all duration-300 first:rounded-l-full last:rounded-r-full"
            title={`${s.label}: ${(s.value * 100).toFixed(0)}%`}
          />
        ))}
      </div>
      <div className="flex gap-4">
        {segments.map((s) => (
          <div key={s.label} className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }} />
            <span className="text-xs text-[#93A4B8]">
              {s.label} <span className="font-semibold text-[#F1F5F9]">{(s.value * 100).toFixed(0)}%</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
