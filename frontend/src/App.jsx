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
  '木': { color: '#4ade80', bg: 'rgba(74,222,128,0.1)',  border: 'rgba(74,222,128,0.35)',  label: '목·木' },
  '火': { color: '#f87171', bg: 'rgba(248,113,113,0.1)', border: 'rgba(248,113,113,0.35)', label: '화·火' },
  '土': { color: '#fbbf24', bg: 'rgba(251,191,36,0.1)',  border: 'rgba(251,191,36,0.35)',  label: '토·土' },
  '金': { color: '#e2e8f0', bg: 'rgba(226,232,240,0.08)',border: 'rgba(226,232,240,0.25)', label: '금·金' },
  '水': { color: '#60a5fa', bg: 'rgba(96,165,250,0.1)',  border: 'rgba(96,165,250,0.35)',  label: '수·水' },
}
const SHI_OPTIONS = [
  { label: '子(자)時  23:30 ~ 01:29', hour: 0,  minute: 30 },
  { label: '丑(축)時  01:30 ~ 03:29', hour: 2,  minute: 30 },
  { label: '寅(인)時  03:30 ~ 05:29', hour: 4,  minute: 30 },
  { label: '卯(묘)時  05:30 ~ 07:29', hour: 6,  minute: 30 },
  { label: '辰(진)時  07:30 ~ 09:29', hour: 8,  minute: 30 },
  { label: '巳(사)時  09:30 ~ 11:29', hour: 10, minute: 30 },
  { label: '午(오)時  11:30 ~ 13:29', hour: 12, minute: 30 },
  { label: '未(미)時  13:30 ~ 15:29', hour: 14, minute: 30 },
  { label: '申(신)時  15:30 ~ 17:29', hour: 16, minute: 30 },
  { label: '酉(유)時  17:30 ~ 19:29', hour: 18, minute: 30 },
  { label: '戌(술)時  19:30 ~ 21:29', hour: 20, minute: 30 },
  { label: '亥(해)時  21:30 ~ 23:29', hour: 22, minute: 30 },
]
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

// 신살 유형 분류
const SINSAL_KIND = {
  // 관심도가 높은 살(하이라이트)
  '도화살': 'focus', '장성살': 'focus', '반안살': 'focus',
  // 일반
  '역마살': 'jung', '화개살': 'jung', '지살': 'jung',
  // 주의(저채도)
  '겁살': 'hyung', '재살': 'hyung', '천살': 'hyung',
  '월살': 'hyung', '망신살': 'hyung', '육해살': 'hyung',
  '양인살': 'hyung', '공망': 'hyung',
}

const SINSAL_PRIORITY = { focus: 0, gil: 1, jung: 2, hyung: 3 }

