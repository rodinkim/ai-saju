import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { normalizeLlmMarkdown } from './normalizeLlmMarkdown.js'
import './History.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || `http://${window.location.hostname}:8000`

const CATEGORY_META = {
  wealth:     { label: '재물 사주',  icon: '🌿', accent: '#C07855', bg: '#FEF6EB' },
  love:       { label: '연애 사주',  icon: '🌸', accent: '#C47898', bg: '#FEF0F6' },
  fortune:    { label: '올해 운세',  icon: '🌒', accent: '#8A60B0', bg: '#F4EEF8' },
  pastlife:   { label: '전생 사주',  icon: '🌀', accent: '#6048A0', bg: '#F0EEF8' },
  vocation:   { label: '천직 사주',  icon: '✨', accent: '#A08030', bg: '#FEFAE8' },
  daewoon:    { label: '대운 사주',  icon: '🌊', accent: '#3868A8', bg: '#EEF4FC' },
  couple:     { label: '궁합',       icon: '🪡', accent: '#B06080', bg: '#FEF0F6' },
  family:     { label: '가족',       icon: '🏔️', accent: '#4878A8', bg: '#EEF4FC' },
  friendship: { label: '우정',       icon: '🌱', accent: '#3A7A50', bg: '#F0FAF2' },
}

function formatDate(iso) {
  const d = new Date(iso)
  const now = new Date()
  const diffDays = Math.floor((now - d) / 86400000)
  if (diffDays === 0) return '오늘'
  if (diffDays === 1) return '어제'
  if (diffDays < 7) return `${diffDays}일 전`
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
}

function groupByDate(items) {
  const groups = []
  let curLabel = null
  for (const item of items) {
    const d = new Date(item.created_at)
    const now = new Date()
    const diffDays = Math.floor((now - d) / 86400000)
    const label = diffDays === 0 ? '오늘'
      : diffDays === 1 ? '어제'
      : diffDays < 7 ? '이번 주'
      : diffDays < 30 ? '이번 달'
      : `${d.getFullYear()}년 ${d.getMonth() + 1}월`
    if (label !== curLabel) {
      groups.push({ label, items: [item] })
      curLabel = label
    } else {
      groups[groups.length - 1].items.push(item)
    }
  }
  return groups
}

const mdComponents = {
  strong: ({ node: _n, children }) => <strong className="md-strong">{children}</strong>,
  b:      ({ node: _n, children }) => <b      className="md-strong">{children}</b>,
}

export default function History() {
  const navigate = useNavigate()
  const token = localStorage.getItem('token')

  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    if (!token) {
      navigate('/', { state: { openLogin: true } })
      return
    }
    fetch(`${API_BASE}/api/saju/history`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => (r.ok ? r.json() : Promise.reject()))
      .then(setItems)
      .catch(() => navigate('/'))
      .finally(() => setLoading(false))
  }, [])

  const openDetail = async (item) => {
    setSelected({ item, detail: null })
    setDetailLoading(true)
    try {
      const r = await fetch(`${API_BASE}/api/saju/history/${item.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const detail = await r.json()
      setSelected({ item, detail })
    } catch { /* 요약만 표시 */ }
    finally { setDetailLoading(false) }
  }

  const groups = groupByDate(items)

  return (
    <div className="hist-page">

      <header className="hist-header">
        <button className="hist-back" onClick={() => navigate('/')} aria-label="뒤로">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.2"
            strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <span className="hist-title">분석 이력</span>
      </header>

      {loading ? (
        <div className="hist-loading">
          <div className="hist-spinner" />
          불러오는 중
        </div>
      ) : items.length === 0 ? (
        <div className="hist-empty">
          <div className="hist-empty-icon">🌿</div>
          <p className="hist-empty-title">아직 분석 이력이 없어요</p>
          <p className="hist-empty-sub">첫 번째 사주 분석을 시작해보세요.<br/>분석 결과가 여기에 저장됩니다.</p>
          <button className="hist-empty-btn" onClick={() => navigate('/')}>분석 시작하기</button>
        </div>
      ) : (
        <ul className="hist-list">
          {groups.map(group => (
            <li key={group.label}>
              <div className="hist-date-group">{group.label}</div>
              <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
                {group.items.map(item => {
                  const meta = CATEGORY_META[item.category] ?? { label: item.category, icon: '✨', accent: '#C07855', bg: '#FEF6EB' }
                  const isRelation = item.birth_info_b != null
                  const pillarsLine = isRelation
                    ? `${item.label_a || '나'} ${item.day_pillar} · ${item.label_b || '상대'} ${item.day_pillar_b}`
                    : `${item.day_pillar}일주 · ${item.birth_info.split(' ').slice(0, 3).join(' ')}`

                  return (
                    <li key={item.id}>
                      <button className="hist-item" onClick={() => openDetail(item)}>
                        <div className="hist-item-stripe" style={{ background: meta.accent }} />
                        <div className="hist-item-icon-wrap">
                          <div className="hist-item-icon" style={{ background: meta.bg }}>
                            {meta.icon}
                          </div>
                        </div>
                        <div className="hist-item-body">
                          <div className="hist-item-top">
                            <span className="hist-item-cat" style={{ color: meta.accent }}>{meta.label}</span>
                            <span className="hist-item-date">{formatDate(item.created_at)}</span>
                          </div>
                          <div className="hist-item-pillars">{pillarsLine}</div>
                          {item.summary && (
                            <div className="hist-item-summary">{item.summary}</div>
                          )}
                        </div>
                        <div className="hist-item-chevron">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" strokeWidth="2"
                            strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="9 18 15 12 9 6"/>
                          </svg>
                        </div>
                      </button>
                    </li>
                  )
                })}
              </ul>
            </li>
          ))}
        </ul>
      )}

      {selected && (() => {
        const meta = CATEGORY_META[selected.item.category] ?? { label: selected.item.category, icon: '✨', accent: '#C07855', bg: '#FEF6EB' }
        const isRelation = selected.item.birth_info_b != null
        const pillarsLine = isRelation
          ? `${selected.item.label_a || '나'} ${selected.item.day_pillar}일주 · ${selected.item.label_b || '상대'} ${selected.item.day_pillar_b}일주`
          : `${selected.item.day_pillar}일주 · ${selected.item.birth_info}`

        return (
          <>
            <div className="hist-backdrop" onClick={() => setSelected(null)} />
            <div className="hist-sheet">
              <div className="hist-sheet-handle" />

              <div className="hist-sheet-header">
                <div className="hist-sheet-icon" style={{ background: meta.bg }}>
                  {meta.icon}
                </div>
                <div className="hist-sheet-meta">
                  <div className="hist-sheet-cat" style={{ color: meta.accent }}>{meta.label}</div>
                  <div className="hist-sheet-pillars">{pillarsLine}</div>
                  <div className="hist-sheet-date">{formatDate(selected.item.created_at)}</div>
                </div>
              </div>

              <div className="hist-sheet-divider" />

              <div className="hist-sheet-body">
                {detailLoading ? (
                  <div className="hist-sheet-loading">
                    <div className="hist-spinner" />
                    불러오는 중
                  </div>
                ) : selected.detail?.result_text ? (
                  <div className="hist-result">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                      {normalizeLlmMarkdown(selected.detail.result_text)}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="hist-sheet-fallback">{selected.item.summary}</p>
                )}
              </div>
            </div>
          </>
        )
      })()}
    </div>
  )
}
