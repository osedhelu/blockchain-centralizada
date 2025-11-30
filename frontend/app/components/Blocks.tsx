'use client'

import { useState, useEffect } from 'react'

interface BlocksProps {
  apiBase: string
}

export default function Blocks({ apiBase }: BlocksProps) {
  const [blocks, setBlocks] = useState<any[]>([])
  const [expandedBlocks, setExpandedBlocks] = useState<Set<number>>(new Set())

  useEffect(() => {
    loadBlocks()
  }, [])

  const loadBlocks = async () => {
    try {
      const response = await fetch(`${apiBase}/chain`)
      const data = await response.json()
      setBlocks(data.chain || [])
    } catch (error) {
      console.error('Error cargando bloques:', error)
    }
  }

  const toggleBlock = (index: number) => {
    const newExpanded = new Set(expandedBlocks)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedBlocks(newExpanded)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copiado al portapapeles')
    })
  }

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

  return (
    <div className="card">
      <div className="card-title">Últimos Bloques</div>
      <button className="btn btn-secondary" onClick={loadBlocks}>Actualizar</button>
      <div style={{ marginTop: '20px' }}>
        <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '16px' }}>
          Total: {blocks.length} bloques
        </div>
        {blocks.slice().reverse().map((block) => (
          <div
            key={block.index}
            onClick={() => toggleBlock(block.index)}
            style={{
              background: expandedBlocks.has(block.index) ? 'rgba(255, 255, 255, 0.06)' : 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '12px',
              cursor: 'pointer',
              transition: 'all 0.3s'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ flex: 1 }}>
                <strong>Bloque #{block.index}</strong>
                <div style={{ fontFamily: 'monospace', fontSize: '12px', color: '#8a8fa3', wordBreak: 'break-all', marginTop: '4px' }}>
                  Hash: {block.hash}
                </div>
                <div style={{ fontSize: '12px', color: '#8a8fa3', marginTop: '8px' }}>
                  Transacciones: {block.transactions.length} | Nonce: {block.nonce} | {new Date(block.timestamp).toLocaleString()}
                </div>
              </div>
              <div>
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: '12px', padding: '6px 12px', marginRight: '10px' }}
                  onClick={(e) => { e.stopPropagation(); toggleBlock(block.index) }}
                >
                  {expandedBlocks.has(block.index) ? '▲' : '▼'} Ver Transacciones
                </button>
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: '12px', padding: '6px 12px' }}
                  onClick={(e) => { e.stopPropagation(); copyToClipboard(block.hash) }}
                >
                  Copiar Hash
                </button>
              </div>
            </div>
            {expandedBlocks.has(block.index) && (
              <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
                {block.transactions.map((tx: any, idx: number) => (
                  <div key={idx} style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '6px', padding: '12px', marginBottom: '8px' }}>
                    <div style={{ fontFamily: 'monospace', fontSize: '11px', color: '#8a8fa3', marginBottom: '8px' }}>
                      Hash: {tx.hash}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 0', fontSize: '13px' }}>
                      <span style={{ color: '#8a8fa3' }}>De:</span>
                      <span style={{ color: '#eaecef' }}>{tx.sender}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 0', fontSize: '13px' }}>
                      <span style={{ color: '#8a8fa3' }}>Para:</span>
                      <span style={{ color: '#eaecef' }}>{tx.recipient}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 0', fontSize: '13px' }}>
                      <span style={{ color: '#8a8fa3' }}>Monto:</span>
                      <span style={{ color: '#f0b90b', fontWeight: 'bold' }}>
                        {tx.amount_formatted || formatWei(tx.amount)}
                      </span>
                    </div>
                    <button
                      className="btn btn-secondary"
                      style={{ marginTop: '8px', fontSize: '11px', padding: '4px 8px' }}
                      onClick={(e) => { e.stopPropagation(); copyToClipboard(tx.hash) }}
                    >
                      Copiar Hash TX
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

