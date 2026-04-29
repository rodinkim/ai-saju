import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import './Home.css'
import ChargeModal from './ChargeModal.jsx'

const API_HOST = window.location.hostname || 'localhost'
const API_BASE = `http://${API_HOST}:8000`

const CATEGORIES = [
  {
    id: 'fortune',
    title: '올해 운세',
    sub: '올해 나에게 어떤 기운이 오는지',
    icon: '🌒',
    gradient: 'linear-gradient(135deg, #F4EEF8 0%, #EAE0F5 100%)',
    accent: '#8A60B0',
  },
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
  {
    id: 'daewoon',
    title: '대운 사주',
    sub: '내 인생 전성기는 언제인가',
    icon: '🌊',
    gradient: 'linear-gradient(135deg, #EEF4FC 0%, #E0EDF8 100%)',
    accent: '#3868A8',
  },
  {
    id: 'pastlife',
    title: '전생 사주',
    sub: '전생에서 이번 생으로 가져온 것',
    icon: '🌀',
    gradient: 'linear-gradient(135deg, #F0EEF8 0%, #E4E0F5 100%)',
    accent: '#6048A0',
  },
  {
    id: 'vocation',
    title: '천직 사주',
    sub: '내가 타고난 진짜 직업의 방향',
    icon: '✨',
    gradient: 'linear-gradient(135deg, #FEFAE8 0%, #FAF3D0 100%)',
    accent: '#A08030',
  },
]

const RELATION_CATEGORIES = [
  {
    id: 'couple',
    title: '궁합',
    sub: '두 사람의 기운이 어떻게 만나는지',
    icon: '🪡',
    gradient: 'linear-gradient(135deg, #FEF0F6 0%, #FAE8F0 100%)',
    accent: '#B06080',
  },
  {
    id: 'family',
    title: '가족',
    sub: '가족 사이의 기운과 관계 패턴',
    icon: '🏔️',
    gradient: 'linear-gradient(135deg, #EEF4FC 0%, #E8F0F8 100%)',
    accent: '#4878A8',
  },
  {
    id: 'friendship',
    title: '우정',
    sub: '친구 사이의 시너지와 어긋나는 지점',
    icon: '🌱',
    gradient: 'linear-gradient(135deg, #F0FAF2 0%, #E8F5EA 100%)',
    accent: '#3A7A50',
  },
]

export default function Home() {
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState(null)
  const [showLogin, setShowLogin] = useState(false)
  const [showCharge, setShowCharge] = useState(false)

  useEffect(() => {
    if (location.state?.openLogin) setShowLogin(true)
  }, [location.state])

  useEffect(() => {
    // 소셜 콜백 후 URL에 ?token= 이 있으면 저장
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    if (token) {
      localStorage.setItem('token', token)
      window.history.replaceState({}, '', '/')
    }

    // 저장된 토큰으로 사용자 정보 조회
    const saved = localStorage.getItem('token')
    if (saved) {
      fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${saved}` },
      })
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(setUser)
        .catch(() => localStorage.removeItem('token'))
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  return (
    <>
    <div className="home-page">

      <header className="home-header">
        <div className="home-header-top">
          <div className="home-brand">토정</div>
          {user ? (
            <div className="user-info">
              {user.profile_image && (
                <img className="user-avatar" src={user.profile_image} alt={user.name} referrerPolicy="no-referrer" />
              )}
              <span className="user-name">{user.name}</span>
              <button className="user-credits" onClick={() => setShowCharge(true)}>🪙 {user.credits}</button>
              <button className="logout-btn" onClick={handleLogout}>로그아웃</button>
            </div>
          ) : (
            <button className="login-trigger-btn" onClick={() => setShowLogin(true)}>로그인</button>
          )}
        </div>
        <h1 className="home-title">오늘, 무엇이<br /><em>궁금하세요?</em></h1>
        <p className="home-sub">명리학으로 나를 더 깊이 이해해보세요</p>
      </header>

      {!user && (
        <button className="free-credit-banner" onClick={() => setShowLogin(true)}>
          <span className="free-credit-badge">무료</span>
          <div className="free-credit-text">
            <strong>지금 로그인하면 30 크레딧 즉시 지급</strong>
            <span>사주 분석 3회를 무료로 경험해보세요</span>
          </div>
          <span className="free-credit-arrow">›</span>
        </button>
      )}

      <div className="category-section-label">나의 사주</div>
      <div className="category-list">
        {CATEGORIES.map(cat => (
          <button
            key={cat.id}
            className="category-card"
            style={{ background: cat.gradient }}
            onClick={() => navigate('/analyze', { state: { category: cat } })}
          >
            <div className="category-img-wrap">
              {cat.image && (
                <img
                  src={cat.image}
                  alt={cat.title}
                  className="category-img"
                  onError={e => { e.currentTarget.style.display = 'none' }}
                />
              )}
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

      <div className="category-section-label">두 사람 사주</div>
      <div className="category-list">
        {RELATION_CATEGORIES.map(cat => (
          <button
            key={cat.id}
            className="category-card category-card-relation"
            style={{ background: cat.gradient }}
            onClick={() => navigate('/relation', { state: { category: cat } })}
          >
            <div className="category-img-wrap">
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

      <p className="home-footer">토정 · 생년월일시 기반 명리 분석</p>

    </div>

    {showCharge && (
      <ChargeModal user={user} onClose={() => setShowCharge(false)} />
    )}

    {showLogin && (

      <>
        <div className="login-backdrop" onClick={() => setShowLogin(false)} />
        <div className="login-sheet">
          <div className="login-sheet-handle" />
          <p className="login-sheet-title">소셜 로그인</p>
          <div className="login-sheet-buttons">
            <a className="social-btn naver" href={`${API_BASE}/auth/naver`}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M16.273 12.845L7.376 0H0v24h7.727V11.155L16.624 24H24V0h-7.727z"/>
              </svg>
              네이버로 계속하기
            </a>
            <a className="social-btn kakao" href={`${API_BASE}/auth/kakao`}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 3C6.477 3 2 6.477 2 10.5c0 2.548 1.565 4.788 3.938 6.12L4.9 20.1a.5.5 0 0 0 .724.54l4.431-2.962A11.6 11.6 0 0 0 12 18c5.523 0 10-3.477 10-7.5S17.523 3 12 3z"/>
              </svg>
              카카오로 계속하기
            </a>
            <a className="social-btn google" href={`${API_BASE}/auth/google`}>
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              구글로 계속하기
            </a>
          </div>
        </div>
      </>
    )}
    </>
  )
}
