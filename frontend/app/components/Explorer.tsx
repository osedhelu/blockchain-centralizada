'use client'

import { useState, useEffect } from 'react'

interface ExplorerProps {
  apiBase: string
}

export default function Explorer({ apiBase }: ExplorerProps) {
  const [chainInfo, setChainInfo] = useState<any>(null)
  const [searchAddress, setSearchAddress] = useState('')
  const [searchResult, setSearchResult] = useState<any>(null)
  const [txHash, setTxHash] = useState('')
  const [txResult, setTxResult] = useState<any>(null)
  const [pendingTransactions, setPendingTransactions] = useState<any[]>([])
  const [miningAddress, setMiningAddress] = useState('')
  const [miningResult, setMiningResult] = useState<any>(null)

  useEffect(() => {
    loadChainInfo()
    loadPendingTransactions()
  }, [])

  const loadChainInfo = async () => {
    try {
      const response = await fetch(`${apiBase}/chain/info`)
      const data = await response.json()
      setChainInfo(data)
    } catch (error) {
      console.error('Error cargando info:', error)
    }
  }

  const loadPendingTransactions = async () => {
    try {
      const response = await fetch(`${apiBase}/transactions/pending`)
      const data = await response.json()
      setPendingTransactions(data.pending_transactions || [])
    } catch (error) {
      console.error('Error cargando transacciones pendientes:', error)
    }
  }

  const mineBlock = async () => {
    if (!miningAddress.trim()) {
      alert('Por favor ingresa una dirección para recibir la recompensa de minería')
      return
    }
    try {
      setMiningResult({ loading: true })
      const response = await fetch(`${apiBase}/mine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mining_reward_address: miningAddress })
      })
      const data = await response.json()
      setMiningResult(data)
      if (data.success || data.task_id) {
        // Recargar transacciones pendientes después de un momento
        setTimeout(() => {
          loadPendingTransactions()
          loadChainInfo()
        }, 2000)
      }
    } catch (error: any) {
      setMiningResult({ error: error.message })
    }
  }

  const handleSearchAddress = async () => {
    if (!searchAddress.trim()) {
      alert('Por favor ingresa una dirección')
      return
    }

    try {
      const [balanceRes, txRes] = await Promise.all([
        fetch(`${apiBase}/wallet/${searchAddress}/balance`),
        fetch(`${apiBase}/wallet/${searchAddress}/transactions`)
      ])

      const balance = await balanceRes.json()
      const transactions = await txRes.json()

      setSearchResult({ balance, transactions })
    } catch (error: any) {
      setSearchResult({ error: error.message })
    }
  }

  const handleSearchTx = async () => {
    if (!txHash.trim()) {
      alert('Por favor ingresa el hash de la transacción')
      return
    }

    try {
      const response = await fetch(`${apiBase}/transaction/${txHash}`)
      if (!response.ok) {
        if (response.status === 404) {
          setTxResult({ error: 'Transacción no encontrada' })
          return
        }
        throw new Error(`Error HTTP: ${response.status}`)
      }
      const data = await response.json()
      setTxResult(data)
    } catch (error: any) {
      setTxResult({ error: error.message })
    }
  }

  const formatWei = (wei: string | number) => {
    if (!wei) return '0'
    const weiStr = wei.toString()
    if (weiStr === '0') return '0'
    
    const weiBigInt = BigInt(weiStr)
    const divisor = BigInt('1000000000000000000')
    
    const wholePart = weiBigInt / divisor
    const fractionalPart = weiBigInt % divisor
    
    if (fractionalPart === BigInt(0)) {
      return wholePart.toString()
    }
    
    const fractionalStr = fractionalPart.toString().padStart(18, '0').replace(/0+$/, '')
    return fractionalStr ? `${wholePart}.${fractionalStr}` : wholePart.toString()
  }

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '30px' }}>
        <div className="card">
          <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '8px' }}>Bloques Totales</div>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#f0b90b' }}>
            {chainInfo?.length || '-'}
          </div>
        </div>
        <div className="card">
          <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '8px' }}>Transacciones Pendientes</div>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#f0b90b' }}>
            {chainInfo?.pending_transactions || '-'}
          </div>
        </div>
        <div className="card">
          <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '8px' }}>Estado de la Cadena</div>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: chainInfo?.is_valid ? '#0ecb81' : '#f6465d' }}>
            {chainInfo?.is_valid ? '✓ Válida' : '✗ Inválida'}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Buscar Dirección</div>
        <input
          type="text"
          className="input-field"
          placeholder="0x..."
          value={searchAddress}
          onChange={(e) => setSearchAddress(e.target.value)}
        />
        <button className="btn btn-primary" onClick={handleSearchAddress}>Buscar</button>
        {searchResult && (
          <div style={{ marginTop: '20px' }}>
            {searchResult.error ? (
              <div className="error">Error: {searchResult.error}</div>
            ) : (
              <div>
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '14px', color: '#8a8fa3' }}>Dirección</div>
                  <div className="wallet-address">{searchResult.balance?.address}</div>
                  <div style={{ fontSize: '14px', color: '#8a8fa3', marginTop: '16px' }}>Balance</div>
                  <div className="balance-display">
                    {searchResult.balance?.balance_formatted || formatWei(searchResult.balance?.balance || 0)}
                  </div>
                  <div style={{ fontSize: '14px', color: '#8a8fa3', marginTop: '16px' }}>Total de Transacciones</div>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f0b90b' }}>
                    {searchResult.transactions?.count || 0}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-title">Buscar Transacción por Hash</div>
        <input
          type="text"
          className="input-field"
          placeholder="Hash de la transacción..."
          value={txHash}
          onChange={(e) => setTxHash(e.target.value)}
        />
        <button className="btn btn-primary" onClick={handleSearchTx}>Buscar Transacción</button>
        {txResult && (
          <div style={{ marginTop: '20px' }}>
            {txResult.error ? (
              <div className="error">{txResult.error}</div>
            ) : (
              <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '6px', padding: '12px' }}>
                <div style={{ fontFamily: 'monospace', fontSize: '11px', color: '#8a8fa3', marginBottom: '8px' }}>
                  <strong>Hash:</strong> {txResult.transaction?.hash}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 0', fontSize: '13px' }}>
                  <span style={{ color: '#8a8fa3' }}>Bloque:</span>
                  <span style={{ color: '#eaecef' }}>#{txResult.block_index}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 0', fontSize: '13px' }}>
                  <span style={{ color: '#8a8fa3' }}>De:</span>
                  <span style={{ color: '#eaecef' }}>{txResult.transaction?.sender}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 0', fontSize: '13px' }}>
                  <span style={{ color: '#8a8fa3' }}>Para:</span>
                  <span style={{ color: '#eaecef' }}>{txResult.transaction?.recipient}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 0', fontSize: '13px' }}>
                  <span style={{ color: '#8a8fa3' }}>Monto:</span>
                  <span style={{ color: '#f0b90b', fontWeight: 'bold', fontSize: '18px' }}>
                    {txResult.transaction?.amount_formatted || formatWei(txResult.transaction?.amount || 0)}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-title">Transacciones Pendientes</div>
        <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '16px' }}>
          Las transacciones pendientes están esperando ser incluidas en un bloque. Para confirmarlas, necesitas minar un bloque.
        </div>
        <button className="btn btn-secondary" onClick={loadPendingTransactions} style={{ marginBottom: '16px' }}>
          Actualizar Lista
        </button>
        {pendingTransactions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#8a8fa3' }}>
            No hay transacciones pendientes
          </div>
        ) : (
          <div>
            <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '16px' }}>
              Total: {pendingTransactions.length} transacción(es) pendiente(s)
            </div>
            {pendingTransactions.map((tx: any, idx: number) => (
              <div key={idx} style={{ background: 'rgba(240, 185, 11, 0.1)', border: '1px solid rgba(240, 185, 11, 0.3)', borderRadius: '8px', padding: '16px', marginBottom: '12px' }}>
                <div style={{ fontSize: '16px', fontWeight: '600', color: '#f0b90b', marginBottom: '8px' }}>
                  Transacción #{idx + 1}
                </div>
                <div style={{ fontFamily: 'monospace', fontSize: '11px', color: '#8a8fa3', marginBottom: '8px', wordBreak: 'break-all' }}>
                  <strong>Hash:</strong> {tx.hash}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 0', fontSize: '13px' }}>
                  <span style={{ color: '#8a8fa3' }}>De:</span>
                  <span style={{ color: '#eaecef', wordBreak: 'break-all' }}>{tx.sender}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 0', fontSize: '13px' }}>
                  <span style={{ color: '#8a8fa3' }}>Para:</span>
                  <span style={{ color: '#eaecef', wordBreak: 'break-all' }}>{tx.recipient}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 0', fontSize: '13px' }}>
                  <span style={{ color: '#8a8fa3' }}>Monto:</span>
                  <span style={{ color: '#f0b90b', fontWeight: 'bold', fontSize: '18px' }}>
                    {tx.amount_formatted || formatWei(tx.amount || 0)}
                  </span>
                </div>
                {tx.message && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 0', fontSize: '13px' }}>
                    <span style={{ color: '#8a8fa3' }}>Mensaje:</span>
                    <span style={{ color: '#eaecef' }}>{tx.message}</span>
                  </div>
                )}
                <div style={{ marginTop: '12px', padding: '8px', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '4px', fontSize: '12px', color: '#8a8fa3' }}>
                  ⏳ Estado: Pendiente de confirmación (necesita ser minada)
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-title">Minar Bloque</div>
        <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '16px' }}>
          Minar un bloque incluirá todas las transacciones pendientes y te dará una recompensa de minería.
        </div>
        <label className="input-label">Dirección para Recompensa de Minería</label>
        <input
          type="text"
          className="input-field"
          placeholder="0x..."
          value={miningAddress}
          onChange={(e) => setMiningAddress(e.target.value)}
        />
        <button 
          className="btn btn-primary" 
          onClick={mineBlock}
          disabled={miningResult?.loading || pendingTransactions.length === 0}
        >
          {miningResult?.loading ? 'Minando...' : `Minar Bloque (${pendingTransactions.length} TX pendientes)`}
        </button>
        {miningResult && (
          <div style={{ marginTop: '20px' }}>
            {miningResult.error ? (
              <div className="error">Error: {miningResult.error}</div>
            ) : miningResult.loading ? (
              <div className="success">⏳ Minando bloque...</div>
            ) : miningResult.success ? (
              <div className="success">
                ✓ Bloque minado exitosamente<br />
                Bloque #{miningResult.block?.index}<br />
                Hash: {miningResult.block?.hash?.substring(0, 20)}...
              </div>
            ) : miningResult.task_id ? (
              <div className="success">
                ✓ Minería iniciada (modo asíncrono)<br />
                Task ID: {miningResult.task_id}<br />
                Estado: {miningResult.status}
              </div>
            ) : (
              <div className="error">{miningResult.message || 'Error desconocido'}</div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

