// Disable WebSocket in development for codespace compatibility
const isCodespace = process.env.CODESPACE_NAME || 
                   window.location.hostname.includes('app.github.dev') ||
                   window.location.hostname.includes('preview.emergentagent.com');

if (isCodespace) {
  // Override WebSocket to prevent connection attempts
  window.WebSocket = class NoOpWebSocket {
    constructor() {
      setTimeout(() => {
        if (this.onopen) this.onopen();
      }, 0);
    }
    
    send() {}
    close() {}
    addEventListener() {}
    removeEventListener() {}
  };
  
  // Disable service worker registration
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(function(registrations) {
      for(let registration of registrations) {
        registration.unregister();
      }
    });
  }
}

export default isCodespace;