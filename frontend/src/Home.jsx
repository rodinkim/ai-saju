import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Home.css'

const CATEGORIES = [
  { id: 'free',   title: '무료 사주', image: '/images/무료/무료사주.webp', icon: '🎁', ratio: '7 / 10' },
  { id: 'wealth', title: '재물 사주', image: '/images/재물/재물사주.webp', icon: '💰', ratio: '7 / 10' },
  { id: 'love',   title: '연애 사주', image: '/images/연애/연애사주.webp', icon: '💕', ratio: '7 / 10' },
]

export default function Home() {
  const navigate = useNavigate()
  const [index, setIndex] = useState(0)

  const prev = () => setIndex(i => (i - 1 + CATEGORIES.length) % CATEGORIES.length)
  const next = () => setIndex(i => (i + 1) % CATEGORIES.length)
  const cat  = CATEGORIES[index]

  return (
    <div className="home-page">

      <header className="home-hero">
        <div className="home-deco"><span />명리학 기반 AI 분석<span /></div>
        <h1 className="home-title">무엇이 <em>궁금</em>하신가요?</h1>
      </header>

      <div className="slider">
        {/* 이전 */}
        <button className="slider-arrow left" onClick={prev} aria-label="이전">
          <iconify-icon icon="solar:arrow-left-bold" />
        </button>

        {/* 카드 */}
        <button
          key={cat.id}
          className="slider-card"
          onClick={() => navigate('/analyze', { state: { category: cat } })}
        >
          <div className="slider-img-wrap" style={{ aspectRatio: cat.ratio }}>
            <img
              src={cat.image}
              alt={cat.title}
              className="slider-img"
              onError={e => { e.currentTarget.style.display = 'none' }}
            />
            <div className="slider-fallback">{cat.icon}</div>
          </div>
        </button>

        {/* 다음 */}
        <button className="slider-arrow right" onClick={next} aria-label="다음">
          <iconify-icon icon="solar:arrow-right-bold" />
        </button>
      </div>

      {/* 인디케이터 */}
      <div className="slider-dots">
        {CATEGORIES.map((c, i) => (
          <button
            key={c.id}
            className={`dot${i === index ? ' active' : ''}`}
            onClick={() => setIndex(i)}
            aria-label={c.title}
          />
        ))}
      </div>

    </div>
  )
}
