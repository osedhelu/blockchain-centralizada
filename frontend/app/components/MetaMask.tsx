'use client'

import { useState, useEffect } from 'react'

interface MetaMaskProps {
  apiBase: string
}

declare global {
  interface Window {
    ethereum?: any
  }
}

export default function MetaMask({ apiBase }: MetaMaskProps) {
  const [authToken, setAuthToken] = useState<string | null>(null)
  const [connectedAddress, setConnectedAddress] = useState<string | null>(null)
  const [isConnecting, setIsConnecting] = useState(false)
  const [myBalance, setMyBalance] = useState<any>(null)
  const [myTransactions, setMyTransactions] = useState<any>(null)
  const [transferRecipient, setTransferRecipient] = useState('')
  const [transferAmount, setTransferAmount] = useState('')
  const [transferResult, setTransferResult] = useState<any>(null)
  const [ws, setWs] = useState<WebSocket | null>(null)

  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token')
    const savedAddress = localStorage.getItem('wallet_address')
    if (savedToken && savedAddress) {
      setAuthToken(savedToken)
      setConnectedAddress(savedAddress)
    }
    checkMetaMaskAvailable()
  }, [])

  useEffect(() => {
    if (!connectedAddress) {
      if (ws) {
        ws.close()
        setWs(null)
      }
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsUrl = `${protocol}://${window.location.host}/ws/wallet/${connectedAddress.toLowerCase()}`
    const socket = new WebSocket(wsUrl)

    socket.onopen = () => {
      // Podríamos enviar un ping inicial si fuera necesario
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'balance_update' && data.address?.toLowerCase() === connectedAddress.toLowerCase()) {
          setMyBalance({
            address: data.address,
            balance: data.balance,
            balance_formatted: data.balance_formatted,
          })
        }
      } catch (e) {
        console.error('Error procesando mensaje de WebSocket:', e)
      }
    }

    socket.onerror = (event) => {
      console.error('Error en WebSocket:', event)
    }

    socket.onclose = () => {
      setWs(null)
    }

    setWs(socket)

    return () => {
      socket.close()
    }
  }, [connectedAddress])

  const checkMetaMaskAvailable = () => {
    if (typeof window.ethereum === 'undefined') {
      // MetaMask no disponible
    }
  }

  const connectMetaMask = async () => {
    if (isConnecting) return
    if (typeof window.ethereum === 'undefined') {
      alert('MetaMask no está instalado')
      return
    }
    if (connectedAddress && authToken) {
      alert('Ya estás conectado con: ' + connectedAddress.substring(0, 6) + '...' + connectedAddress.substring(38))
      return
    }

    setIsConnecting(true)
    try {
      let accounts = []
      try {
        accounts = await window.ethereum.request({ method: 'eth_accounts' })
      } catch (e) {
        console.log('Error obteniendo cuentas:', e)
      }

      if (!accounts || accounts.length === 0) {
        try {
          accounts = await window.ethereum.request({ method: 'eth_requestAccounts' })
        } catch (error: any) {
          if (error.code === 4001) {
            throw new Error('Conexión rechazada por el usuario')
          } else if (error.message && error.message.includes('already pending')) {
            throw new Error('Ya hay una solicitud pendiente. Por favor espera y vuelve a intentar.')
          } else {
            throw error
          }
        }
      }

      const address = accounts[0]
      if (!address) throw new Error('No se pudo obtener la dirección')

      const messageResponse = await fetch(`${apiBase}/auth/message/${address}`)
      if (!messageResponse.ok) {
        const error = await messageResponse.json()
        throw new Error(error.detail || 'Error obteniendo mensaje')
      }
      const messageData = await messageResponse.json()

      let signature
      try {
        signature = await window.ethereum.request({
          method: 'personal_sign',
          params: [messageData.message, address]
        })
      } catch (error: any) {
        if (error.code === 4001) {
          throw new Error('Firma rechazada por el usuario')
        } else {
          throw error
        }
      }

      const authResponse = await fetch(`${apiBase}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          address: address,
          signature: signature,
          message: messageData.message
        })
      })

      if (!authResponse.ok) {
        const error = await authResponse.json()
        throw new Error(error.detail || 'Error en la autenticación')
      }

      const authData = await authResponse.json()
      setAuthToken(authData.access_token)
      setConnectedAddress(address.toLowerCase())
      localStorage.setItem('auth_token', authData.access_token)
      localStorage.setItem('wallet_address', address.toLowerCase())
      alert('MetaMask conectado exitosamente')
    } catch (error: any) {
      alert('Error: ' + (error.message || 'Error desconocido'))
    } finally {
      setIsConnecting(false)
    }
  }

  const disconnectMetaMask = () => {
    setAuthToken(null)
    setConnectedAddress(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('wallet_address')
    setMyBalance(null)
    setMyTransactions(null)
    if (ws) {
      ws.close()
      setWs(null)
    }
    alert('Desconectado exitosamente')
  }

  const getMyBalance = async () => {
    if (!authToken) {
      alert('Por favor conecta MetaMask primero')
      return
    }
    try {
      const response = await fetch(`${apiBase}/wallet/balance`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      })
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Error obteniendo balance' }))
        throw new Error(errorData.detail || 'Error obteniendo balance')
      }
      const data = await response.json()
      setMyBalance(data)
    } catch (error: any) {
      console.error('Error obteniendo balance:', error)
      setMyBalance({ error: error.message || 'Error desconocido' })
    }
  }

  const transferFunds = async () => {
    if (!authToken) {
      alert('Por favor conecta MetaMask primero')
      return
    }
    if (!transferRecipient.trim() || !transferAmount || parseFloat(transferAmount) <= 0) {
      alert('Por favor completa todos los campos correctamente')
      return
    }
    try {
      const response = await fetch(`${apiBase}/transactions/transfer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          recipient: transferRecipient,
          amount: parseFloat(transferAmount)
        })
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Error en la transferencia')
      }
      const data = await response.json()
      setTransferResult({ success: true, data })
      setTransferRecipient('')
      setTransferAmount('')
    } catch (error: any) {
      setTransferResult({ error: error.message })
    }
  }

  const getMyTransactions = async () => {
    if (!authToken) {
      alert('Por favor conecta MetaMask primero')
      return
    }
    try {
      const response = await fetch(`${apiBase}/wallet/transactions`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      })
      if (!response.ok) throw new Error('Error obteniendo transacciones')
      const data = await response.json()
      setMyTransactions(data)
    } catch (error: any) {
      setMyTransactions({ error: error.message })
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
        <div className="card-title">Conectar MetaMask</div>
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '8px' }}>Estado:</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: connectedAddress ? '#0ecb81' : '#8a8fa3' }}>
            {connectedAddress ? `Conectado: ${connectedAddress}` : 'No conectado'}
          </div>
        </div>
        <button
          className="btn btn-primary"
          onClick={connectMetaMask}
          disabled={isConnecting || typeof window.ethereum === 'undefined'}
        >
          {isConnecting ? 'Conectando...' : 'Conectar MetaMask'}
        </button>
        {connectedAddress && (
          <button className="btn btn-secondary" onClick={disconnectMetaMask} style={{ marginLeft: '10px' }}>
            Desconectar
          </button>
        )}
        {connectedAddress && (
          <div style={{ marginTop: '20px' }}>
            <div style={{ fontSize: '14px', color: '#8a8fa3' }}>Dirección Conectada</div>
            <div className="wallet-address">{connectedAddress}</div>
          </div>
        )}
      </div>

      {connectedAddress && authToken && (
        <div>
          <div className="card">
            <div className="card-title">Mi Balance</div>
            <button className="btn btn-secondary" onClick={getMyBalance}>Consultar Balance</button>
            {myBalance && (
              <div style={{ marginTop: '20px' }}>
                {myBalance.error ? (
                  <div className="error">Error: {myBalance.error}</div>
                ) : (
                  <div>
                    <div style={{ fontSize: '14px', color: '#8a8fa3' }}>Dirección</div>
                    <div className="wallet-address">{myBalance.address}</div>
                    <div style={{ fontSize: '14px', color: '#8a8fa3', marginTop: '16px' }}>Balance</div>
                    <div className="balance-display">
                      {myBalance.balance_formatted || formatWei(myBalance.balance || 0)}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-title">Transferir Fondos</div>
            <label className="input-label">Dirección Destinataria</label>
            <input
              type="text"
              className="input-field"
              placeholder="0x..."
              value={transferRecipient}
              onChange={(e) => setTransferRecipient(e.target.value)}
            />
            <label className="input-label">Monto</label>
            <input
              type="number"
              step="0.000000000000000001"
              className="input-field"
              placeholder="0.0"
              value={transferAmount}
              onChange={(e) => setTransferAmount(e.target.value)}
            />
            <button className="btn btn-primary" onClick={transferFunds}>Transferir</button>
            {transferResult && (
              <div style={{ marginTop: '20px' }}>
                {transferResult.error ? (
                  <div className="error">Error: {transferResult.error}</div>
                ) : (
                  <div className="success">
                    ✓ Transacción creada exitosamente<br />
                    De: {transferResult.data?.transaction?.sender}<br />
                    Para: {transferResult.data?.transaction?.recipient}<br />
                    Monto: {transferResult.data?.transaction?.amount}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-title">Mis Transacciones</div>
            <button className="btn btn-secondary" onClick={getMyTransactions}>Ver Mis Transacciones</button>
            {myTransactions && (
              <div style={{ marginTop: '20px' }}>
                {myTransactions.error ? (
                  <div className="error">Error: {myTransactions.error}</div>
                ) : myTransactions.transactions?.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px', color: '#8a8fa3' }}>No hay transacciones</div>
                ) : (
                  <div>
                    <div style={{ fontSize: '14px', color: '#8a8fa3', marginBottom: '16px' }}>
                      Total: {myTransactions.count} transacciones
                    </div>
                    {myTransactions.transactions?.map((tx: any, idx: number) => (
                      <div key={idx} style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '8px', padding: '16px', marginBottom: '12px' }}>
                        <div style={{ fontSize: '18px', fontWeight: '600', color: tx.type === 'sent' ? '#f6465d' : '#0ecb81' }}>
                          {tx.type === 'sent' ? '-' : '+'}{tx.amount_formatted || formatWei(tx.amount)}
                        </div>
                        <div style={{ fontSize: '12px', color: '#8a8fa3', marginTop: '4px' }}>
                          {tx.type === 'sent' ? `Para: ${tx.recipient}` : `De: ${tx.sender}`}
                          <br />
                          Bloque: {tx.block_index} | {new Date(tx.timestamp).toLocaleString()}
                          <br />
                          Hash: {tx.hash?.substring(0, 16)}...
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

