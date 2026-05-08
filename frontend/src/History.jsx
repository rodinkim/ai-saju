import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { normalizeLlmMarkdown } from './normalizeLlmMarkdown.js'
import './History.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || `http://${window.location.hostname}:8000`

const CATEGORY_META = {
  wealth:     { label: '재물 사주',  icon: '🌿', accent: '#C07855' },
  love:       { label: '연애 사주',  icon: '🌸', accent: '#C47898' },
  fortune:    { label: '올해 운세',  icon: '🌒', accent: '#8A60B0' },
  pastlife:   { label: '전생 사주',  icon: '🌀', accent: '#6048A0' },
  vocation:   { label: '천직 사주',  icon: '✨', accent: '#A08030' },
  daewoon:    { label: '대운 사주',  icon: '🌊', accent: '#3868A8' },
  couple:     { label: '궁합',       icon: '🪡', accent: '#B06080' },
  family:     { label: '가족',       icon: '🏔️', accent: '#4878A8' },
  friendship: { label: '우정',       icon: '🌱', accent: '#3A7A50' },
}

function formatDate(iso) {
  const d = new Date(iso)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
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
  const [selected, setSelected] = useState(null)   // { item, detail | null }
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
    } catch {
      // 요약만 표시
    } finally {
      setDetailLoading(false)
    }
  }

  const closeDetail = () => setSelected(null)

  return (
    <div className="hist-page">

      <header className="hist-header">
        <button className="hist-back" onClick={() => navigate('/')}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <span className="hist-title">분석 이력</span>
      </header>

      {loading ? (
        <div className="hist-loading">불러오는 중...</div>
      ) : items.length === 0 ? (
        <div className="hist-empty">
          <p className="hist-empty-msg">아직 분석 이력이 없어요</p>
          <button className="hist-empty-btn" onClick={() => navigate('/')}>첫 분석 하러 가기</button>
        </div>
      ) : (
        <ul className="hist-list">
          {items.map(item => {
            const meta = CATEGORY_META[item.category] ?? { label: item.category, icon: '✨', accent: '#888' }
            const isRelation = item.birth_info_b != null
            const pillarsLine = isRelation
              ? `${item.label_a || '나'} ${item.day_pillar}일주 · ${item.label_b || '상대'} ${item.day_pillar_b}일주`
              : `${item.day_pillar}일주 · ${item.birth_info.split(' ').slice(0, 3).join(' ')}`

            return (
              <li key={item.id}>
                <button className="hist-item" onClick={() => openDetail(item)}>
                  <div className="hist-item-icon" style={{ background: `${meta.accent}1A` }}>
                    {meta.icon}
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
                  <span className="hist-item-arrow">›</span>
                </button>
              </li>
            )
          })}
        </ul>
      )}

      {selected && (
        <>
          <div className="hist-backdrop" onClick={closeDetail} />
          <div className="hist-sheet">
            <div className="hist-sheet-handle" />

            <div className="hist-sheet-top">
              <div className="hist-sheet-cat" style={{ color: CATEGORY_META[selected.item.category]?.accent ?? '#888' }}>
                {CATEGORY_META[selected.item.category]?.icon} {CATEGORY_META[selected.item.category]?.label ?? selected.item.category}
              </div>
              <div className="hist-sheet-date">{formatDate(selected.item.created_at)}</div>
            </div>

            <div className="hist-sheet-pillars">
              {selected.item.birth_info_b
                ? `${selected.item.label_a || '나'} ${selected.item.day_pillar}일주 · ${selected.item.label_b || '상대'} ${selected.item.day_pillar_b}일주`
                : `${selected.item.day_pillar}일주 · ${selected.item.birth_info}`
              }
            </div>

            <div className="hist-sheet-body">
              {detailLoading ? (
                <div className="hist-sheet-loading">불러오는 중...</div>
              ) : selected.detail?.result_text ? (
                <div className="hist-sheet-result">
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
      )}
    </div>
  )
}
