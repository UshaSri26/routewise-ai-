export default function Methodology() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-[#F1F5F9]">Methodology</h1>
        <p className="text-sm text-[#93A4B8] mt-1">
          How RouteWise AI scores, normalizes, and selects routes.
        </p>
      </div>

      <Section title="1. Multi-Criteria Decision Analysis (MCDA)">
        <p>
          RouteWise AI uses a deterministic weighted-sum MCDA model. Each route is scored
          across three criteria — cost, transit time, and composite risk — then combined
          using user-specified weights. The default is 40% cost, 30% time, and 30% risk.
        </p>
        <Formula>
          S(r) = w_cost · ñ_cost(r) + w_time · ñ_time(r) + w_risk · ñ_risk(r)
        </Formula>
        <p>
          A <em>lower</em> score is better. The recommended route is the feasible route with the
          minimum weighted score.
        </p>
      </Section>

      <Section title="2. Min-Max Normalization">
        <p>
          Cost, transit time, and composite risk are normalized across every candidate for
          the selected shipment (including routes marked infeasible), so different units are
          comparable. Scores are lane-relative, not comparable between shipments:
        </p>
        <Formula>
          ñ(x) = (x − min) / (max − min + ε)
        </Formula>
        <p>
          ε = 1×10⁻⁶ prevents division by zero when all routes share the same value for a criterion.
          In that equal-value case the optimizer assigns zero to that normalized criterion for all routes.
        </p>
      </Section>

      <Section title="3. Composite Risk Index">
        <p>A single risk metric is computed from three sub-indicators:</p>
        <Formula>
          Risk(r) = 0.4 × delay_prob + 0.3 × (congestion / 100) + 0.3 × (geopolitical / 100)
        </Formula>
        <p>
          Delay probability is in [0, 1]; congestion and geopolitical indicators are in [0, 100].
          This composite is a synthetic planning index, not a calibrated probability of loss, and
          is min-max normalized before entering the MCDA score.
        </p>
      </Section>

      <Section title="4. Hard Constraints">
        <p>Routes exceeding any supplied hard constraint are marked infeasible before ranking:</p>
        <ul className="list-disc list-inside space-y-1 text-[#93A4B8]">
          <li><code>max_budget</code> — route cost must not exceed this USD amount</li>
          <li><code>max_days</code> — transit days must not exceed this limit</li>
          <li><code>max_risk</code> — composite risk must not exceed this threshold</li>
        </ul>
        <p>
          If no feasible routes exist, the optimizer returns the best-effort result from all
          routes, clearly flagged as infeasible. It prefers the route with the fewest violated
          limits, then the lowest weighted score.
        </p>
      </Section>

      <Section title="5. Pareto Dominance">
        <p>
          A route <em>dominates</em> another if it is at least as good on all three criteria and
          strictly better on at least one:
        </p>
        <Formula>
          r₁ ≺ r₂ ⟺ cost(r₁) ≤ cost(r₂) ∧ time(r₁) ≤ time(r₂) ∧ risk(r₁) ≤ risk(r₂)
          ∧ (at least one strict inequality)
        </Formula>
        <p>
          Routes not dominated by any other route form the Pareto frontier and are flagged
          with the ◆ Pareto badge in results.
        </p>
      </Section>

      <Section title="6. Sensitivity Analysis">
        <p>
          Four standardized weight profiles test how the recommendation changes under different
          business priorities. The optimizer uses these profiles in both the React and Streamlit
          scenario views:
        </p>
        <div className="grid grid-cols-2 gap-3 mt-3">
          {[
            { name: 'Balanced', w: '0.40 / 0.30 / 0.30' },
            { name: 'Cost-Focused', w: '0.70 / 0.15 / 0.15' },
            { name: 'Time-Critical', w: '0.15 / 0.70 / 0.15' },
            { name: 'Risk-Averse', w: '0.15 / 0.15 / 0.70' },
          ].map((p) => (
            <div key={p.name} className="bg-[#0A1626] rounded-lg border border-[#22344A] px-4 py-3">
              <div className="text-sm font-semibold text-[#21D4C2] mb-1">{p.name}</div>
              <div className="text-xs text-[#93A4B8]">Cost / Time / Risk = {p.w}</div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="7. AI Explanation Engine">
        <p>
          The React/FastAPI recommendation explanation is generated deterministically from the
          optimizer result. The optional Streamlit Gemini integration is a separate explanation
          feature; it does not select the route. No API key is required for the primary demo.
        </p>
      </Section>

      <Section title="8. Dataset">
        <p>
          The dataset is <strong>fully synthetic</strong>. It is generated deterministically from a
          fixed seed and contains 30 shipment lanes × 4 route alternatives = 120 options:
        </p>
        <ul className="list-disc list-inside space-y-1 text-[#93A4B8]">
          <li>18 domestic India lanes use rail parcel, surface truck, express road, and priority road/air options.</li>
          <li>12 international lanes use standard ocean, express ocean, resilient ocean, and air options.</li>
          <li>Price and transit estimates are synthetic small-shipment planning assumptions, not carrier quotes.</li>
        </ul>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card space-y-3">
      <h2 className="text-base font-bold text-[#F1F5F9] pb-2 border-b border-[#22344A]">{title}</h2>
      <div className="text-sm text-[#93A4B8] leading-relaxed space-y-3">{children}</div>
    </div>
  );
}

function Formula({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-[#0A1626] border border-[#22344A] rounded-lg px-4 py-3 font-mono text-xs text-[#21D4C2] overflow-x-auto">
      {children}
    </div>
  );
}
