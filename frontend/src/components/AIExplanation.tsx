interface AIExplanationProps {
  explanation: string;
}

export default function AIExplanation({ explanation }: AIExplanationProps) {
  const paragraphs = explanation.split('\n').filter((p) => p.trim());

  return (
    <div className="card-elevated space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-[#21D4C2]/15 border border-[#21D4C2]/30 flex items-center justify-center">
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24">
            <path
              d="M12 2L9.5 9H2l5.5 4.5L5.5 21 12 16l6.5 5-2-7.5L22 9h-7.5L12 2Z"
              stroke="#21D4C2"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <div>
          <div className="text-sm font-semibold text-[#F1F5F9]">AI Explanation</div>
          <div className="text-[10px] text-[#93A4B8]">Grounded in optimizer results</div>
        </div>
      </div>

      <div className="space-y-2.5 border-t border-[#22344A] pt-4">
        {paragraphs.map((p, i) => (
          <p key={i} className="text-sm text-[#93A4B8] leading-relaxed">
            {p}
          </p>
        ))}
      </div>
    </div>
  );
}
