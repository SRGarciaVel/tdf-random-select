import { useEffect, useState } from 'react'
import socketConnection from './socketConnection'
import './App.css'

// Overlay minimo del walking skeleton (ver SPECS.md paragrafo 7).
// Se reemplaza por la grilla real de personajes en la Fase 3 del ROADMAP.
function App() {
  const [lastMessage, setLastMessage] = useState('esperando ping del panel de control')

  useEffect(() => {
    const socket = socketConnection.get()

    socket.on('ping_broadcast', (payload: { message: string }) => {
      setLastMessage(payload.message)
    })

    return () => {
      socket.off('ping_broadcast')
    }
  }, [])

  return (
    <div className="overlay-root">
      <p>{lastMessage}</p>
    </div>
  )
}

export default App
