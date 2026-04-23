import { useNavigate } from 'react-router-dom'
import './Home.css'

const CATEGORIES = [
  {
    id: 'love',
    title: '연애 사주',
    sub: '나의 연애 성향과 인연의 흐름',
    icon: '🌸',
    gradient: 'linear-gradient(135deg, #FEF0F6 0%, #EEE8FA 100%)',
    accent: '#C47898',
    image: '/images/연애/연애사주.webp',
  },
  {
    id: 'wealth',
    title: '재물 사주',
    sub: '돈의 흐름과 커리어의 방향',
    icon: '🌿',
    gradient: 'linear-gradient(135deg, #FEF5E8 0%, #FAF0DC 100%)',
    accent: '#C07855',
    image: '/images/재물/재물사주.webp',
  },
]

export default function Home() {
  const navigate = useNavigate()

  return (
    <div className="home-page">

      <header className="home-header">
        <div className="home-brand">사주 AI</div>
        <h1 className="home-title">오늘, 무엇이<br /><em>궁금하세요?</em></h1>
        <p className="home-sub">사주팔자로 나를 더 깊이 이해해보세요</p>
      </header>

      <div className="category-list">
        {CATEGORIES.map(cat => (
          <button
            key={cat.id}
            className="category-card"
            style={{ background: cat.gradient }}
            onClick={() => navigate('/analyze', { state: { category: cat } })}
          >
            <div className="category-img-wrap">
              <img
                src={cat.image}
                alt={cat.title}
                className="category-img"
                onError={e => { e.currentTarget.style.display = 'none' }}
              />
              <div className="category-img-fallback">{cat.icon}</div>
            </div>
            <div className="category-info">
              <div className="category-title" style={{ color: cat.accent }}>{cat.title}</div>
              <div className="category-sub">{cat.sub}</div>
            </div>
            <div className="category-arrow" style={{ color: cat.accent }}>›</div>
          </button>
        ))}
      </div>

      <p className="home-footer">생년월일시 기반 명리학 AI 분석</p>

    </div>
  )
}
