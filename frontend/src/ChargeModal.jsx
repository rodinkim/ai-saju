import { useState } from 'react'
import './ChargeModal.css'

const API_HOST = window.location.hostname || 'localhost'
const API_BASE = `http://${API_HOST}:8000`
const TOSS_CLIENT_KEY = 'test_ck_KNbdOvk5rkwvA5bmk4ZErn07xlzm'

const PACKAGES = [
  { credits: 100, count: 10, amount: 4900,  label: '기본' },
  { credits: 300, count: 30, amount: 12900, label: '인기', popular: true },
  { credits: 500, count: 50, amount: 19900, label: '프리미엄' },
]

function loadTossScript() {
  return new Promise((resolve, reject) => {
    if (window.TossPayments) { resolve(); return }
    const script = document.createElement('script')
    script.src = 'https://js.tosspayments.com/v1/payment'
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })
}

export default function ChargeModal({ user, onClose }) {
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleCharge = async () => {
    if (!selected || loading) return
    setLoading(true)
    try {
      await loadTossScript()
      const tossPayments = window.TossPayments(TOSS_CLIENT_KEY)
      const orderId = `saju-${user.id}-${Date.now()}`
      await tossPayments.requestPayment('카드', {
        amount: selected.amount,
        orderId,
        orderName: `사주 분석 ${selected.credits} 크레딧`,
        customerName: user.name || '사용자',
        successUrl: `${window.location.origin}/payment/result`,
        failUrl: `${window.location.origin}/payment/result`,
      })
    } catch (e) {
      // 사용자가 결제창 닫은 경우 포함
      setLoading(false)
    }
  }

  return (
    <>
      <div className="charge-backdrop" onClick={onClose} />
      <div className="charge-sheet">
        <div className="charge-handle" />
        <p className="charge-title">크레딧 충전</p>
        <p className="charge-sub">1회 분석에 10 크레딧이 사용돼요</p>

        <div className="charge-packages">
          {PACKAGES.map(pkg => (
            <button
              key={pkg.credits}
              className={`charge-pkg${selected?.credits === pkg.credits ? ' selected' : ''}${pkg.popular ? ' popular' : ''}`}
              onClick={() => setSelected(pkg)}
            >
              {pkg.popular && <span className="pkg-badge">인기</span>}
              <div className="pkg-left">
                <span className="pkg-credits">{pkg.credits} 크레딧</span>
                <span className="pkg-count">분석 {pkg.count}회</span>
              </div>
              <span className="pkg-price">{pkg.amount.toLocaleString()}원</span>
            </button>
          ))}
        </div>

        <button
          className="charge-pay-btn"
          disabled={!selected || loading}
          onClick={handleCharge}
        >
          {loading
            ? '처리 중...'
            : selected
              ? `${selected.amount.toLocaleString()}원 결제하기`
              : '패키지를 선택해주세요'}
        </button>
      </div>
    </>
  )
}
