import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './PaymentResult.css'

const API_HOST = window.location.hostname || 'localhost'
const API_BASE = `http://${API_HOST}:8000`

export default function PaymentResult() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('loading')
  const [addedCredits, setAddedCredits] = useState(0)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const paymentKey = params.get('paymentKey')
    const orderId    = params.get('orderId')
    const amount     = params.get('amount')

    if (!paymentKey || !orderId || !amount) {
      setErrorMsg(params.get('message') || '결제가 취소되었습니다')
      setStatus('fail')
      return
    }

    const token = localStorage.getItem('token')
    fetch(`${API_BASE}/payment/confirm`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ paymentKey, orderId, amount: Number(amount) }),
    })
      .then(r => r.ok ? r.json() : r.json().then(d => Promise.reject(d.detail)))
      .then(data => { setAddedCredits(data.added); setStatus('success') })
      .catch(msg => {
        setErrorMsg(typeof msg === 'string' ? msg : '결제 처리 중 오류가 발생했습니다')
        setStatus('fail')
      })
  }, [])

  return (
    <div className="payment-result-page">
      {status === 'loading' && (
        <div className="result-loading">
          <div className="result-spinner" />
          <p>결제 처리 중...</p>
        </div>
      )}

      {status === 'success' && (
        <div className="result-card success">
          <div className="result-icon">✦</div>
          <h2>충전 완료!</h2>
          <p><strong>{addedCredits} 크레딧</strong>이 지급되었어요</p>
          <p className="result-sub">토정으로 운명을 탐구해보세요</p>
          <button className="result-btn" onClick={() => navigate('/')}>홈으로 가기</button>
        </div>
      )}

      {status === 'fail' && (
        <div className="result-card fail">
          <div className="result-icon">✕</div>
          <h2>결제 실패</h2>
          <p>{errorMsg}</p>
          <button className="result-btn" onClick={() => navigate('/')}>홈으로 가기</button>
        </div>
      )}
    </div>
  )
}
