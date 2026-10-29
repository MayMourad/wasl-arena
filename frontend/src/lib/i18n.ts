const D: Record<string, { en: string; ar: string }> = {
  'nav.launch': { en: 'Launch', ar: 'البداية' },
  'nav.setup': { en: 'Family Setup', ar: 'إعداد العائلة' },
  'nav.library': { en: 'Games', ar: 'الألعاب' },
  'nav.prepare': { en: 'Prepare', ar: 'التحضير' },
  'nav.arena': { en: 'Live Arena', ar: 'الساحة' },
  'nav.replay': { en: 'AI Referee Replay', ar: 'إعادة الحكم' },
  'nav.cup': { en: 'Family Cup', ar: 'كأس العائلة' },
  'nav.lab': { en: 'Evaluation Lab', ar: 'مختبر التقييم' },
  'hero.title': { en: 'One family. Three games. One fair AI referee.', ar: 'عائلة واحدة. ثلاث ألعاب. حكم ذكي عادل.' },
  'hero.cta': { en: 'Start Family Game Day', ar: 'ابدأ يوم الألعاب العائلي' },
  'hero.sub': { en: 'Real play on camera. Every point backed by evidence you can replay.', ar: 'لعب حقيقي أمام الكاميرا. كل نقطة مدعومة بدليل يمكنك إعادته.' },
}
export const tr = (k: string, lang: 'en' | 'ar') => D[k]?.[lang] ?? D[k]?.en ?? k
