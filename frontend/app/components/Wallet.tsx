'use client'

import { useState } from 'react'

interface WalletProps {
  apiBase: string
}

export default function Wallet({ apiBase }: WalletProps) {
  const [walletResult, setWalletResult] = useState<any>(null)
  const [importMnemonic, setImportMnemonic] = useState('')
  const [accountIndex, setAccountIndex] = useState(0)
  const [importResult, setImportResult] = useState<any>(null)
  const [balanceAddress, setBalanceAddress] = useState('')
  const [balanceResult, setBalanceResult] = useState<any>(null)
  const [txAddress, setTxAddress] = useState('')
  const [txResult, setTxResult] = useState<any>(null)

  const generateWallet = async () => {
    try {
      const response = await fetch(`${apiBase}/wallet/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_index: 0 })
      })
      const data = await response.json()
      setWalletResult(data)
    } catch (error: any) {
      setWalletResult({ error: error.message })
    }
  }

  const importWallet = async () => {
    try {
      const response = await fetch(`${apiBase}/wallet/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mnemonic: importMnemonic, account_index: accountIndex })
      })
      const data = await response.json()
      setImportResult(data)
    } catch (error: any) {
      setImportResult({ error: error.message })
    }
  }

  const checkBalance = async () => {
    if (!balanceAddress.trim()) {
      alert('Por favor ingresa una dirección')
      return
    }
    try {
      const response = await fetch(`${apiBase}/wallet/${balanceAddress}/balance`)
      const data = await response.json()
      setBalanceResult(data)
    } catch (error: any) {
      setBalanceResult({ error: error.message })
    }
  }

  const getTransactions = async () => {
    if (!txAddress.trim()) {
      alert('Por favor ingresa una dirección')
      return
    }
    try {
      const response = await fetch(`${apiBase}/wallet/${txAddress}/transactions`)
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
    if (fractionalPart === BigInt(0)) return wholePart.toString()
    const fractionalStr = fractionalPart.toString().padStart(18, '0').replace(/0+$/, '')
    return fractionalStr ? `${wholePart}.${fractionalStr}` : wholePart.toString()
  }

  return (
    <div>
      <div className="card">
        <div className="card-title">Generar Nueva Wallet</div>
        <button className="btn btn-primary" onClick={generateWallet}>Generar Wallet</button>
        {walletResult && (
          <div style={{ marginTop: '20px' }}>
            {walletResult.error ? (
              <div className="error">Error: {walletResult.error}</div>
            ) : (
              <div className="success">
                <div><strong>Dirección:</strong> {walletResult.wallet?.address}</div>
                <div style={{ marginTop: '10px' }}><strong>Mnemonic:</strong> {walletResult.wallet?.mnemonic}</div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-title">Importar Wallet desde Mnemonic</div>
        <label className="input-label">Mnemonic (12 palabras)</label>
        <input
          type="text"
          className="input-field"
          placeholder="palabra1 palabra2 ... palabra12"
          value={importMnemonic}
          onChange={(e) => setImportMnemonic(e.target.value)}
        />
        <label className="input-label">Índice de cuenta (default: 0)</label>
        <input
          type="number"
          className="input-field"
          value={accountIndex}
          onChange={(e) => setAccountIndex(parseInt(e.target.value) || 0)}
          min="0"
        />
        <button className="btn btn-primary" onClick={importWallet}>Importar Wallet</button>
        {importResult && (
          <div style={{ marginTop: '20px' }}>
            {importResult.error ? (
              <div className="error">Error: {importResult.error}</div>
            ) : (
              <div className="success">
                <div><strong>Dirección:</strong> {importResult.wallet?.address}</div>
                <div style={{ marginTop: '10px' }}><strong>Balance:</strong> {formatWei(importResult.balance || 0)}</div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-title">Consultar Balance</div>
        <input
          type="text"
          className="input-field"
          placeholder="0x..."
          value={balanceAddress}
          onChange={(e) => setBalanceAddress(e.target.value)}
        />
        <button className="btn btn-primary" onClick={checkBalance}>Consultar Balance</button>
        {balanceResult && (
          <div style={{ marginTop: '20px' }}>
            {balanceResult.error ? (
              <div className="error">Error: {balanceResult.error}</div>
            ) : (
              <div>
                <div style={{ fontSize: '14px', color: '#8a8fa3' }}>Dirección</div>
                <div className="wallet-address">{balanceResult.address}</div>
                <div style={{ fontSize: '14px', color: '#8a8fa3', marginTop: '16px' }}>Balance</div>
                <div className="balance-display">
                  {balanceResult.balance_formatted || formatWei(balanceResult.balance || 0)}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-title">Transacciones de la Wallet</div>
        <input
          type="text"
          className="input-field"
          placeholder="0x..."
          value={txAddress}
          onChange={(e) => setTxAddress(e.target.value)}
        />
        <button className="btn btn-primary" onClick={getTransactions}>Ver Transacciones</button>
        {txResult && (
          <div style={{ marginTop: '20px' }}>
            {txResult.error ? (
              <div className="error">Error: {txResult.error}</div>
            ) : txResult.transactions?.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#8a8fa3' }}>No hay transacciones</div>
            ) : (
              <div>
                <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '16px' }}>
                  Total: {txResult.count} transacciones
                </div>
                {txResult.transactions?.map((tx: any, idx: number) => (
                  <div key={idx} style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '8px', padding: '16px', marginBottom: '12px' }}>
                    <div style={{ fontSize: '18px', fontWeight: '600', color: tx.type === 'sent' ? '#f6465d' : '#0ecb81' }}>
                      {tx.type === 'sent' ? '-' : '+'}{tx.amount_formatted || formatWei(tx.amount)}
                    </div>
                    <div style={{ fontSize: '12px', color: '#8a8fa3', marginTop: '4px' }}>
                      {tx.type === 'sent' ? `Para: ${tx.recipient}` : `De: ${tx.sender}`}
                      <br />
                      Bloque: {tx.block_index} | {new Date(tx.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

