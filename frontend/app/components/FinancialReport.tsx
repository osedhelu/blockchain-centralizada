'use client'

import { useState, useEffect } from 'react'

interface FinancialReportProps {
  apiBase: string
}

export default function FinancialReport({ apiBase }: FinancialReportProps) {
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const loadReport = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${apiBase}/financial/report`)
      const data = await response.json()
      setReport(data)
    } catch (error: any) {
      console.error('Error cargando reporte:', error)
      setReport({ error: error.message })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReport()
  }, [])

  const formatWei = (wei: string | number) => {
    if (!wei) return '0'
    const weiStr = wei.toString()
    if (weiStr === '0') return '0'
    const weiBigInt = BigInt(weiStr)
    const divisor = BigInt('1000000000000000000')
    const wholePart = weiBigInt / divisor
    const fractionalPart = weiBigInt % divisor
    if (fractionalPart === BigInt(0)) return wholePart.toString()
    const fractionalStr = fractionalPart.toString().padStart(18, '0').replace(/0+$/, '')
    return fractionalStr ? `${wholePart}.${fractionalStr}` : wholePart.toString()
  }

  if (loading) {
    return (
      <div className="card">
        <div className="card-title">Reporte Financiero</div>
        <div style={{ textAlign: 'center', padding: '40px', color: '#8a8fa3' }}>
          Cargando reporte...
        </div>
      </div>
    )
  }

  if (report?.error) {
    return (
      <div className="card">
        <div className="card-title">Reporte Financiero</div>
        <div className="error">Error: {report.error}</div>
        <button className="btn btn-primary" onClick={loadReport} style={{ marginTop: '16px' }}>
          Reintentar
        </button>
      </div>
    )
  }

  if (!report) {
    return null
  }

  return (
    <div>
      {/* Resumen General */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
        <div className="card">
          <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '8px' }}>Bloques Totales</div>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#f0b90b' }}>
            {report.summary?.total_blocks || 0}
          </div>
        </div>
        <div className="card">
          <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '8px' }}>Total Transacciones</div>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#f0b90b' }}>
            {report.summary?.total_transactions || 0}
          </div>
        </div>
        <div className="card">
          <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '8px' }}>Volumen Total</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f0b90b' }}>
            {report.summary?.total_volume_formatted || formatWei(report.summary?.total_volume_wei || 0)}
          </div>
        </div>
        <div className="card">
          <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '8px' }}>Direcciones Únicas</div>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#f0b90b' }}>
            {report.summary?.unique_addresses || 0}
          </div>
        </div>
        <div className="card">
          <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '8px' }}>Recompensas Minadas</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#0ecb81' }}>
            {report.summary?.total_rewards_formatted || formatWei(report.summary?.total_rewards_wei || 0)}
          </div>
        </div>
        <div className="card">
          <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '8px' }}>Promedio TX/Bloque</div>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#f0b90b' }}>
            {report.summary?.average_transactions_per_block || 0}
          </div>
        </div>
      </div>

      {/* Top Direcciones */}
      <div className="card">
        <div className="card-title">Top 10 Direcciones por Balance</div>
        <button className="btn btn-secondary" onClick={loadReport} style={{ marginBottom: '16px' }}>
          Actualizar Reporte
        </button>
        {report.top_addresses?.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#8a8fa3' }}>
            No hay direcciones con balance
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <th style={{ padding: '12px', textAlign: 'left', color: '#8a8fa3', fontSize: '14px' }}>#</th>
                  <th style={{ padding: '12px', textAlign: 'left', color: '#8a8fa3', fontSize: '14px' }}>Dirección</th>
                  <th style={{ padding: '12px', textAlign: 'right', color: '#8a8fa3', fontSize: '14px' }}>Balance</th>
                </tr>
              </thead>
              <tbody>
                {report.top_addresses?.map((addr: any, idx: number) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                    <td style={{ padding: '12px', color: '#eaecef' }}>{idx + 1}</td>
                    <td style={{ padding: '12px' }}>
                      <div className="wallet-address" style={{ fontSize: '12px' }}>{addr.address}</div>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', color: '#f0b90b', fontWeight: 'bold' }}>
                      {addr.balance_formatted || formatWei(addr.balance || 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Estadísticas Diarias */}
      <div className="card">
        <div className="card-title">Estadísticas de los Últimos 7 Días</div>
        {report.daily_statistics?.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#8a8fa3' }}>
            No hay datos disponibles
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <th style={{ padding: '12px', textAlign: 'left', color: '#8a8fa3', fontSize: '14px' }}>Fecha</th>
                  <th style={{ padding: '12px', textAlign: 'right', color: '#8a8fa3', fontSize: '14px' }}>Transacciones</th>
                  <th style={{ padding: '12px', textAlign: 'right', color: '#8a8fa3', fontSize: '14px' }}>Volumen</th>
                </tr>
              </thead>
              <tbody>
                {report.daily_statistics?.map((day: any, idx: number) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                    <td style={{ padding: '12px', color: '#eaecef' }}>
                      {new Date(day.date).toLocaleDateString('es-ES', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', color: '#eaecef' }}>
                      {day.transactions}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', color: '#f0b90b', fontWeight: 'bold' }}>
                      {day.volume_formatted || formatWei(day.volume || 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Últimas Transacciones */}
      <div className="card">
        <div className="card-title">Últimas Transacciones</div>
        {report.recent_transactions?.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#8a8fa3' }}>
            No hay transacciones recientes
          </div>
        ) : (
          <div>
            {report.recent_transactions?.map((tx: any, idx: number) => (
              <div key={idx} style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '8px', padding: '16px', marginBottom: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '12px', color: '#8a8fa3', marginBottom: '4px' }}>
                      Bloque #{tx.block_index} | {new Date(tx.timestamp).toLocaleString()}
                    </div>
                    <div style={{ fontFamily: 'monospace', fontSize: '11px', color: '#8a8fa3', wordBreak: 'break-all' }}>
                      Hash: {tx.hash}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#f0b90b' }}>
                      {tx.amount_formatted || formatWei(tx.amount || 0)}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginTop: '8px' }}>
                  <div>
                    <span style={{ color: '#8a8fa3' }}>De: </span>
                    <span style={{ color: '#eaecef', wordBreak: 'break-all' }}>{tx.sender}</span>
                  </div>
                  <div style={{ marginLeft: '16px' }}>
                    <span style={{ color: '#8a8fa3' }}>Para: </span>
                    <span style={{ color: '#eaecef', wordBreak: 'break-all' }}>{tx.recipient}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Información del Reporte */}
      <div className="card">
        <div style={{ fontSize: '12px', color: '#8a8fa3', textAlign: 'center' }}>
          Reporte generado el {new Date(report.generated_at).toLocaleString()}
        </div>
      </div>
    </div>
  )
}

