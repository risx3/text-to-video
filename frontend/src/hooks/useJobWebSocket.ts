import { useCallback, useEffect, useRef } from 'react'
import type { WSMessage } from '../types/job'

interface Options {
  jobId: string | null
  onMessage: (msg: WSMessage) => void
  enabled?: boolean
}

const RECONNECT_DELAY_MS = 2000

export function useJobWebSocket({ jobId, onMessage, enabled = true }: Options) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const shouldReconnect = useRef(true)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    if (!jobId || !enabled) return

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${protocol}://${window.location.host}/ws/${jobId}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        if (msg.type !== 'ping') {
          onMessageRef.current(msg)
        }
      } catch {
        // ignore parse errors
      }
    }

    ws.onclose = (event) => {
      // Don't reconnect on clean close (1000) or if job is done
      if (!shouldReconnect.current || event.code === 1000) return
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [jobId, enabled])

  useEffect(() => {
    if (!jobId || !enabled) return

    shouldReconnect.current = true
    connect()

    return () => {
      shouldReconnect.current = false
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      wsRef.current?.close(1000, 'component unmounted')
    }
  }, [jobId, enabled, connect])

  const disconnect = useCallback(() => {
    shouldReconnect.current = false
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    wsRef.current?.close(1000, 'manual disconnect')
  }, [])

  return { disconnect }
}
