import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { normalizeLlmMarkdown } from './normalizeLlmMarkdown.js'
import './App.css'

const API_HOST = window.location.hostname || 'localhost'
const API_URL = `http://${API_HOST}:8000/api/saju/analyze/stream`

/** `node` / `rest`는 DOM에 넘기지 않음(Safari·React 경고로 스타일 무시 유발 가능). */
const analysisMarkdownComponents = {
  strong: ({ node: _node, className, children }) => (
    <strong className={['md-strong', className].filter(Boolean).join(' ')}>
      {children}
    </strong>
  ),
  b: ({ node: _node, className, children }) => (
    <b className={['md-strong', className].filter(Boolean).join(' ')}>
      {children}
    </b>
  ),
}

const STEM_ELEMENT = {
  '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
  '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
}
const BRANCH_ELEMENT = {
  '子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火',
  '午': '火', '申': '金', '酉': '金', '辰': '土', '戌': '土', '丑': '土', '未': '土',
}
const ELEMENT_META = {
  '木': { color: '#3A8A50', bg: '#F0FAF2', border: '#C4E8CE', label: '목·木' },
  '火': { color: '#C04848', bg: '#FEF0EF', border: '#F4C4C0', label: '화·火' },
  '土': { color: '#B06828', bg: '#FEF6EB', border: '#EDD8B0', label: '토·土' },
  '金': { color: '#5A6878', bg: '#F0F2F4', border: '#C8D0D8', label: '금·金' },
  '水': { color: '#3878B0', bg: '#EEF4FC', border: '#B4D0EE', label: '수·水' },
}
const SHI_OPTIONS = [
  { label: '자시 · 23:30 ~ 01:29', hour: 0,  minute: 30 },
  { label: '축시 · 01:30 ~ 03:29', hour: 2,  minute: 30 },
  { label: '인시 · 03:30 ~ 05:29', hour: 4,  minute: 30 },
  { label: '묘시 · 05:30 ~ 07:29', hour: 6,  minute: 30 },
  { label: '진시 · 07:30 ~ 09:29', hour: 8,  minute: 30 },
  { label: '사시 · 09:30 ~ 11:29', hour: 10, minute: 30 },
  { label: '오시 · 11:30 ~ 13:29', hour: 12, minute: 30 },
  { label: '미시 · 13:30 ~ 15:29', hour: 14, minute: 30 },
  { label: '신시 · 15:30 ~ 17:29', hour: 16, minute: 30 },
  { label: '유시 · 17:30 ~ 19:29', hour: 18, minute: 30 },
  { label: '술시 · 19:30 ~ 21:29', hour: 20, minute: 30 },
  { label: '해시 · 21:30 ~ 23:29', hour: 22, minute: 30 },
]
const YEAR_OPTIONS = Array.from({ length: 2010 - 1940 + 1 }, (_, i) => 2010 - i)
const MONTH_OPTIONS = Array.from({ length: 12 }, (_, i) => i + 1)
function getDaysInMonth(year, month) { return new Date(year, month, 0).getDate() }

const initialForm = { year: 1992, month: 8, day: 26, shiIndex: 9, gender: 'male', calendar_type: 'solar', is_leap_month: false }

function ElementBadge({ char, elementMap }) {
  const meta = ELEMENT_META[elementMap[char]] || {}
  return (
    <div className="element-badge" style={{ background: meta.bg, borderColor: meta.border }}>
      <span className="element-char" style={{ color: meta.color }}>{char}</span>
      <span className="element-label" style={{ color: meta.color }}>{meta.label}</span>
    </div>
  )
}

