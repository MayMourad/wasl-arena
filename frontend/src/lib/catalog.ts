/** Mirrors backend/app/rules/souq.py CATALOG (ids, prices). Backend remains the scoring authority. */
export const PRODUCTS: Record<string, { en: string; ar: string; price: number }> = {
  dates: { en: 'Dates', ar: 'تمر', price: 12 },
  coffee: { en: 'Coffee', ar: 'قهوة', price: 18 },
  spices: { en: 'Spices', ar: 'بهارات', price: 15 },
  pottery: { en: 'Pottery', ar: 'فخار', price: 25 },
  textile: { en: 'Textile', ar: 'قماش', price: 30 },
  oud: { en: 'Oud', ar: 'عود', price: 40 },
  honey: { en: 'Honey', ar: 'عسل', price: 20 },
  rosewater: { en: 'Rose water', ar: 'ماء الورد', price: 10 },
}

export const COLOR_SWATCH: Record<string, string> = {
  red: '#C0262F', blue: '#2447C8', purple: '#7B3FA0', orange: '#E07A1F', teal: '#167E80', white: '#EDEDED', yellow: '#E8CF1B',
}

export const RULES = {
  football: [
    ['Valid goal', '+1', 'AI saw the ball enter the calibrated goal zone after being seen outside it'],
    ['Unsupported / unsure goal', '0', 'Marked NEEDS_REVIEW; counts only if the host accepts it'],
    ['Winner', 'Highest score', 'Verified goals only'],
    ['Tie', 'Golden goal', 'First verified goal in the extension wins, otherwise a draw'],
    ['Possession & MVP', 'Longest ball time', 'Team and player with the most observed possession; unobserved time is "unknown"'],
    ['Host penalty', '−1', 'Applied manually by the host and written to the audit log'],
  ],
  falaj: [
    ['Farm watered', '+3', 'Water reaches a destination through matching open tile sides'],
    ['Leak', '−1', 'Water reaches an open channel end with no matching neighbour (rocks, edges, gaps)'],
    ['Speed bonus', 'up to +2', 'All three farms watered: ≤45 s = +2, ≤70 s = +1'],
    ['Round', '90 s', 'The board state when time ends is judged'],
    ['Tie-break', 'Network, then time', 'Shortest valid network wins, then earliest completion'],
  ],
  souq: [
    ['Requested item shown', '+2', 'Right product card shown to the camera'],
    ['Spoken match', '+1', 'Player names the same product within ±5 s of showing it'],
    ['Over budget', '−2', 'Total price of distinct cards exceeds the budget (once)'],
    ['Duplicate', '0', 'Showing the same product again earns nothing and is not paid twice'],
    ['Audio ≠ video', 'Review', 'Said one product, showed another: host decides'],
    ['Tie-break', 'Lower spend, then time', ''],
  ],
} as const
