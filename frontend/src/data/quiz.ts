export interface QuizQuestion {
  id: number
  text: string
  options: { label: string; score: number }[]
}

// Score 0 = cautious indicator, 1 = understanding, 2 = proficient
// Final level: sum maps to cautious (<7), understanding (7-12), proficient (>12) across 10 questions
export const QUIZ_QUESTIONS: QuizQuestion[] = [
  {
    id: 1,
    text: '你衝浪幾年了？',
    options: [
      { label: '還沒開始 / 不到半年', score: 0 },
      { label: '半年到 2 年', score: 1 },
      { label: '2 年以上', score: 2 },
    ],
  },
  {
    id: 2,
    text: '你在浪高多少的浪況下感覺最自在？',
    options: [
      { label: '膝胸以下（1m 以內）', score: 0 },
      { label: '頭高左右（1–1.5m）', score: 1 },
      { label: '頭高以上（1.5m+）', score: 2 },
    ],
  },
  {
    id: 3,
    text: '你曾遇過明顯的離岸流嗎？當時你怎麼應對？',
    options: [
      { label: '沒遇過，或不確定如何辨識', score: 0 },
      { label: '遇過，往沙灘方向用力游', score: 0 },
      { label: '遇過，橫向游離再回岸', score: 2 },
    ],
  },
  {
    id: 4,
    text: '下水前你會查哪些資料？',
    options: [
      { label: '看天氣 App 確認不下雨就好', score: 0 },
      { label: '看浪高和風速', score: 1 },
      { label: '查浪高、週期、風向、潮汐', score: 2 },
    ],
  },
  {
    id: 5,
    text: '波浪週期 12 秒比 6 秒的浪，有什麼主要差異？',
    options: [
      { label: '沒什麼差別', score: 0 },
      { label: '12 秒的浪比較長比較有力', score: 1 },
      { label: '12 秒的浪能量更深、間距大、更難預測', score: 2 },
    ],
  },
  {
    id: 6,
    text: '今天浪高 2m、週期 8s、風速 25 kt 側風。你會？',
    options: [
      { label: '條件挺好的，直接下水', score: 0 },
      { label: '先在岸上觀察 15 分鐘再決定', score: 1 },
      { label: '先評估自己的實力，再找防護較好的位置', score: 2 },
    ],
  },
  {
    id: 7,
    text: '高潮時和低潮時，礁石點的危險程度有什麼不同？',
    options: [
      { label: '潮汐不影響礁石危險程度', score: 0 },
      { label: '低潮時礁石更淺、更危險', score: 1 },
      { label: '需視礁石深度和浪況，不同點情況不同', score: 2 },
    ],
  },
  {
    id: 8,
    text: '你有沒有在下水前，跟岸上的人說你的計畫（你在哪、預計多久）？',
    options: [
      { label: '從來沒想過這件事', score: 0 },
      { label: '偶爾會', score: 1 },
      { label: '每次都有，或單獨衝浪時一定告知', score: 2 },
    ],
  },
  {
    id: 9,
    text: '你在陌生的浪點怎麼判斷是否適合下水？',
    options: [
      { label: '看起來可以就下去', score: 0 },
      { label: '先詢問當地人或確認有救生員', score: 1 },
      { label: '觀察浪型、出入水路線、危險物件後再決定', score: 2 },
    ],
  },
  {
    id: 10,
    text: '你認為「風速突然增大」代表什麼？',
    options: [
      { label: '可能有點麻煩，但衝浪不太受風影響', score: 0 },
      { label: '浪況可能變亂，要注意', score: 1 },
      { label: '表示海況不穩定，且可能有更強的陣風跟浪', score: 2 },
    ],
  },
]
