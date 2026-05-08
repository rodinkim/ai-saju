import { useEffect, useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import './Home.css'
import ChargeModal from './ChargeModal.jsx'

const API_BASE = import.meta.env.VITE_API_BASE_URL || `http://${window.location.hostname}:8000`

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

const UserIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)

export default function Home() {
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState(null)
  const [showLogin, setShowLogin] = useState(false)
  const [showCharge, setShowCharge] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)

  useEffect(() => {
    if (location.state?.openLogin) setShowLogin(true)
  }, [location.state])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    if (token) {
      localStorage.setItem('token', token)
      window.history.replaceState({}, '', '/')
    }
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
    setShowUserMenu(false)
  }

  return (
    <>
    <div className="home-page">

      {/* ── 네비게이션 바 ── */}
      <nav className="home-nav">
        <div className="home-nav-side" />
        <span className="home-nav-brand">토정</span>
        <div className="home-nav-side home-nav-right">
          {user && (
            <button className="nav-credits-btn" onClick={() => setShowCharge(true)}>
              🪙 {user.credits}
            </button>
          )}
          <button
            className={`nav-user-btn${user ? ' nav-user-btn--active' : ''}`}
            onClick={() => user ? setShowUserMenu(true) : setShowLogin(true)}
            aria-label={user ? '프로필 메뉴' : '로그인'}
          >
            {user?.profile_image
              ? <img className="nav-avatar" src={user.profile_image} alt={user.name} referrerPolicy="no-referrer" />
              : <UserIcon />
            }
          </button>
        </div>
      </nav>

      {/* ── 히어로 ── */}
      <header className="home-hero">
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

      <div className="category-section-label">크레딧 요금</div>
      <div className="pricing-list">
        {[
          { credits: 100, count: 10, amount: 3900,  label: '기본' },
          { credits: 300, count: 30, amount: 9900,  label: '인기', popular: true },
          { credits: 500, count: 50, amount: 16900, label: '프리미엄' },
        ].map(pkg => (
          <div key={pkg.credits} className={`pricing-card${pkg.popular ? ' pricing-popular' : ''}`}>
            {pkg.popular && <span className="pricing-badge">인기</span>}
            <div className="pricing-info">
              <span className="pricing-label">{pkg.label}</span>
              <span className="pricing-credits">{pkg.credits} 크레딧 · 분석 {pkg.count}회</span>
            </div>
            <span className="pricing-price">{pkg.amount.toLocaleString()}원</span>
          </div>
        ))}
        <p className="pricing-note">1회 분석에 10 크레딧이 사용됩니다 · 부가세 포함</p>
      </div>

      <footer className="home-footer">
        <p className="home-footer-brand">토정</p>
        <p>상호명: 토정 · 대표자: 김오성</p>
        <p>사업자등록번호: 810-67-00813</p>
        <p>주소: 서울특별시 서초구 반포동 740-3</p>
        <p>고객센터: 010-2315-1992 · rladhtjdzoq@naver.com</p>
        <div className="home-footer-links">
          <Link to="/terms">이용약관</Link>
          <span>·</span>
          <Link to="/privacy">개인정보처리방침</Link>
        </div>
        <p className="home-footer-copy">© 2026 토정. All rights reserved.</p>
      </footer>

    </div>

    {showCharge && (
      <ChargeModal user={user} onClose={() => setShowCharge(false)} />
    )}

    {/* ── 유저 메뉴 바텀시트 ── */}
    {showUserMenu && user && (
      <>
        <div className="login-backdrop" onClick={() => setShowUserMenu(false)} />
        <div className="user-menu-sheet">
          <div className="login-sheet-handle" />
          <div className="user-menu-profile">
            {user.profile_image
              ? <img className="user-menu-avatar" src={user.profile_image} alt={user.name} referrerPolicy="no-referrer" />
              : <div className="user-menu-avatar-placeholder"><UserIcon /></div>
            }
            <div className="user-menu-info">
              <p className="user-menu-name">{user.name}</p>
              <p className="user-menu-credits">🪙 크레딧 {user.credits}개 보유</p>
            </div>
          </div>
          <div className="user-menu-divider" />
          <div className="user-menu-actions">
            <button className="user-menu-item" onClick={() => { setShowUserMenu(false); navigate('/history') }}>
              <span className="user-menu-item-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
              </span>
              분석 이력
              <svg className="user-menu-item-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
            <button className="user-menu-item" onClick={() => { setShowUserMenu(false); setShowCharge(true) }}>
              <span className="user-menu-item-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="16"/>
                  <line x1="8" y1="12" x2="16" y2="12"/>
                </svg>
              </span>
              크레딧 충전
              <svg className="user-menu-item-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </div>
          <div className="user-menu-divider" />
          <button className="user-menu-logout" onClick={handleLogout}>로그아웃</button>
        </div>
      </>
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
