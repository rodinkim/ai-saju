import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { normalizeLlmMarkdown } from './normalizeLlmMarkdown.js'
import './App.css'
import './Relation.css'

const API_HOST = window.location.hostname || 'localhost'
const API_URL = `http://${API_HOST}:8000/api/saju/relation/stream`

const analysisMarkdownComponents = {
  strong: ({ node: _node, className, children }) => (
    <strong className={['md-strong', className].filter(Boolean).join(' ')}>{children}</strong>
  ),
  b: ({ node: _node, className, children }) => (
    <b className={['md-strong', className].filter(Boolean).join(' ')}>{children}</b>
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

const initialPerson = (year = 1992) => ({
  year, month: 8, day: 26, shiIndex: 9,
  gender: 'female', calendar_type: 'solar', is_leap_month: false, label: '',
})

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

function PersonPillars({ label, pillars }) {
  return (
    <div className="person-pillars">
      <div className="person-pillars-label">{label || 'A'}</div>
      <div className="pillars">
        <PillarCard label="시주" pillar={pillars.hour_pillar} />
        <PillarCard label="일주" pillar={pillars.day_pillar} />
        <PillarCard label="월주" pillar={pillars.month_pillar} />
        <PillarCard label="년주" pillar={pillars.year_pillar} />
      </div>
    </div>
  )
}

function PersonForm({ title, form, onChange, setGender }) {
  return (
    <div className="person-form">
      <div className="person-form-title">{title}</div>

      <div className="field">
        <label>이름 / 별칭 <span className="field-optional">(선택)</span></label>
        <input
          type="text"
          name="label"
          value={form.label}
          onChange={onChange}
          placeholder="예: 나, 친구, 엄마"
          className="label-input"
          maxLength={10}
        />
      </div>

      <div className="form-section-label">
        <iconify-icon icon="solar:calendar-bold-duotone" /> 생년월일
      </div>
      <div className="date-grid">
        <div className="field field-year">
          <label>연도</label>
          <select name="year" value={form.year} onChange={onChange}>
            {YEAR_OPTIONS.map(y => <option key={y} value={y}>{y}년</option>)}
          </select>
        </div>
        <div className="field">
          <label>월</label>
          <select name="month" value={form.month} onChange={onChange}>
            {MONTH_OPTIONS.map(m => <option key={m} value={m}>{m}월</option>)}
          </select>
        </div>
        <div className="field">
          <label>일</label>
          <select name="day" value={form.day} onChange={onChange}>
            {Array.from({ length: getDaysInMonth(form.year, form.month) }, (_, i) => i + 1).map(d => (
              <option key={d} value={d}>{d}일</option>
            ))}
          </select>
        </div>
        <div className="field field-full">
          <label>달력</label>
          <select name="calendar_type" value={form.calendar_type} onChange={onChange}>
            <option value="solar">양력</option>
            <option value="lunar">음력</option>
          </select>
        </div>
      </div>
      {form.calendar_type === 'lunar' && (
        <label className="leap-month-label">
          <input type="checkbox" name="is_leap_month" checked={form.is_leap_month} onChange={onChange} />
          윤달
        </label>
      )}

      <div className="form-section-label">
        <iconify-icon icon="solar:clock-circle-bold-duotone" /> 태어난 시
      </div>
      <div className="field">
        <select name="shiIndex" value={form.shiIndex} onChange={onChange}>
          {SHI_OPTIONS.map((s, i) => <option key={i} value={i}>{s.label}</option>)}
        </select>
      </div>

      <div className="form-section-label">
        <iconify-icon icon="solar:user-bold-duotone" /> 성별
      </div>
      <div className="gender-toggle">
        <button type="button" className={`gender-btn${form.gender === 'male' ? ' active' : ''}`} onClick={() => setGender('male')}>
          <iconify-icon icon="solar:men-bold-duotone" /> 남성
        </button>
        <button type="button" className={`gender-btn${form.gender === 'female' ? ' active' : ''}`} onClick={() => setGender('female')}>
          <iconify-icon icon="solar:women-bold-duotone" /> 여성
        </button>
      </div>
    </div>
  )
}

export default function Relation() {
  const navigate = useNavigate()
  const location = useLocation()
  const category = location.state?.category

  const [formA, setFormA] = useState(initialPerson(1992))
  const [formB, setFormB] = useState(initialPerson(1990))
  const [pillarsA, setPillarsA] = useState(null)
  const [pillarsB, setPillarsB] = useState(null)
  const [streamText, setStreamText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [needsLogin, setNeedsLogin] = useState(false)

  const makeHandler = (setter) => (e) => {
    const { name, value, type, checked } = e.target
    setter(prev => {
      const updated = {
        ...prev,
        [name]: type === 'checkbox' ? checked
               : ['year', 'month', 'day', 'shiIndex'].includes(name) ? Number(value)
               : value,
      }
      if (name === 'calendar_type' && value === 'solar') updated.is_leap_month = false
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

  const buildPersonPayload = (form) => {
    const shi = SHI_OPTIONS[form.shiIndex]
    return {
      year: form.year, month: form.month, day: form.day,
      hour: shi.hour, minute: shi.minute,
      gender: form.gender, calendar_type: form.calendar_type,
      is_leap_month: form.is_leap_month,
      label: form.label,
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setNeedsLogin(false)
    setResult(null)
    setPillarsA(null)
    setPillarsB(null)
    setStreamText('')

    try {
      const token = localStorage.getItem('token')
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          person_a: buildPersonPayload(formA),
          person_b: buildPersonPayload(formB),
          category: category?.id ?? 'couple',
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
        buf = parts.pop()

        for (const part of parts) {
          const eventMatch = part.match(/^event: (\w+)/)
          const dataMatch = part.match(/^data: ([\s\S]*)$/m)
          if (!eventMatch || !dataMatch) continue

          const event = eventMatch[1]
          const raw = dataMatch[1].trim()
          let data
          try { data = JSON.parse(raw) } catch { data = raw }

          if (event === 'pillars_a') {
            setPillarsA(typeof data === 'object' ? data : JSON.parse(raw))
            setLoading(false)
          } else if (event === 'pillars_b') {
            setPillarsB(typeof data === 'object' ? data : JSON.parse(raw))
          } else if (event === 'delta') {
            fullText += typeof data === 'string' ? data : raw
            setStreamText(fullText.replace(/\*\*([^*\n]+)\*\*([가-힣])/g, '**$1** $2'))
          } else if (event === 'done') {
            setResult({ summary: typeof data === 'object' ? data.summary : '' })
          } else if (event === 'error') {
            throw new Error(typeof data === 'string' ? data : JSON.stringify(data))
          }
        }
      }
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const CATEGORY_HERO = {
    couple:     { deco: '두 사람 명리 분석', title: '궁합', titleSub: '사주 분석', sub: '두 사람의 사주가 만나는 방식을 분석합니다' },
    family:     { deco: '두 사람 명리 분석', title: '가족', titleSub: '사주 분석', sub: '가족 사이의 기운과 관계 패턴을 분석합니다' },
    friendship: { deco: '두 사람 명리 분석', title: '우정', titleSub: '사주 분석', sub: '친구 사이의 시너지와 어긋나는 지점을 분석합니다' },
  }
  const hero = CATEGORY_HERO[category?.id] ?? CATEGORY_HERO.couple

  return (
    <div className="page">

      <button className="back-btn" onClick={() => navigate(-1)}>
        <iconify-icon icon="solar:arrow-left-bold" />
        <span>다른 사주 보기</span>
      </button>

      <div className="hero">
        <div className="hero-deco">
          <iconify-icon icon="solar:stars-bold-duotone" style={{ color: 'var(--gold-dim)' }} />
          {hero.deco}
        </div>
        <h1 className="hero-title">
          {hero.title}<br /><span>{hero.titleSub}</span>
        </h1>
        <p className="hero-sub">{hero.sub}</p>
      </div>

      <div className="form-outer">
        <div className="form-inner">
          <form className="form-body" onSubmit={handleSubmit}>

            <PersonForm
              title="첫 번째 사람"
              form={formA}
              onChange={makeHandler(setFormA)}
              setGender={(g) => setFormA(prev => ({ ...prev, gender: g }))}
            />

            <div className="person-divider">
              <span>두 번째 사람</span>
            </div>

            <PersonForm
              title="두 번째 사람"
              form={formB}
              onChange={makeHandler(setFormB)}
              setGender={(g) => setFormB(prev => ({ ...prev, gender: g }))}
            />

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading
                ? <><div className="spinner" />분석 중...</>
                : <><iconify-icon icon="solar:magic-stick-3-bold-duotone" />분석하기</>
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
          <button className="login-required-btn" onClick={() => navigate('/', { state: { openLogin: true } })}>
            로그인하기
          </button>
        </div>
      )}

      {error && <div className="error-box">{error}</div>}

      {pillarsA && (
        <div className="result-section">
          <div className="result-label">원국</div>

          <PersonPillars label={formA.label || '첫 번째 사람'} pillars={pillarsA} />
          {pillarsB && <PersonPillars label={formB.label || '두 번째 사람'} pillars={pillarsB} />}

          {streamText && (
            <>
              <div className="result-label">명리 분석</div>
              <div className="analysis-outer">
                <div className="analysis-inner">
                  <div className="analysis-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={analysisMarkdownComponents}>
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