function ExtrasSection({ gwiin, gwiinDetails, sinsal, wealthMode }) {
  if (!gwiin?.length && !sinsal?.length) return null
  const pillarOrder = ['년', '월', '일', '시']
  const groupedSinsal = pillarOrder
    .map((pillar) => ({
      pillar,
      items: (sinsal ?? [])
        .filter((item) => item.pillar === pillar)
        .sort((a, b) => {
          const aKind = SINSAL_KIND[a.name] ?? 'jung'
          const bKind = SINSAL_KIND[b.name] ?? 'jung'
          const aPriority = SINSAL_PRIORITY[aKind] ?? 99
          const bPriority = SINSAL_PRIORITY[bKind] ?? 99
          if (aPriority !== bPriority) return aPriority - bPriority
          return a.name.localeCompare(b.name, 'ko')
        }),
    }))
    .filter((group) => group.items.length > 0)

  const body = (
    <div className="extras-section">
      {gwiin?.length > 0 && (
        <div className="extras-row">
          <span className="extras-label">귀인</span>
          <div className="extras-tags">
            {(gwiinDetails?.length ? gwiinDetails : gwiin.map((name) => ({ name })) ).map((item, i) => (
              <span key={`${item.name}-${item.basis ?? 'none'}-${i}`} className={`extras-tag extras-tag-gwiin${item.weakened ? ' extras-tag-weakened' : ''}`}>
                {item.name}
                {item.basis ? <span className="extras-pillar-label">({item.basis})</span> : null}
                {item.weakened ? <span className="extras-pillar-label">(약화:{item.weaken_reason})</span> : null}
              </span>
            ))}
          </div>
        </div>
      )}
      {sinsal?.length > 0 && (
        <div className="extras-row extras-row-sinsal">
          <span className="extras-label">신살</span>
          <div className="extras-sinsal-groups">
            {groupedSinsal.map((group) => (
              <div key={group.pillar} className="extras-sinsal-group">
                <span className="extras-sinsal-group-title">{group.pillar}주</span>
                <div className="extras-tags">
                  {group.items.map((item, i) => (
                    <span key={`${group.pillar}-${item.name}-${item.basis ?? 'none'}-${i}`} className={`extras-tag extras-tag-sinsal-${SINSAL_KIND[item.name] ?? 'jung'}`}>
                      {item.name}
                      <span className="extras-pillar-label">
                        ({item.basis ?? '기준없음'})
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  if (wealthMode) {
    return (
      <details className="extras-details extras-details-wealth">
        <summary className="extras-details-summary">귀인·신살 참고</summary>
        {body}
      </details>
    )
  }

  return body
}

function PillarCard({ label, pillar }) {
  return (
    <div className="pillar-outer">
      <div className="pillar-inner">
        <div className="pillar-card">
          <div className="pillar-title">{label}</div>
          <div className="pillar-badges">
            <ElementBadge char={pillar.heavenly_stem} elementMap={STEM_ELEMENT} />
            <ElementBadge char={pillar.earthly_branch} elementMap={BRANCH_ELEMENT} />
          </div>
          <div className="pillar-korean">{pillar.korean}</div>
        </div>
      </div>
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

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm(prev => {
      const updated = {
        ...prev,
        [name]: type === 'checkbox' ? checked
               : ['year', 'month', 'day', 'shiIndex'].includes(name) ? Number(value)
               : value,
      }
      // 양력으로 바꾸면 윤달 초기화
      if (name === 'calendar_type' && value === 'solar') {
        updated.is_leap_month = false
      }
      return updated
    })
  }
  const setGender = (g) => setForm(prev => ({ ...prev, gender: g }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null); setResult(null); setPillars(null); setStreamText('')
    try {
      const shi = SHI_OPTIONS[form.shiIndex]
      console.log('[Submit] 요청 시작 | URL:', API_URL, '| category:', category?.id ?? 'free', '| year:', form.year)
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          year: form.year, month: form.month, day: form.day,
          hour: shi.hour, minute: shi.minute,
          gender: form.gender, calendar_type: form.calendar_type,
          is_leap_month: form.is_leap_month,
          category: category?.id ?? 'wealth',
        }),
      })
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || '분석 실패') }

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
          명리학 기반 AI 분석
        </div>
        <h1 className="hero-title">
          {category ? <>{category.title}<br /><span>사주 분석</span></> : <>사주<span>팔자</span><br />명리 분석</>}
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
                  <input type="number" name="year" value={form.year} onChange={handleChange} min={1900} max={2100} />
                </div>
                <div className="field">
                  <label>월</label>
                  <input type="number" name="month" value={form.month} onChange={handleChange} min={1} max={12} />
                </div>
                <div className="field">
                  <label>일</label>
                  <input type="number" name="day" value={form.day} onChange={handleChange} min={1} max={31} />
                </div>
                <div className="field">
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

      {error && <div className="error-box">{error}</div>}

      {pillars && (
        <div className="result-section">

          <div className="result-label">
            {isLove ? '원국 (연애 해석의 기준)' : '원국 (재물 해석의 기준)'}
          </div>

          <div className="pillars">
            <PillarCard label="시주 時柱" pillar={pillars.hour_pillar} />
            <PillarCard label="일주 日柱" pillar={pillars.day_pillar} />
            <PillarCard label="월주 月柱" pillar={pillars.month_pillar} />
            <PillarCard label="년주 年柱" pillar={pillars.year_pillar} />
          </div>
          <ExtrasSection
            gwiin={pillars.gwiin}
            gwiinDetails={pillars.gwiin_details}
            sinsal={pillars.sinsal}
            wealthMode={!isLove}
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
