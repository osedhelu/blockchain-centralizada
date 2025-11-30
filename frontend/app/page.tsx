'use client'

import { useState, useEffect } from 'react'
import Explorer from './components/Explorer'
import Wallet from './components/Wallet'
import Blocks from './components/Blocks'
import MetaMask from './components/MetaMask'

const API_BASE = typeof window !== 'undefined' ? window.location.origin : ''

export default function Home() {
  const [activeTab, setActiveTab] = useState('explorer')

  return (
    <div>
      <header>
        <div className="header-content">
          <div>
            <div className="logo">🔗 Blockchain Explorer</div>
            <div className="nav-tabs">
              <div 
                className={`tab ${activeTab === 'explorer' ? 'active' : ''}`}
                onClick={() => setActiveTab('explorer')}
              >
                Explorador
              </div>
              <div 
                className={`tab ${activeTab === 'wallet' ? 'active' : ''}`}
                onClick={() => setActiveTab('wallet')}
              >
                Wallet
              </div>
              <div 
                className={`tab ${activeTab === 'blocks' ? 'active' : ''}`}
                onClick={() => setActiveTab('blocks')}
              >
                Bloques
              </div>
              <div 
                className={`tab ${activeTab === 'metamask' ? 'active' : ''}`}
                onClick={() => setActiveTab('metamask')}
              >
                MetaMask
              </div>
            </div>
          </div>
          <div id="wallet-status" style={{ marginLeft: '20px', padding: '8px 16px', background: 'rgba(240, 185, 11, 0.2)', border: '1px solid #f0b90b', borderRadius: '6px', fontSize: '12px' }}>
            <span id="wallet-connected">No conectado</span>
          </div>
        </div>
      </header>

      <div className="container">
        {activeTab === 'explorer' && <Explorer apiBase={API_BASE} />}
        {activeTab === 'wallet' && <Wallet apiBase={API_BASE} />}
        {activeTab === 'blocks' && <Blocks apiBase={API_BASE} />}
        {activeTab === 'metamask' && <MetaMask apiBase={API_BASE} />}
      </div>
    </div>
  )
}

