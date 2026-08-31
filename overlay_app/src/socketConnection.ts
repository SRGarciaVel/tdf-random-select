import { io, Socket } from 'socket.io-client'

const BACKEND_URL = 'http://localhost:5001'

class SocketSingleton {
  private instance: Socket | null = null

  get(): Socket {
    if (this.instance === null) {
      this.instance = io(BACKEND_URL, {
        transports: ['websocket'],
        timeout: 5000,
        reconnectionDelay: 500,
        reconnectionDelayMax: 1500,
      })
    }
    return this.instance
  }
}

export default new SocketSingleton()
