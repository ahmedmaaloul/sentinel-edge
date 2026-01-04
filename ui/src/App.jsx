import { useState, useEffect, useRef } from 'react';

function StatusBadge({ connected }) {
  return (
    <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
      <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
      {connected ? 'SYSTEM ONLINE' : 'DISCONNECTED'}
    </div>
  );
}

function AlertCard({ alert }) {
  const timestamp = new Date(alert.timestamp * 1000).toLocaleTimeString();

  return (
    <div className="bg-white border-l-4 border-red-500 shadow-md p-4 rounded mb-3 animate-in fade-in slide-in-from-right-4">
      <div className="flex justify-between items-start">
        <h3 className="font-bold text-red-600 flex items-center gap-2">
          ⚠️ ANOMALY DETECTED
        </h3>
        <span className="text-xs text-gray-500 font-mono">{timestamp}</span>
      </div>

      <div className="mt-2">
        {alert.anomalies.map((a, i) => (
          <div key={i} className="mb-2">
            <span className="inline-block bg-red-50 text-red-700 text-xs px-2 py-0.5 rounded border border-red-200 font-mono mr-2">
              {a.label}
            </span>
            <p className="text-gray-700 mt-1 text-sm">{a.description}</p>
          </div>
        ))}
      </div>

      <div className="mt-2 pt-2 border-t border-gray-100 flex justify-between text-xs text-gray-400">
        <span>Frame ID: {alert.frame_id}</span>
        <span>Latency: {alert.processing_latency_ms.toFixed(1)}ms</span>
      </div>
    </div>
  );
}

function App() {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [frame, setFrame] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws/stream');

    ws.onopen = () => {
      console.log('Connected to Sentinel-Edge Stream');
      setConnected(true);
    };

    ws.onclose = () => {
      console.log('Disconnected');
      setConnected(false);
      setFrame(null);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        if (msg.type === "frame") {
          setFrame(msg.data);
        } else if (msg.type === "alert") {
          console.log("Alert received:", msg.data);
          setAlerts(prev => [msg.data, ...prev].slice(0, 50));
        } else {
          // Legacy fallback (if raw json sent)
          setAlerts(prev => [msg, ...prev].slice(0, 50));
        }
      } catch (e) {
        console.error("Failed to parse message:", e);
      }
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 text-white p-2 rounded-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-gray-900">Sentinel<span className="text-blue-600">Edge</span></h1>
          </div>
          <StatusBadge connected={connected} />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Left Column: Live View */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-black rounded-xl overflow-hidden shadow-lg aspect-video relative group border border-gray-800">

              {frame ? (
                <img
                  src={`data:image/jpeg;base64,${frame}`}
                  alt="Live Feed"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center text-gray-500 bg-gray-900">
                  <div className="text-center">
                    <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
                    <p className="font-mono text-sm tracking-widest text-gray-400">NO LIVE VIDEO SIGNAL</p>
                    <p className="text-xs text-gray-600 mt-1">WAITING FOR STREAM...</p>
                  </div>
                </div>
              )}

              {/* Overlay */}
              <div className="absolute top-4 left-4">
                <span className="bg-red-600 text-white text-xs font-bold px-2 py-1 rounded flex items-center gap-1">
                  <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
                  LIVE
                </span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                <p className="text-xs text-gray-500 uppercase font-semibold">Model</p>
                <p className="font-mono text-sm font-bold mt-1">Qwen2.5-VL-7B</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                <p className="text-xs text-gray-500 uppercase font-semibold">Device</p>
                <p className="font-mono text-sm font-bold mt-1 text-purple-600">Apple Silicon (MPS)</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                <p className="text-xs text-gray-500 uppercase font-semibold">Events Today</p>
                <p className="font-mono text-sm font-bold mt-1">{alerts.length}</p>
              </div>
            </div>
          </div>

          {/* Right Column: Alert Feed */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Live Alerts</h2>
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">{alerts.length} events</span>
            </div>

            <div className="space-y-3 h-[600px] overflow-y-auto pr-2 custom-scrollbar">
              {alerts.length === 0 ? (
                <div className="text-center py-10 text-gray-400 border-2 border-dashed border-gray-200 rounded-lg">
                  <p>No anomalies detected yet.</p>
                  <p className="text-sm mt-1">System is monitoring...</p>
                </div>
              ) : (
                alerts.map((alert, idx) => (
                  <AlertCard key={idx} alert={alert} />
                ))
              )}
              <div ref={bottomRef} />
            </div>
          </div>

        </div>
      </main>
    </div>
  )
}

export default App