const SINSAL_META = {
  '도화살': { emoji: '🌸', desc: '이성에게 매력적', type: 'focus' },
  '장성살': { emoji: '🛡️', desc: '강한 추진력',     type: 'focus' },
  '반안살': { emoji: '🔮', desc: '뛰어난 통찰력',   type: 'focus' },
  '역마살': { emoji: '🌿', desc: '활발한 변동·이동', type: 'jung'  },
  '화개살': { emoji: '🎨', desc: '예술적 감수성',   type: 'jung'  },
  '지살':   { emoji: '🌱', desc: '새로운 시작',     type: 'jung'  },
  '겁살':   { emoji: '⚡', desc: '강한 에너지',     type: 'hyung' },
  '양인살': { emoji: '🗡️', desc: '날카로운 기운',   type: 'hyung' },
  '망신살': { emoji: '🌀', desc: '주의가 필요',     type: 'hyung' },
}

function ExtrasSection({ gwiin, gwiinDetails, sinsal }) {
  const gwiinItems = (gwiinDetails?.length
    ? gwiinDetails
    : (gwiin ?? []).map(name => ({ name }))
  )

  const sinsalCards = (sinsal ?? [])
    .filter(s => SINSAL_META[s.name])
    .map(s => ({ ...SINSAL_META[s.name], name: s.name, pillar: s.pillar }))

  if (!gwiinItems.length && !sinsalCards.length) return null

  return (
    <div className="highlight-grid">
      {gwiinItems.map((item, i) => (
        <div key={i} className={`highlight-card highlight-gwiin${item.weakened ? ' highlight-weakened' : ''}`}>
          <span className="highlight-emoji">⭐</span>
          <div className="highlight-info">
            <span className="highlight-name">{item.name}</span>
            <span className="highlight-desc">{item.basis ? `${item.basis} 기준` : '귀인의 도움'}</span>
          </div>
        </div>
      ))}
      {sinsalCards.map((card, i) => (
        <div key={i} className={`highlight-card highlight-${card.type}`}>
          <span className="highlight-emoji">{card.emoji}</span>
          <div className="highlight-info">
            <span className="highlight-name">{card.name}</span>
            <span className="highlight-desc">{card.desc}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

function PillarCard({ label, pillar }) {
  const stemMeta   = ELEMENT_META[STEM_ELEMENT[pillar.heavenly_stem]]   || {}
  const branchMeta = ELEMENT_META[BRANCH_ELEMENT[pillar.earthly_branch]] || {}
  return (
    <div className="pillar-card">
      <div className="pillar-label">{label}</div>
      <div className="pillar-cell" style={{ color: stemMeta.color, background: stemMeta.bg, borderColor: stemMeta.border }}>
        <span className="pillar-char">{pillar.heavenly_stem}</span>
        <span className="pillar-elem">{stemMeta.label}</span>
      </div>
      <div className="pillar-cell" style={{ color: branchMeta.color, background: branchMeta.bg, borderColor: branchMeta.border }}>
        <span className="pillar-char">{pillar.earthly_branch}</span>
        <span className="pillar-elem">{branchMeta.label}</span>
      </div>
      <div className="pillar-korean">{pillar.korean}</div>
    </div>
  )
}

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()
  const category = location.state?.category
  const isLove = category?.id === 'love'

  console.log('[App] 페이지 로드 v2 | category:', category?.id ?? 'none', '| API:', API_URL)

  const [form, setForm] = useState(initialForm)
  const [pillars, setPillars] = useState(null)
  const [streamText, setStreamText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [needsLogin, setNeedsLogin] = useState(false)

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm(prev => {
      const updated = {
        ...prev,
        [name]: type === 'checkbox' ? checked
               : ['year', 'month', 'day', 'shiIndex'].includes(name) ? Number(value)
               : value,
      }
      if (name === 'calendar_type' && value === 'solar') {
        updated.is_leap_month = false
      }
      // 연/월 변경 시 선택한 일이 해당 월 최대치를 초과하면 보정
      if (name === 'year' || name === 'month') {
        const maxDay = getDaysInMonth(
          name === 'year' ? Number(value) : prev.year,
          name === 'month' ? Number(value) : prev.month,
        )
        if (updated.day > maxDay) updated.day = maxDay
      }
      return updated
    })
  }
  const setGender = (g) => setForm(prev => ({ ...prev, gender: g }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null); setNeedsLogin(false); setResult(null); setPillars(null); setStreamText('')
    try {
      const shi = SHI_OPTIONS[form.shiIndex]
      console.log('[Submit] 요청 시작 | URL:', API_URL, '| category:', category?.id ?? 'free', '| year:', form.year)
      const token = localStorage.getItem('token')
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          year: form.year, month: form.month, day: form.day,
          hour: shi.hour, minute: shi.minute,
          gender: form.gender, calendar_type: form.calendar_type,
          is_leap_month: form.is_leap_month,
          category: category?.id ?? 'wealth',
        }),
      })
      if (!res.ok) {
        const d = await res.json()
        if (res.status === 401) { setNeedsLogin(true); setLoading(false); return }
        if (res.status === 402) throw new Error('크레딧이 부족합니다. 충전 후 이용해주세요.')
        throw new Error(d.detail || '분석 실패')
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      let fullText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buf += decoder.decode(value, { stream: true })
        const parts = buf.split('\n\n')
        buf = parts.pop() // 마지막 미완성 청크 보존

        for (const part of parts) {
          const eventMatch = part.match(/^event: (\w+)/)
          const dataMatch = part.match(/^data: ([\s\S]*)$/m)
          if (!eventMatch || !dataMatch) continue

          const event = eventMatch[1]
          const raw = dataMatch[1].trim()

          let data
          try {
            data = JSON.parse(raw)
          } catch {
            // 백엔드가 JSON 인코딩 안 한 경우 raw 문자열 그대로 사용
            data = raw
            console.warn('[SSE] JSON 파싱 실패, raw 사용:', event, raw.slice(0, 50))
          }

          if (event === 'pillars') {
            setPillars(typeof data === 'object' ? data : JSON.parse(raw))
            setLoading(false)
          } else if (event === 'delta') {
            fullText += typeof data === 'string' ? data : raw
            const display = fullText.replace(/\*\*([^*\n]+)\*\*([가-힣])/g, '**$1** $2')
            setStreamText(display)
          } else if (event === 'done') {
            const summary = typeof data === 'object' ? data.summary : ''
            setResult({ summary })
          } else if (event === 'error') {
            const msg = typeof data === 'string' ? data : JSON.stringify(data)
            console.error('[SSE] error event:', msg)
            throw new Error(msg)
          }
        }
      }
    } catch (err) { setError(err.message); setLoading(false) }
  }

  return (
    <div className="page">

      {/* 뒤로가기 */}
      <button className="back-btn" onClick={() => navigate(-1)}>
        <iconify-icon icon="solar:arrow-left-bold" />
        <span>다른 사주 보기</span>
      </button>

      {/* 히어로 */}
      <div className="hero">
        <div className="hero-deco">
          <iconify-icon icon="solar:stars-bold-duotone" style={{ color: 'var(--gold-dim)' }} />
          정밀 명리 분석
        </div>
        <h1 className="hero-title">
          {category ? <>{category.title}<br /><span>명리 분석</span></> : <>사주<span>팔자</span><br />명리 분석</>}
        </h1>
        <p className="hero-sub">
          {category?.sub ?? '생년월일시를 입력하면 오행 분포와 용신을 분석하고 깊이 있는 운명 해석을 제공합니다'}
        </p>
      </div>

      {/* 입력 폼 */}
      <div className="form-outer">
        <div className="form-inner">
          <form className="form-body" onSubmit={handleSubmit}>

            <div>
              <div className="form-section-label">
                <iconify-icon icon="solar:calendar-bold-duotone" />  생년월일
              </div>
              <div className="date-grid">
                <div className="field field-year">
                  <label>연도</label>
                  <select name="year" value={form.year} onChange={handleChange}>
                    {YEAR_OPTIONS.map(y => (
                      <option key={y} value={y}>{y}년</option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>월</label>
                  <select name="month" value={form.month} onChange={handleChange}>
                    {MONTH_OPTIONS.map(m => (
                      <option key={m} value={m}>{m}월</option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>일</label>
                  <select name="day" value={form.day} onChange={handleChange}>
                    {Array.from({ length: getDaysInMonth(form.year, form.month) }, (_, i) => i + 1).map(d => (
                      <option key={d} value={d}>{d}일</option>
                    ))}
                  </select>
                </div>
                <div className="field field-full">
                  <label>달력</label>
                  <select name="calendar_type" value={form.calendar_type} onChange={handleChange}>
                    <option value="solar">양력</option>
                    <option value="lunar">음력</option>
                  </select>
                </div>
              </div>
              {form.calendar_type === 'lunar' && (
                <label className="leap-month-label">
                  <input
                    type="checkbox"
                    name="is_leap_month"
                    checked={form.is_leap_month}
                    onChange={handleChange}
                  />
                  윤달
                </label>
              )}
            </div>

            <div>
              <div className="form-section-label">
                <iconify-icon icon="solar:clock-circle-bold-duotone" />  태어난 시
              </div>
              <p className="field-hint">출생 시간대를 선택해주세요 · 정확하지 않으면 가장 가까운 시간대로</p>
              <div className="field">
                <select name="shiIndex" value={form.shiIndex} onChange={handleChange}>
                  {SHI_OPTIONS.map((s, i) => (
                    <option key={i} value={i}>{s.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <div className="form-section-label">
                <iconify-icon icon="solar:user-bold-duotone" />  성별
              </div>
              <div className="gender-toggle">
                <button type="button" className={`gender-btn${form.gender === 'male' ? ' active' : ''}`} onClick={() => setGender('male')}>
                  <iconify-icon icon="solar:men-bold-duotone" />  남성
                </button>
                <button type="button" className={`gender-btn${form.gender === 'female' ? ' active' : ''}`} onClick={() => setGender('female')}>
                  <iconify-icon icon="solar:women-bold-duotone" />  여성
                </button>
              </div>
            </div>

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading
                ? <><div className="spinner" />분석 중...</>
                : <><iconify-icon icon="solar:magic-stick-3-bold-duotone" />사주 분석하기</>
              }
            </button>

          </form>
        </div>
      </div>

      {needsLogin && (
        <div className="login-required-card">
          <div className="login-required-icon">✦</div>
          <div className="login-required-text">
            <strong>소셜 로그인으로 3초면 돼요</strong>
            <span>카카오 · 네이버 · 구글 중 편한 걸로</span>
          </div>
          <button
            className="login-required-btn"
            onClick={() => navigate('/', { state: { openLogin: true } })}
          >
            로그인하기
          </button>
        </div>
      )}

      {error && <div className="error-box">{error}</div>}

      {pillars && (
        <div className="result-section">

          <div className="result-label">
            {isLove ? '원국 (연애 해석의 기준)' : '원국 (재물 해석의 기준)'}
          </div>

          <div className="pillars">
            <PillarCard label="시주" pillar={pillars.hour_pillar} />
            <PillarCard label="일주" pillar={pillars.day_pillar} />
            <PillarCard label="월주" pillar={pillars.month_pillar} />
            <PillarCard label="년주" pillar={pillars.year_pillar} />
          </div>
          <ExtrasSection
            gwiin={pillars.gwiin}
            gwiinDetails={pillars.gwiin_details}
            sinsal={pillars.sinsal}
          />

          {streamText && (
            <>
              <div className="result-label">
                {isLove ? '명리 분석 (연애 중심 · 종합)' : '명리 분석 (재물 중심 · 종합)'}
              </div>
              <div className="analysis-outer">
                <div className="analysis-inner">
                  <div className="analysis-body">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={analysisMarkdownComponents}
                    >
                      {normalizeLlmMarkdown(streamText)}
                    </ReactMarkdown>
                    {!result && <span className="stream-cursor" />}
                  </div>
                </div>
              </div>
            </>
          )}

        </div>
      )}

    </div>
  )
}
